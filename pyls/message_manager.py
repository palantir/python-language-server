# Copyright 2017 Palantir Technologies, Inc.
import json
import logging
import threading

from jsonrpc.jsonrpc2 import JSONRPC20Response
from jsonrpc.jsonrpc import JSONRPCRequest
from jsonrpc.exceptions import (
    JSONRPCInvalidRequestException,
)


log = logging.getLogger(__name__)


class MessageManager(object):
    """ Read/Write JSON RPC messages """

    def __init__(self, rfile, wfile):
        self.batch_messages = {}
        self.rfile = rfile
        self.wfile = wfile
        self.write_lock = threading.Lock()

    def close(self):
        with self.write_lock:
            self.wfile.close()
            self.rfile.close()

    def get_messages(self):
        """
        Generator that produces well structured JSON RPC message.

        Returns:
            message: received message

        Note:
            This method is not thread safe and should only invoked from a single thread
        """
        while not self.rfile.closed:
            request_str = self._read_message()

            if request_str is None:
                # log.error("failed to read message")
                continue
            if isinstance(request_str, bytes):
                request_str = request_str.decode("utf-8")

            try:
                try:
                    message_blob = json.loads(request_str)
                    message = JSONRPCRequest.from_data(message_blob)
                except JSONRPCInvalidRequestException:
                    # work around where JSONRPC20Reponse expects _id key
                    message_blob['_id'] = message_blob['id']
                    message = JSONRPC20Response(**message_blob)
            except (KeyError, ValueError):
                log.error("Could not parse message %s", request_str)
                continue

            yield message

    def write_message(self, message):
        """ Write message to out file descriptor

        Args:
            message (dict): body of the message to send
        """
        with self.write_lock:
            if self.wfile.closed:
                return
            log.debug("Sending %s", message)
            body = json.dumps(message, separators=(",", ":"))
            content_length = len(body)
            response = (
                "Content-Length: {}\r\n"
                "Content-Type: application/vscode-jsonrpc; charset=utf8\r\n\r\n"
                "{}".format(content_length, body)
            )
            self.wfile.write(response.encode('utf-8'))
            self.wfile.flush()

    def _read_message(self):
        """Reads the contents of a message

        :return body of message if parsable else None
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
