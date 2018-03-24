# Copyright 2017 Palantir Technologies, Inc.
import json
import logging
import threading

log = logging.getLogger(__name__)


class JsonRpcServer(object):

    def __init__(self, rfile, wfile):
        self.rfile = rfile
        self.wfile = wfile

        self.write_lock = threading.Lock()

    def shutdown(self):
        with self.write_lock:
            self.wfile.close()
            self.rfile.close()

    def listen(self, message_consumer):
        """Blocking call to listen for messages on the rfile.

        Args:
            message_consumer (fn): function that is passed each message as it is read off the socket.
        """
        while not self.rfile.closed:
            request_str = self._read_message()

            if request_str is None:
                break
            if isinstance(request_str, bytes):
                request_str = request_str.decode("utf-8")

            try:
                message_consumer(json.loads(request_str))
            except ValueError:
                log.exception("Failed to parse JSON message %s", request_str)
                continue

    def _read_message(self):
        """Reads the contents of a message.

        Returns:
            body of message if parsable else None
        """
        line = self.rfile.readline()

        if not line:
            return None

        content_length = self._content_length(line)

        # Blindly consume all header lines
        while line and line.strip():
            line = self.rfile.readline()

        if not line:
            return None

        # Grab the body
        return self.rfile.read(content_length)

    def write(self, message):
        """ Write message to wfile.

        Args:
            message (dict): a JSON RPC message to write to the wfile.
        """
        with self.write_lock:
            if self.wfile.closed:
                return

            log.debug('Sending %s', message)
            try:
                body = json.dumps(message)
                content_length = len(body)
                response = (
                    "Content-Length: {}\r\n"
                    "Content-Type: application/vscode-jsonrpc; charset=utf8\r\n\r\n"
                    "{}".format(content_length, body)
                )
                self.wfile.write(response.encode('utf-8'))
                self.wfile.flush()
            except Exception:  # pylint: disable=broad-except
                log.exception("Failed to write message to output file %s", message)

    @staticmethod
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
