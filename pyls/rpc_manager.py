# Copyright 2017 Palantir Technologies, Inc.
import logging
from uuid import uuid1

from concurrent.futures import ThreadPoolExecutor, Future
from jsonrpc.base import JSONRPCBaseResponse
from jsonrpc.jsonrpc1 import JSONRPC10Response
from jsonrpc.jsonrpc2 import JSONRPC20Response, JSONRPC20Request
from jsonrpc.exceptions import JSONRPCMethodNotFound, JSONRPCInternalError

from .message_manager import MessageManager

log = logging.getLogger(__name__)

RESPONSE_CLASS_MAP = {
    "1.0": JSONRPC10Response,
    "2.0": JSONRPC20Response
}


class JSONRPCManager(object):
    """ Implementation of the Microsoft VSCode Language Server Protocol
    https://github.com/Microsoft/language-server-protocol/blob/master/versions/protocol-1-x.md
    """

    def __init__(self, rx, tx, message_handler):
        self._message_manager = MessageManager(rx, tx)
        self._message_handler = message_handler
        self._shutdown = False
        self._sent_requests = {}
        self._received_requests = {}
        self._executor_service = ThreadPoolExecutor()

    def start(self):
        """Start reading JSONRPC messages off of rx"""
        self.consume_requests()

    def shutdown(self):
        """Set flag to ignore all non exit messages"""
        self._shutdown = True

    def exit(self):
        """Stop listening for new message"""
        self._executor_service.shutdown()
        self._message_manager.close()

    def call(self, method, params=None):
        """Send a JSONRPC message with an expected response.

        Args:
            method (str): The method name of the message to send
            params (dict): The payload of the message

        Returns:
            Future that will resolve once a response has been recieved

        """
        log.debug('Calling %s %s', method, params)
        request = JSONRPC20Request(_id=uuid1().int, method=method, params=params)
        request_future = Future()
        self._sent_requests[request._id] = request_future
        self._message_manager.write_message(request.data)
        return request_future

    def notify(self, method, params=None):
        """Send a JSONRPC notification.

         Args:
             method (str): The method name of the notification to send
             params (dict): The payload of the notification
         """
        log.debug('Notify %s %s', method, params)
        notification = JSONRPC20Request(method=method, params=params)
        self._message_manager.write_message(notification.data)

    def cancel(self, request_id):
        """Cancel pending request handler.

        Args:
            request_id (string | number): The id of the original request

        Note:
            Request will only be cancelled if it has not begun execution.
        """
        log.debug('Cancel request %d', request_id)
        try:
            self._received_requests[request_id].cancel()
        except KeyError:
            log.error('Received cancel for finished/nonexistent request %d', request_id)

    def consume_requests(self):
        """ Infinite loop watching for messages from the client."""
        for message in self._message_manager.get_messages():
            if isinstance(message, JSONRPCBaseResponse):
                self._handle_response(message)
            else:
                self._handle_request(message)

    def _handle_request(self, request):
        """Execute corresponding handler for the recieved request

        Args:
            request (JSONRPCBaseRequest): request to act upon

        Note:
            requests are handled asynchronously if the handler returns a callable, otherwise they are handle
            synchronously by the main thread
        """
        if self._shutdown and request.method != 'exit':
            return

        params = request.params if request.params is not None else {}
        try:
            maybe_handler = self._message_handler(request.method, params)
        except KeyError:
            log.debug("No handler found for %s", request.method)
            self._message_manager.write_message(
                JSONRPC20Response(_id=request._id, error=JSONRPCMethodNotFound()._data).data)
            return

        if request._id in self._received_requests:
            log.error('Received request %s with duplicate id', request.data)
        elif callable(maybe_handler):
            self._handle_async_request(request, maybe_handler)
        elif not request.is_notification:
            log.debug("sync request %s", request._id)
            response = _make_response(request, result=maybe_handler)
            self._message_manager.write_message(response.data)

    def _handle_async_request(self, request, handler):
        log.debug("async request %s", request._id)
        future = self._executor_service.submit(handler)

        if request.is_notification:
            return

        self._received_requests[request._id] = future

        def did_finish_callback(completed_future):
            if completed_future.cancelled():
                log.debug('Cleared cancelled request %d', request._id)
                del self._received_requests[request._id]
                return

            error, trace = completed_future.exception_info()
            del self._received_requests[request._id]
            if error is not None:
                log.error("Failed to handle request %s with error %s %s", request._id, error, trace)
                # TODO(forozco): add more descriptive error
                response = _make_response(request, errror=JSONRPCInternalError()._data)
            else:
                response = _make_response(request, result=completed_future.result())
            self._message_manager.write_message(response.data)
        future.add_done_callback(did_finish_callback)

    def _handle_response(self, response):
        try:
            request = self._sent_requests[response._id]
            log.debug("Received response %s", response.data)

            def cleanup(_):
                del self._sent_requests[response._id]
            request.add_done_callback(cleanup)
            request.set_result(response.data)

        except KeyError:
            log.error('Received unexpected response %s', response.data)


def _make_response(request, **kwargs):
    response = RESPONSE_CLASS_MAP[request.JSONRPC_VERSION](_id=request._id, **kwargs)
    response.request = request
    return response
