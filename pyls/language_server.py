# Copyright 2017 Palantir Technologies, Inc.
import logging
import re
import socketserver
from . import uris
from .server import JSONRPCServer

log = logging.getLogger(__name__)


class _StreamHandlerWrapper(socketserver.StreamRequestHandler, object):
    """A wrapper class that is used to construct a custom handler class."""

    delegate = None

    def setup(self):
        super(_StreamHandlerWrapper, self).setup()
        self.delegate = self.DELEGATE_CLASS(self.rfile, self.wfile)

    def handle(self):
        self.delegate.handle()


def start_tcp_lang_server(bind_addr, port, handler_class):
    if not issubclass(handler_class, JSONRPCServer):
        raise ValueError("Handler class must be a subclass of JSONRPCServer")

    # Construct a custom wrapper class around the user's handler_class
    wrapper_class = type(
        handler_class.__name__ + "Handler",
        (_StreamHandlerWrapper,),
        {'DELEGATE_CLASS': handler_class}
    )

    server = socketserver.ThreadingTCPServer((bind_addr, port), wrapper_class)
    try:
        log.info("Serving %s on (%s, %s)", handler_class.__name__, bind_addr, port)
        server.serve_forever()
    except KeyboardInterrupt:
        server.exit()
    finally:
        log.info("Shutting down")
        server.server_close()


def start_io_lang_server(rfile, wfile, handler_class):
    if not issubclass(handler_class, JSONRPCServer):
        raise ValueError("Handler class must be a subclass of LanguagJSONRPCServereServer")
    log.info("Starting %s IO language server", handler_class.__name__)
    server = handler_class(rfile, wfile)
    server.handle()


class MethodJSONRPCServer(JSONRPCServer):
    """JSONRPCServer that calls methods on itself with params."""

    def __getitem__(self, item):
        """The jsonrpc dispatcher uses getitem to retrieve the RPC method implementation."""
        method_name = "m_" + _method_to_string(item)
        if not hasattr(self, method_name):
            raise KeyError("Cannot find method %s" % method_name)
        func = getattr(self, method_name)

        def wrapped(*args, **kwargs):
            try:
                return func(*args, **kwargs)
            except:  # pylint: disable=bare-except
                log.exception("CAUGHT")
                raise
        return wrapped


class LanguageServer(MethodJSONRPCServer):
    """ Implementation of the Microsoft VSCode Language Server Protocol
    https://github.com/Microsoft/language-server-protocol/blob/master/versions/protocol-1-x.md
    """

    process_id = None
    root_uri = None
    init_opts = None

    def capabilities(self):
        return {}

    def initialize(self, root_uri, init_opts, process_id):
        pass

    def m_initialize(self, **kwargs):
        log.debug("Language server intialized with %s", kwargs)
        if 'rootUri' in kwargs:
            self.root_uri = kwargs['rootUri']
        elif 'rootPath' in kwargs:
            root_path = kwargs['rootPath']
            self.root_uri = uris.from_fs_path(root_path)
        else:
            self.root_uri = ''
        self.init_opts = kwargs.get('initializationOptions')
        self.process_id = kwargs.get('processId')

        self.initialize(self.root_uri, self.init_opts, self.process_id)

        # Get our capabilities
        return {'capabilities': self.capabilities()}

    def m___cancel_request(self, **kwargs):
        # TODO: We could I suppose launch tasks in their own threads and kill
        # them on cancel, but is it really worth the effort given most methods
        # are reasonably quick?
        # This tends to happen when cancelling a hover request
        pass

    def m_shutdown(self, **_kwargs):
        self.shutdown()

    def m_exit(self, **_kwargs):
        self.exit()


_RE_FIRST_CAP = re.compile('(.)([A-Z][a-z]+)')
_RE_ALL_CAP = re.compile('([a-z0-9])([A-Z])')


def _method_to_string(method):
    return _camel_to_underscore(
        method.replace("/", "__").replace("$", "")
    )


def _camel_to_underscore(string):
    s1 = _RE_FIRST_CAP.sub(r'\1_\2', string)
    return _RE_ALL_CAP.sub(r'\1_\2', s1).lower()
