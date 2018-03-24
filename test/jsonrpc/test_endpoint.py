# Copyright 2018 Palantir Technologies, Inc.
# pylint: disable=redefined-outer-name
import time
import mock
import pytest

from pyls.jsonrpc import exceptions
from pyls.jsonrpc.endpoint import Endpoint

MSG_ID = 'id'


@pytest.fixture()
def dispatcher():
    return {}


@pytest.fixture()
def consumer():
    return mock.MagicMock()


@pytest.fixture()
def endpoint(dispatcher, consumer):
    return Endpoint(dispatcher, consumer, id_generator=lambda: MSG_ID)


def test_bad_message(endpoint):
    # Ensure doesn't raise for a bad message
    endpoint.consume({'key': 'value'})


def test_notify(endpoint, consumer):
    endpoint.notify('methodName', {'key': 'value'})
    consumer.assert_called_once_with({
        'jsonrpc': '2.0',
        'method': 'methodName',
        'params': {'key': 'value'}
    })


def test_notify_none_params(endpoint, consumer):
    endpoint.notify('methodName', None)
    consumer.assert_called_once_with({
        'jsonrpc': '2.0',
        'method': 'methodName',
    })


def test_request(endpoint, consumer):
    future = endpoint.request('methodName', {'key': 'value'})
    assert not future.done()

    consumer.assert_called_once_with({
        'jsonrpc': '2.0',
        'id': MSG_ID,
        'method': 'methodName',
        'params': {'key': 'value'}
    })

    # Send the response back to the endpoint
    result = 1234
    endpoint.consume({
        'jsonrpc': '2.0',
        'id': MSG_ID,
        'result': result
    })

    assert future.result(timeout=2) == result


def test_request_error(endpoint, consumer):
    future = endpoint.request('methodName', {'key': 'value'})
    assert not future.done()

    consumer.assert_called_once_with({
        'jsonrpc': '2.0',
        'id': MSG_ID,
        'method': 'methodName',
        'params': {'key': 'value'}
    })

    # Send an error back from the client
    error = exceptions.JsonRpcInvalidRequest(data=1234)
    endpoint.consume({
        'jsonrpc': '2.0',
        'id': MSG_ID,
        'error': error.to_dict()
    })

    # Verify the exception raised by the future is the same as the error the client serialized
    with pytest.raises(exceptions.JsonRpcException) as exc_info:
        assert future.result(timeout=2)
    assert exc_info.type == exceptions.JsonRpcInvalidRequest
    assert exc_info.value == error


def test_request_cancel(endpoint, consumer):
    future = endpoint.request('methodName', {'key': 'value'})
    assert not future.done()

    consumer.assert_called_once_with({
        'jsonrpc': '2.0',
        'id': MSG_ID,
        'method': 'methodName',
        'params': {'key': 'value'}
    })

    # Cancel the request
    future.cancel()
    consumer.assert_any_call({
        'jsonrpc': '2.0',
        'method': '$/cancelRequest',
        'params': {'id': MSG_ID}
    })

    with pytest.raises(exceptions.JsonRpcException) as exc_info:
        assert future.result(timeout=2)
    assert exc_info.type == exceptions.JsonRpcRequestCancelled


def test_consume_notification(endpoint, dispatcher):
    handler = mock.Mock()
    dispatcher['methodName'] = handler

    endpoint.consume({
        'jsonrpc': '2.0',
        'method': 'methodName',
        'params': {'key': 'value'}
    })
    handler.assert_called_once_with({'key': 'value'})


def test_consume_notification_error(endpoint, dispatcher):
    handler = mock.Mock(side_effect=ValueError)
    dispatcher['methodName'] = handler
    # Verify the consume doesn't throw
    endpoint.consume({
        'jsonrpc': '2.0',
        'method': 'methodName',
        'params': {'key': 'value'}
    })
    handler.assert_called_once_with({'key': 'value'})


def test_consume_notification_method_not_found(endpoint):
    # Verify consume doesn't throw for method not found
    endpoint.consume({
        'jsonrpc': '2.0',
        'method': 'methodName',
        'params': {'key': 'value'}
    })


def test_consume_async_notification_error(endpoint, dispatcher):
    def _async_handler(params):
        assert params == {'key': 'value'}
        raise ValueError()
    handler = mock.Mock(return_value=_async_handler)
    dispatcher['methodName'] = handler

    # Verify the consume doesn't throw
    endpoint.consume({
        'jsonrpc': '2.0',
        'method': 'methodName',
        'params': {'key': 'value'}
    })
    handler.assert_called_once_with({'key': 'value'})


