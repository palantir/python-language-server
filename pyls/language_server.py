# Copyright 2017 Palantir Technologies, Inc.
import logging
import socketserver
from uuid import uuid1

from concurrent.futures import ThreadPoolExecutor, Future
from jsonrpc.jsonrpc2 import JSONRPC20Response, JSONRPC20Request
from jsonrpc.exceptions import JSONRPCMethodNotFound

from . import uris
from .rpc_manager import JSONRPCManager

log = logging.getLogger(__name__)


class _StreamHandlerWrapper(socketserver.StreamRequestHandler, object):
    """A wrapper class that is used to construct a custom handler class."""

    delegate = None

    def setup(self):
        super(_StreamHandlerWrapper, self).setup()
        # pylint: disable=no-member
        self.delegate = self.DELEGATE_CLASS(self.rfile, self.wfile)

    def handle(self):
        self.delegate.handle()


def start_tcp_lang_server(bind_addr, port, handler_class):
    if not issubclass(handler_class, LanguageServer):
        raise ValueError('Handler class must be a subclass of JSONRPCServer')

    # Construct a custom wrapper class around the user's handler_class
    wrapper_class = type(
        handler_class.__name__ + 'Handler',
        (_StreamHandlerWrapper,),
        {'DELEGATE_CLASS': handler_class}
    )

    server = socketserver.TCPServer((bind_addr, port), wrapper_class)
    try:
        log.info('Serving %s on (%s, %s)', handler_class.__name__, bind_addr, port)
        server.serve_forever()
    finally:
        log.info('Shutting down')
        server.server_close()


def start_io_lang_server(rfile, wfile, handler_class):
    if not issubclass(handler_class, LanguageServer):
        raise ValueError('Handler class must be a subclass of JSONRPCServer')
    log.info('Starting %s IO language server', handler_class.__name__)
    server = handler_class(rfile, wfile)
    server.start()


class JSONRPCManager(object):
    """ Implementation of the Microsoft VSCode Language Server Protocol
    https://github.com/Microsoft/language-server-protocol/blob/master/versions/protocol-1-x.md
    """

    def __init__(self, rx, tx):
        self._message_manager = JSONRPCManager(rx, tx)
        self._sent_requests = {}
        self._received_requests = {}
        self.executor_service = ThreadPoolExecutor()
        self.process_id = None
        self.root_uri = None
        self.init_opts = None

    def start(self):
        self.consume_requests()

    def call(self, method, params=None):
        log.debug('Calling %s %s', method, params)
        request = JSONRPC20Request(_id=str(uuid1()), method=method, params=params)
        request_future = Future()
        self._sent_requests[request._id] = request_future
        self._message_manager.write_message(request.data)
        return request_future

    def notify(self, method, params=None):
        log.debug('Notify %s %s', method, params)
        notification = JSONRPC20Request(method=method, params=params)
        self._message_manager.write_message(notification.data)


    def consume_requests(self):
        """ Infinite loop watching for messages from the client"""
        for message in self._message_manager.get_messages():
            log.debug('Received message %s', message if isinstance(message, dict) else message.data)
            if isinstance(message, JSONRPC20Response):
                self._handle_response(message)
            elif isinstance(message, JSONRPC20Request):
                if message.is_notification:
                    self.handle_notification(message.method, message.params)
                else:
                    self._handle_request(message)
            else:
                # TODO(forozco): do something with rpc errors
                pass

    def _handle_request(self, request):
        handler = self.get_request_handler(request.method)
        if handler is None:
            self._message_manager.write_message(JSONRPCMethodNotFound().data)
            return
        elif request._id in self._received_requests:
            log.error('Received request %s with duplicate id', request.data)
            return

        future = self.executor_service.submit(handler, **request.params)
        self._received_requests[request._id] = future
        def did_finish(completed_future):
            if completed_future.cancelled():
                log.debug('Cleared cancelled request %d', request._id)
                del self._received_requests[request._id]
                return

            error, trace = completed_future.exception_info()
            response = None
            if error is not None:
                if isinstance(error, dict):
                    response = JSONRPC20Response(_id=request._id, error=error)
                    log.error("responded to %s with %s", request.data, response.data)
                else:
                    log.error('request %d failed %s %s', request._id, error, trace)
                    return
            else:
                log.debug('Sending response %s', completed_future.result())
                response = JSONRPC20Response(_id=request._id, result=completed_future.result())
            self._message_manager.write_message(response._data)
            del self._received_requests[request._id]

        future.add_done_callback(did_finish)

    def _handle_response(self, response):
        try:
            request = self._sent_requests[response._id]
            def cleanup():
                del self._sent_requests[response._id]
            request.add_done_callback(cleanup)
            request.set_result(response.result if response.result is not None else response.error)

        except KeyError:
            log.error('Received unexpected response %s', response.data)

    def handle_notification(self, method, params):
        pass

    def get_request_handler(self, method):
        pass

    def initialize(self, root_uri, init_opts, process_id):
        pass

    def capabilities(self):  # pylint: disable=no-self-use
        return {}

    def m_initialize(self, **kwargs):
        log.debug('Language server initialized with %s', kwargs)
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
        request_id = kwargs['id']
        log.debug('Cancel request %d', request_id)
        try:
            # Request will only be cancelled if it has not begun execution
            self._received_requests[request_id].cancel()
        except KeyError:
            log.error('Received cancel for finished/nonexistent request %d', request_id)

    def m_shutdown(self, **_kwargs):
        self.m_exit()

    def m_exit(self, **_kwargs):
        self.executor_service.shutdown()
        self._message_manager.exit()
