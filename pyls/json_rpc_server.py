# Copyright 2017 Palantir Technologies, Inc.
import json
import logging
import threading

from jsonrpc.jsonrpc2 import JSONRPC20Response, JSONRPC20BatchRequest, JSONRPC20BatchResponse
from jsonrpc.jsonrpc import JSONRPCRequest
from jsonrpc.exceptions import JSONRPCInvalidRequestException

log = logging.getLogger(__name__)


class JSONRPCServer(object):
    """ Read/Write JSON RPC messages """

    def __init__(self, rfile, wfile):
        self.pending_request = {}
        self.rfile = rfile
        self.wfile = wfile
        self.write_lock = threading.Lock()

    def close(self):
        with self.write_lock:
            self.wfile.close()
            self.rfile.close()

    def get_messages(self):
        """Generator that produces well structured JSON RPC message.

        Yields:
            message: received message

        Note:
            This method is not thread safe and should only invoked from a single thread
        """
        while not self.rfile.closed:
            request_str = self._read_message()

            if request_str is None:
                break
            if isinstance(request_str, bytes):
                request_str = request_str.decode("utf-8")

            try:
                try:
                    message_blob = json.loads(request_str)
                    request = JSONRPCRequest.from_data(message_blob)
                    if isinstance(request, JSONRPC20BatchRequest):
                        self._add_batch_request(request)
                        messages = request
                    else:
                        messages = [request]
                except JSONRPCInvalidRequestException:
                    # work around where JSONRPC20Reponse expects _id key
                    message_blob['_id'] = message_blob['id']
                    # we do not send out batch requests so no need to support batch responses
                    messages = [JSONRPC20Response(**message_blob)]
            except (KeyError, ValueError):
                log.exception("Could not parse message %s", request_str)
                continue

            for message in messages:
                yield message

    def write_message(self, message):
        """ Write message to out file descriptor.

        Args:
            message (JSONRPCRequest, JSONRPCResponse): body of the message to send
        """
        with self.write_lock:
            if self.wfile.closed:
                return
            elif isinstance(message, JSONRPC20Response) and message._id in self.pending_request:
                batch_response = self.pending_request[message._id](message)
                if batch_response is not None:
                    message = batch_response

            if isinstance(message, (JSONRPC20BatchResponse, JSONRPC20BatchRequest)):
                for msg in message:
                    log.debug('Sending %s', msg._data)
            else:
                log.debug('Sending %s', message._data)

            body = message.json
            content_length = len(body)
            response = (
                "Content-Length: {}\r\n"
                "Content-Type: application/vscode-jsonrpc; charset=utf8\r\n\r\n"
                "{}".format(content_length, body)
            )
            self.wfile.write(response.encode('utf-8'))
            self.wfile.flush()

    def _read_message(self):
        """Reads the contents of a message.

        Returns:
            body of message if parsable else None
        """
        line = self.rfile.readline()

        if not line:
            return None

        content_length = _content_length(line)

        # Blindly consume all header lines
        while line and line.strip():
            line = self.rfile.readline()

        if not line:
            return None

        # Grab the body
        return self.rfile.read(content_length)

    def _add_batch_request(self, requests):
        pending_requests = [request for request in requests if not request.is_notification]
        if not pending_requests:
            return

        batch_request = {'pending': len(pending_requests), 'resolved': []}
        for request in pending_requests:
            def cleanup_message(response):
                batch_request['pending'] -= 1
                batch_request['resolved'].append(response)
                del self.pending_request[request._id]
                return JSONRPC20BatchResponse(batch_request['resolved']) if batch_request['pending'] == 0 else None
            self.pending_request[request._id] = cleanup_message


def _content_length(line):
    """Extract the content length from an input line."""
    if line.startswith(b'Content-Length: '):
        _, value = line.split(b'Content-Length: ')
        value = value.strip()
        try:
            return int(value)
        except ValueError:
            raise ValueError("Invalid Content-Length header: {}".format(value))

    return None
