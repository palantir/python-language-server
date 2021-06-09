#!/usr/bin/env python
import logging
from typing import Optional
from tornado import web, ioloop, websocket, process
from tornado.platform.asyncio import AnyThreadEventLoopPolicy

from pyls_jsonrpc import dispatchers, endpoint
from pyls.python_ls import PythonLanguageServer
from io import BytesIO
import threading
import asyncio
try:
    import ujson as json
except Exception:  # pylint: disable=broad-except
    import json

log = logging.getLogger(__name__)


class LanguageServerWebSocketHandler(websocket.WebSocketHandler):
    """Setup tornado websocket handler to host language server."""

    def __init__(self, *args, **kwargs):
        # Create an instance of the language server used to dispatch JSON RPC methods
        self.rx = BytesIO()
        self.tx = BytesIO()
        langserver = PythonLanguageServer(self.rx, self.tx)

        def write_a_message(msg):
            self.write_message(json.dumps(msg))

        # Setup an endpoint that dispatches to the ls, and writes server->client messages
        # back to the client websocket
        self.endpoint = endpoint.Endpoint(langserver, write_a_message)

        # Give the language server a handle to the endpoint so it can send JSON RPC
        # notifications and requests.
        langserver._endpoint = self.endpoint

        super(LanguageServerWebSocketHandler, self).__init__(*args, **kwargs)

        langserver.start()

    def on_message(self, message):
        """Forward client->server messages to the endpoint."""
        self.endpoint.consume(json.loads(message))

    @property
    def ping_interval(self) -> Optional[float]:
        return 5

    def check_origin(self, origin):
        return True


class HealthCheckHandler(web.RequestHandler):

    def get(self):
        self.write("OK")

if __name__ == '__main__':
    asyncio.set_event_loop_policy(AnyThreadEventLoopPolicy())
    app = web.Application([
        (r"/python", LanguageServerWebSocketHandler),
        (r"/health", HealthCheckHandler),
        (r"/", HealthCheckHandler),
    ])
    app.listen(3002)
    ioloop.IOLoop.current().start()