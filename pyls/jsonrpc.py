# Copyright 2017 Palantir Technologies, Inc.
import json
import logging
import re
import socketserver
import threading
from collections import deque

log = logging.getLogger(__name__)
cv = threading.Condition()


class JSONRPCError(Exception):

    PARSE_ERROR = -32700
    INVALID_REQUEST = -32600
    METHOD_NOT_FOUND = -32601
    INVALID_PARAMS = -32602
    INTERNAL_ERROR = -32603
    SERVER_ERROR_START = -32099
    SERVER_ERROR_END = -32000

    def __init__(self, code, message, data=None):
        """ Init the JSONRPCError class

        :param self: the instance
        :param code: the error code
        :type code: integer
        """
        self.data = data or {}
        self.code = code
        self.message = message

    def to_rpc(self):
        return {
            'code': self.code,
            'message': self.message,
            'data': self.data
        }


class JSONRPCServer(socketserver.StreamRequestHandler, object):
    """ Read/Write JSON RPC messages """

    _msg_id = None

    def __init__(self, rfile, wfile):
        self.rfile = rfile
        self.wfile = wfile
        self.messages = deque()
        threading.Thread(
            target=self._write_loop,
            daemon=True
        ).start()

    def shutdown(self):
        # TODO: we should handle this much better
        self.rfile.close()
        self.wfile.close()

    def handle(self):
        # VSCode wants us to keep the connection open, so let's handle messages in a loop
        while True:
            # TODO: need to time out here eventually??
            try:
                self._handle_rpc_call()
            except Exception:
                break

    def handle_json(self, msg):
        # Convert JSONRPC methods to ones on this class
        # e.g. textDocument/didOpen => m_text_document__did_open
        method = "m_" + _method_to_string(msg['method'])

        # If the message is not implemented, then say so
        if not hasattr(self, method):
            log.warning("Missing method %s", method)
            raise JSONRPCError(JSONRPCError.METHOD_NOT_FOUND, msg['method'] + " not implemented")

        log.debug("Got message: %s", msg)

        # Else pass the message with params as kwargs
        # Params may be a dictionary or undefined, so force them to be a dictionary
        params = msg.get('params', {}) or {}
        return getattr(self, method)(**params)

    def call(self, method, params=None):
        """ Call a remote method, for now we ignore the response... """
        call = {
            'jsonrpc': '2.0',
            'method': method,
            'params': params
        }
        self._write_message(call)

    def _handle_rpc_call(self):
        msg = self._read_message()

        # Save the msg id to reply to
        if msg.get('id') is not None:
            self._msg_id = msg['id']

        # Make sure we're running 2.0 protocol
        assert msg['jsonrpc'] == '2.0'

        # Default response
        response = {'jsonrpc': '2.0', 'id': self._msg_id}

        try:
            reply = self.handle_json(msg)
            if reply is None:
                return
            response['result'] = reply
        except JSONRPCError as e:
            log.error("Failed to process message with id %s: %s", self._msg_id, msg)
            response['error'] = e.to_rpc()
        except Exception as e:
            log.exception("Caught internal error")
            err = JSONRPCError(JSONRPCError.INTERNAL_ERROR, str(e))
            response['error'] = err.to_rpc()

        log.debug("Responding to msg %s with %s", self._msg_id, response)
        self._write_message(response)

    def _content_length(self, line):
        if line.startswith("Content-Length: "):
            _, value = line.split("Content-Length: ")
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

        # Grab the body and handle it
        body = self.rfile.read(content_length)

        return json.loads(body)

    def _write_message(self, msg):
        with cv:
            self.messages.append(msg)
            cv.notify()

    def _real_write(self):
        with cv:
            if not self.messages:
                cv.wait()
            # note: only one consumer, so messages won't be empty after awaken
            msg = self.messages.popleft()
        body = json.dumps(msg, separators=(",", ":"))
        content_length = len(body)
        response = (
            "Content-Length: {}\r\n"
            "Content-Type: application/vscode-jsonrpc; charset=utf8\r\n\r\n"
            "{}".format(content_length, body)
        )
        self.wfile.write(response)
        self.wfile.flush()

    def _write_loop(self):
        while True:
            self._real_write()

_RE_FIRST_CAP = re.compile('(.)([A-Z][a-z]+)')
_RE_ALL_CAP = re.compile('([a-z0-9])([A-Z])')


def _method_to_string(method):
    return _camel_to_underscore(
        method.replace("/", "__").replace("$", "")
    )


def _camel_to_underscore(string):
    s1 = _RE_FIRST_CAP.sub(r'\1_\2', string)
    return _RE_ALL_CAP.sub(r'\1_\2', s1).lower()
