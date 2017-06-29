# Copyright 2017 Palantir Technologies, Inc.
import json
import logging
import uuid

import jsonrpc

log = logging.getLogger(__name__)


class JSONRPCServer(object):
    """ Read/Write JSON RPC messages """

    def __init__(self, rfile, wfile):
        self.rfile = rfile
        self.wfile = wfile

    def shutdown(self):
        # TODO: we should handle this much better
        self.rfile.close()
        self.wfile.close()

    def handle(self):
        # VSCode wants us to keep the connection open, so let's handle messages in a loop
        while True:
            try:
                data = self._read_message()
                log.debug("Got message: %s", data)
                response = jsonrpc.JSONRPCResponseManager.handle(data, self)
                if response is not None:
                    self._write_message(response.data)
            except Exception:
                log.exception("Language server shutting down for uncaught exception")
                break

    def call(self, method, params=None):
        """ Call a method on the client. TODO: return the result. """
        log.debug("Sending request %s: %s", method, params)
        req = jsonrpc.jsonrpc2.JSONRPC20Request(method=method, params=params)
        req._id = str(uuid.uuid4())
        self._write_message(req.data)

    def notify(self, method, params=None):
        """ Send a notification to the client, expects no response. """
        log.debug("Sending notification %s: %s", method, params)
        req = jsonrpc.jsonrpc2.JSONRPC20Request(
            method=method, params=params, is_notification=True
        )
        self._write_message(req.data)

    def _content_length(self, line):
        if line.startswith(b'Content-Length: '):
            _, value = line.split(b'Content-Length: ')
            value = value.strip()
            try:
                return int(value)
            except ValueError:
                raise ValueError("Invalid Content-Length header: {}".format(value))

    def _read_message(self):
        line = self.rfile.readline()

        if not line:
            raise EOFError()

        content_length = self._content_length(line)

        # Blindly consume all header lines
        while line and line.strip():
            line = self.rfile.readline()

        if not line:
            raise EOFError()

        # Grab the body
        return self.rfile.read(content_length)

    def _write_message(self, msg):
        body = json.dumps(msg, separators=(",", ":"))
        content_length = len(body)
        response = (
            "Content-Length: {}\r\n"
            "Content-Type: application/vscode-jsonrpc; charset=utf8\r\n\r\n"
            "{}".format(content_length, body)
        )
        self.wfile.write(response.encode('utf-8'))
        self.wfile.flush()