def test_consume_request(endpoint, consumer, dispatcher):
    result = 1234
    handler = mock.Mock(return_value=result)
    dispatcher['methodName'] = handler

    endpoint.consume({
        'jsonrpc': '2.0',
        'id': MSG_ID,
        'method': 'methodName',
        'params': {'key': 'value'}
    })

    handler.assert_called_once_with({'key': 'value'})
    consumer.assert_called_once_with({
        'jsonrpc': '2.0',
        'id': MSG_ID,
        'result': result
    })


def test_consume_async_request(endpoint, consumer, dispatcher):
    def _async_handler(params):
        assert params == {'key': 'value'}
        return 1234
    handler = mock.Mock(return_value=_async_handler)
    dispatcher['methodName'] = handler

    endpoint.consume({
        'jsonrpc': '2.0',
        'id': MSG_ID,
        'method': 'methodName',
        'params': {'key': 'value'}
    })

    handler.assert_called_once_with({'key': 'value'})
    consumer.assert_called_once_with({
        'jsonrpc': '2.0',
        'id': MSG_ID,
        'result': 1234
    })


@pytest.mark.parametrize('exc,error', [
    (ValueError, exceptions.JsonRpcInternalError.of(ValueError())),
    (KeyError, exceptions.JsonRpcInternalError.of(KeyError())),
    (exceptions.JsonRpcMethodNotFound, exceptions.JsonRpcMethodNotFound()),
])
def test_consume_async_request_error(exc, error, endpoint, consumer, dispatcher):
    def _async_handler(params):
        assert params == {'key': 'value'}
        raise exc()
    handler = mock.Mock(return_value=_async_handler)
    dispatcher['methodName'] = handler

    endpoint.consume({
        'jsonrpc': '2.0',
        'id': MSG_ID,
        'method': 'methodName',
        'params': {'key': 'value'}
    })

    handler.assert_called_once_with({'key': 'value'})
    consumer.assert_called_once_with({
        'jsonrpc': '2.0',
        'id': MSG_ID,
        'error': error.to_dict()
    })


def test_consume_request_method_not_found(endpoint, consumer):
    endpoint.consume({
        'jsonrpc': '2.0',
        'id': MSG_ID,
        'method': 'methodName',
        'params': {'key': 'value'}
    })
    consumer.assert_called_once_with({
        'jsonrpc': '2.0',
        'id': MSG_ID,
        'error': exceptions.JsonRpcMethodNotFound().to_dict()
    })


@pytest.mark.parametrize('exc,error', [
    (ValueError, exceptions.JsonRpcInternalError.of(ValueError())),
    (KeyError, exceptions.JsonRpcInternalError.of(KeyError())),
    (exceptions.JsonRpcMethodNotFound.of("method"), exceptions.JsonRpcMethodNotFound.of("method")),
])
def test_consume_request_error(exc, error, endpoint, consumer, dispatcher):
    handler = mock.Mock(side_effect=exc)
    dispatcher['methodName'] = handler

    endpoint.consume({
        'jsonrpc': '2.0',
        'id': MSG_ID,
        'method': 'methodName',
        'params': {'key': 'value'}
    })

    handler.assert_called_once_with({'key': 'value'})
    consumer.assert_called_once_with({
        'jsonrpc': '2.0',
        'id': MSG_ID,
        'error': error.to_dict()
    })


def test_consume_request_cancel(endpoint, dispatcher):
    def async_handler(params):
        assert params == {'key': 'value'}
        time.sleep(3)
    handler = mock.Mock(return_value=async_handler)
    dispatcher['methodName'] = handler

    endpoint.consume({
        'jsonrpc': '2.0',
        'id': MSG_ID,
        'method': 'methodName',
        'params': {'key': 'value'}
    })
    handler.assert_called_once_with({'key': 'value'})

    endpoint.consume({
        'jsonrpc': '2.0',
        'method': '$/cancelRequest',
        'params': {'id': MSG_ID}
    })

    # Because Python's Future cannot be cancelled once it's started, the request is never actually cancelled
    # consumer.assert_called_once_with({
    #     'jsonrpc': '2.0',
    #     'id': MSG_ID,
    #     'error': exceptions.JsonRpcRequestCancelled().to_dict()
    # })


def test_consume_request_cancel_unknown(endpoint):
    # Verify consume doesn't throw
    endpoint.consume({
        'jsonrpc': '2.0',
        'method': '$/cancelRequest',
        'params': {'id': 'unknown identifier'}
    })
