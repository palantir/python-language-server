# Copyright 2017 Palantir Technologies, Inc.
import json
import logging
import re
import jsonrpc
import sys
import socket

log = logging.getLogger(__name__)


if sys.hexversion >= 0x3000000:
    PYTHON3 = True
    socket_type = socket.SocketIO
else:
    socket_type = socket._fileobject
    PYTHON3 = False


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
        done = False
        # VSCode wants us to keep the connection open, so let's handle messages in a loop
        while not done:
            try:
                data = self._read_message()
                log.debug("Got message: %s", data)
                response = jsonrpc.JSONRPCResponseManager.handle(data, self)
                if response is not None:
                    self._write_message(response.data)
            except Exception:
                log.exception("Language server shutting down for uncaught exception")
                break

            if isinstance(self.wfile, socket_type):
                done = True

    def call(self, method, params=None):
        """ Call a method on the client. TODO: return the result. """
        req = jsonrpc.jsonrpc2.JSONRPC20Request(method=method, params=params)
        self._write_message(req.data)

    def notify(self, method, params=None):
        """ Send a notification to the client, expects no response. """
        req = jsonrpc.jsonrpc2.JSONRPC20Request(
            method=method, params=params, is_notification=True
        )
        self._write_message(req.data)

    def __getitem__(self, item):
        # The jsonrpc dispatcher uses getitem to retrieve the RPC method implementation.
        # We convert that to our own convention.
        if not hasattr(self, _method_to_string(item)):
            raise KeyError("Cannot find method %s" % item)
        return getattr(self, _method_to_string(item))

    def _content_length(self, line):
        if line.startswith("Content-Length: "):
            _, value = line.split("Content-Length: ")
            value = value.strip()
            try:
                return int(value)
            except ValueError:
                raise ValueError("Invalid Content-Length header: {}".format(value))

    def readline(self):
        line = self.rfile.readline()

        if isinstance(line, bytes):
            line = line.decode('utf-8')

        return line

    def _read_message(self):
        line = self.readline()

        if not line:
            raise EOFError()

        content_length = self._content_length(line)

        # Blindly consume all header lines
        while line and line.strip():
            cl = self._content_length(line)
            if cl:
                content_length = cl
            line = self.readline()

        if not line:
            raise EOFError()

        # Grab the body
        res = self.rfile.read(content_length)

        if isinstance(res, bytes):
            res = res.decode('utf-8')

        return res

    def _write_message(self, msg):
        body = json.dumps(msg, separators=(",", ":"))
        content_length = len(body)

        if isinstance(self.wfile, socket_type):
            header = "HTTP/1.1 200 OK\r\n"
        else:
            header = ""

        response = (
            "{}"
            "Content-Length: {}\r\n"
            "Content-Type: application/vscode-jsonrpc; charset=utf8\r\n\r\n"
            "{}".format(header, content_length, body)
        )

        if PYTHON3 and isinstance(self.wfile, socket_type):
            response = response.encode("utf-8")

        self.wfile.write(response)
        self.wfile.flush()


_RE_FIRST_CAP = re.compile('(.)([A-Z][a-z]+)')
_RE_ALL_CAP = re.compile('([a-z0-9])([A-Z])')


def _method_to_string(method):
    return "m_" + _camel_to_underscore(
        method.replace("/", "__").replace("$", "")
    )


def _camel_to_underscore(string):
    s1 = _RE_FIRST_CAP.sub(r'\1_\2', string)
    return _RE_ALL_CAP.sub(r'\1_\2', s1).lower()
