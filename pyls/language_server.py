# Copyright 2017 Palantir Technologies, Inc.
import logging
import socketserver
from .jsonrpc import JSONRPCServer
from .workspace import Workspace

log = logging.getLogger(__name__)


def start_tcp_lang_server(bind_addr, port, handler_class):
    if not issubclass(handler_class, LanguageServer):
        raise ValueError("Handler class must be a subclass of LanguageServer")
    server = socketserver.ThreadingTCPServer((bind_addr, port), handler_class)
    try:
        log.info("Serving %s on (%s, %s)", handler_class.__name__, bind_addr, port)
        server.serve_forever()
    except KeyboardInterrupt:
        server.shutdown()
    finally:
        log.info("Shutting down")
        server.server_close()


def start_io_lang_server(rfile, wfile, handler_class):
    if not issubclass(handler_class, LanguageServer):
        raise ValueError("Handler class must be a subclass of LanguageServer")
    log.info("Starting %s IO language server", handler_class.__name__)
    server = handler_class(rfile, wfile)
    server.handle()


class LanguageServer(JSONRPCServer):
    """ Implementation of the Microsoft VSCode Language Server Protocol
    https://github.com/Microsoft/language-server-protocol/blob/master/versions/protocol-1-x.md
    """

    process_id = None
    workspace = None
    init_opts = None

    M_PUBLISH_DIAGNOSTICS = 'textDocument/publishDiagnostics'

    def capabilities(self):
        return {}

    def publish_diagnostics(self, uri, diagnostics):
        log.debug("Publishing diagnostics: %s", diagnostics)
        params = {'uri': uri, 'diagnostics': diagnostics}
        self.call(self.M_PUBLISH_DIAGNOSTICS, params)

    def m_initialize(self, **kwargs):
        log.debug("Language server intialized with %s", kwargs)
        self.process_id = kwargs.get('processId')
        self.workspace = Workspace(kwargs.get('rootPath'))
        self.init_opts = kwargs.get('initializationOptions')

        # Get our capabilities
        return {'capabilities': self.capabilities()}

    def m___cancel_request(self, **kwargs):
        # TODO: We could I suppose launch tasks in their own threads and kill
        # them on cancel, but is it really worth the effort given most methods
        # are reasonably quick?
        # This tends to happen when cancelling a hover request
        pass

    def m_shutdown(self, **kwargs):
        self.shutdown()

    def m_exit(self, **kwargs):
        self.shutdown()
