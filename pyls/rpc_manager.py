# Copyright 2017 Palantir Technologies, Inc.
import logging
from uuid import uuid4

from concurrent.futures import ThreadPoolExecutor, Future
from jsonrpc.base import JSONRPCBaseResponse
from jsonrpc.jsonrpc1 import JSONRPC10Response
from jsonrpc.jsonrpc2 import JSONRPC20Response, JSONRPC20Request
from jsonrpc.exceptions import JSONRPCMethodNotFound, JSONRPCDispatchException, JSONRPCServerError

log = logging.getLogger(__name__)

RESPONSE_CLASS_MAP = {
    "1.0": JSONRPC10Response,
    "2.0": JSONRPC20Response
}


class MissingMethodException(Exception):
    pass


class JSONRPCManager(object):

    def __init__(self, message_manager, message_handler):
        self._message_manager = message_manager
        self._message_handler = message_handler
        self._shutdown = False
        self._sent_requests = {}
        self._received_requests = {}
        self._executor_service = ThreadPoolExecutor(max_workers=5)  # arbitrary pool size

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
        """Send a JSONRPC request.

        Args:
            method (str): The method name of the message to send
            params (dict): The payload of the message

        Returns:
            Future that will resolve once a response has been received
        """
        log.debug('Calling %s %s', method, params)
        request = JSONRPC20Request(_id=str(uuid4()), method=method, params=params)
        request_future = Future()
        self._sent_requests[request._id] = request_future
        self._message_manager.write_message(request)
        return request_future

    def notify(self, method, params=None):
        """Send a JSONRPC notification.

         Args:
             method (str): The method name of the notification to send
             params (dict): The payload of the notification
         """
        log.debug('Notify %s %s', method, params)
        notification = JSONRPC20Request(method=method, params=params, is_notification=True)
        self._message_manager.write_message(notification)

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
            log.debug('Received cancel for finished/nonexistent request %d', request_id)

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
            request (JSONRPCBaseRequest): Request to act upon

        Note:
            Requests are handled asynchronously if the handler returns a callable, otherwise they are handle
            synchronously by the main thread
        """
        if self._shutdown and request.method != 'exit':
            return

        output = None
        try:
            maybe_handler = self._message_handler(request.method, request.params if request.params is not None else {})
        except MissingMethodException as e:
            log.debug(e)
            # Do not need to notify client of failure with notifications
            output = JSONRPC20Response(_id=request._id, error=JSONRPCMethodNotFound()._data)
        except JSONRPCDispatchException as e:
            output = _make_response(request, error=e.error._data)
        except Exception as e:  # pylint: disable=broad-except
            log.exception('synchronous method handler exception for request: %s', request)
            output = _make_response(request, error=JSONRPCServerError()._data)
        else:
            if request._id in self._received_requests:
                log.error('Received request %s with duplicate id', request.data)
            elif callable(maybe_handler):
                log.debug('Async request %s', request._id)
                self._handle_async_request(request, maybe_handler)
            else:
                output = _make_response(request, result=maybe_handler)
        finally:
            if not request.is_notification and output is not None:
                log.debug('Sync request %s', request._id)
                self._message_manager.write_message(output)

    def _handle_async_request(self, request, handler):
        future = self._executor_service.submit(handler)

        if request.is_notification:
            return

        def did_finish_callback(completed_future):
            del self._received_requests[request._id]
            if completed_future.cancelled():
                log.debug('Cleared cancelled request %d', request._id)
            else:
                try:
                    result = completed_future.result()
                except JSONRPCDispatchException as e:
                    output = _make_response(request, error=e.error._data)
                except Exception as e:  # pylint: disable=broad-except
                    # TODO(forozco): add more descriptive error
                    log.exception('asynchronous method handler exception for request: %s', request)
                    output = _make_response(request, error=JSONRPCServerError()._data)
                else:
                    output = _make_response(request, result=result)
                finally:
                    self._message_manager.write_message(output)

        self._received_requests[request._id] = future
        future.add_done_callback(did_finish_callback)

    def _handle_response(self, response):
        """Handle the response to requests sent from the server to the client.

        Args:
            response: (JSONRPC20Response): Received response

        """
        try:
            request = self._sent_requests[response._id]
        except KeyError:
            log.error('Received unexpected response %s', response.data)
        else:
            log.debug("Received response %s", response.data)

            def cleanup(_):
                del self._sent_requests[response._id]
            request.add_done_callback(cleanup)

            if 'result' in response.data:
                request.set_result(response.result)
            else:
                request.set_exception(JSONRPCDispatchException(**response.error))


def _make_response(request, **kwargs):
    response = RESPONSE_CLASS_MAP[request.JSONRPC_VERSION](_id=request._id, **kwargs)
    response.request = request
    return response
