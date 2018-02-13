# Copyright 2017 Palantir Technologies, Inc.
import json
import logging

from jsonrpc.jsonrpc2 import JSONRPC20Response
from jsonrpc.jsonrpc import JSONRPCRequest
from jsonrpc.exceptions import (
    JSONRPCError,
    JSONRPCInvalidRequest,
    JSONRPCInvalidRequestException,
    JSONRPCParseError,
)


log = logging.getLogger(__name__)


class JSONRPCManager(object):
    """ Read/Write JSON RPC messages """

    def __init__(self, rfile, wfile):
        self.batch_messages = {}
        self.rfile = rfile
        self.wfile = wfile

    def exit(self):
        # Exit causes a complete exit of the server
        self.rfile.close()
        self.wfile.close()

    def get_messages(self):
        """Generator that produces well structured JSON RPC message
        :return JSONRPCRequest request:
        """
        while True:
            request_str = self._read_message()

            if request_str is None:
                self.write_message(JSONRPCParseError()._data)
                continue
            if isinstance(request_str, bytes):
                request_str = request_str.decode("utf-8")

            try:
                message = JSONRPCRequest.from_json(request_str)
            except (TypeError, ValueError, JSONRPCInvalidRequestException):
                try:
                    message = JSONRPC20Response.from_json(request_str)
                except (KeyError, ValueError):
                    try:
                        message = JSONRPCError.from_json(request_str)
                    except (ValueError, TypeError):
                        self.write_message(JSONRPCInvalidRequest()._data)
                        continue

            yield message

    def write_message(self, message):
        """ Write message to out file descriptor

        :param any message: response blob
        """
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
