# Copyright 2017 Palantir Technologies, Inc.
import json
import logging
import uuid

from jsonrpc import jsonrpc2, JSONRPCResponseManager

log = logging.getLogger(__name__)


class JSONRPCServer(object):
    """ Read/Write JSON RPC messages """

    def __init__(self, rfile, wfile):
        self.rfile = rfile
        self.wfile = wfile

        self._callbacks = {}
        self._shutdown = False

    def exit(self):
        # Exit causes a complete exit of the server
        self.rfile.close()
        self.wfile.close()

    def shutdown(self):
        # Shutdown signals the server to stop, but not exit
        self._shutdown = True
        log.debug("Server shut down, awaiting exit notification")

    def handle(self):
        while True:
            try:
                data = self._read_message()
                log.debug("Got message: %s", data)

                if self._shutdown:
                    # Handle only the exit notification when we're shut down
                    JSONRPCResponseManager.handle(data, {'exit': self.exit})
                    break

                if isinstance(data, bytes):
                    data = data.decode("utf-8")

                msg = json.loads(data)
                if 'method' in msg:
                    # It's a notification or request
                    # Dispatch to the thread pool for handling
                    response = JSONRPCResponseManager.handle(data, self)
                    if response is not None:
                        self._write_message(response.data)
                else:
                    # Otherwise, it's a response message
                    on_result, on_error = self._callbacks.pop(msg['id'])
                    if 'result' in msg and on_result:
                        on_result(msg['result'])
                    elif 'error' in msg and on_error:
                        on_error(msg['error'])
            except:  # pylint: disable=bare-except
                log.exception("Language server exiting due to uncaught exception")
                break

    def call(self, method, params=None, on_result=None, on_error=None):
        """Call a method on the client."""
        msg_id = str(uuid.uuid4())
        log.debug("Sending request %s: %s: %s", msg_id, method, params)
        req = jsonrpc2.JSONRPC20Request(method=method, params=params)
        req._id = msg_id

        def _default_on_error(error):
            log.error("Call to %s failed with %s", method, error)

        if not on_error:
            on_error = _default_on_error

        self._callbacks[msg_id] = (on_result, on_error)
        self._write_message(req.data)

    def notify(self, method, params=None):
        """ Send a notification to the client, expects no response. """
        log.debug("Sending notification %s: %s", method, params)
        req = jsonrpc2.JSONRPC20Request(
            method=method, params=params, is_notification=True
        )
        self._write_message(req.data)

    def _read_message(self):
        line = self.rfile.readline()

        if not line:
            raise EOFError()

        content_length = _content_length(line)

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


def _content_length(line):
    """Extract the content length from an input line."""
    if line.startswith(b'Content-Length: '):
        _, value = line.split(b'Content-Length: ')
        value = value.strip()
        try:
            return int(value)
        except ValueError:
            raise ValueError("Invalid Content-Length header: {}".format(value))
