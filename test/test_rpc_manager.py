# Copyright 2018 Palantir Technologies, Inc.
import pytest
import time
from StringIO import StringIO
from jsonrpc.jsonrpc2 import JSONRPC20Request, JSONRPC20Response
from pyls.message_manager import MessageManager
from pyls.rpc_manager import JSONRPCManager
from mock import Mock


BASE_HANDLED_RESPONSE_CONTENT = 'handled'
BASE_HANDLED_RESPONSE = JSONRPC20Response(_id=1, result=BASE_HANDLED_RESPONSE_CONTENT)

@pytest.fixture
def rpc_management():
    message_manager = MessageManager(StringIO(), StringIO())
    message_manager.get_messages = Mock(return_value=[JSONRPC20Request(_id=1, method='test', params={})])
    message_manager.write_message = Mock()
    message_handler = Mock(return_value=BASE_HANDLED_RESPONSE_CONTENT)
    rpc_manager = JSONRPCManager(message_manager, message_handler)

    yield rpc_manager, message_manager, message_handler,

    rpc_manager.exit()


def test_handle_request_sync(rpc_management):
    rpc_manager, message_manager, message_handler = rpc_management

    rpc_manager.start()
    message_manager.get_messages.assert_any_call()
    message_manager.write_message.assert_called_once_with(BASE_HANDLED_RESPONSE.data)
    message_handler.assert_called_once_with('test', {})


def test_handle_request_async(rpc_management):
    rpc_manager, message_manager, message_handler = rpc_management
    response = JSONRPC20Response(_id=1, result="async")

    def wrapper():
        return 'async'
    message_handler.configure_mock(return_value=wrapper)

    rpc_manager.start()
    message_manager.get_messages.assert_any_call()
    message_handler.assert_called_once_with('test', {})
    time.sleep(1)
    message_manager.write_message.assert_called_once_with(response.data)


def test_handle_notification_sync(rpc_management):
    rpc_manager, message_manager, message_handler = rpc_management
    notification = JSONRPC20Request(method='notification', params={}, is_notification=True)
    message_manager.get_messages.configure_mock(return_value=[notification])

    rpc_manager.start()
    message_manager.get_messages.assert_any_call()
    message_handler.assert_called_once_with('notification', {})
    message_manager.write_message.assert_not_called()


def test_handle_notification_sync_empty(rpc_management):
    rpc_manager, message_manager, message_handler = rpc_management
    notification = JSONRPC20Request(method='notification', params=None, is_notification=True)
    message_manager.get_messages.configure_mock(return_value=[notification])

    rpc_manager.start()
    message_manager.get_messages.assert_any_call()
    message_handler.assert_called_once_with('notification', {})
    message_manager.write_message.assert_not_called()


def test_handle_notification_async(rpc_management):
    rpc_manager, message_manager, message_handler = rpc_management
    notification = JSONRPC20Request(method='notification', params={}, is_notification=True)
    def wrapper():
        pass
    message_handler.configure_mock(return_value=wrapper)
    message_manager.get_messages.configure_mock(return_value=[notification])

    rpc_manager.start()
    message_manager.get_messages.assert_any_call()
    message_handler.assert_called_once_with('notification', {})
    message_manager.write_message.assert_not_called()


def test_handle_notification_async_empty(rpc_management):
    rpc_manager, message_manager, message_handler = rpc_management
    notification = JSONRPC20Request(method='notification', params=None, is_notification=True)
    def wrapper():
        pass
    message_handler.configure_mock(return_value=wrapper)
    message_manager.get_messages.configure_mock(return_value=[notification])

    rpc_manager.start()
    message_manager.get_messages.assert_any_call()
    message_handler.assert_called_once_with('notification', {})
    message_manager.write_message.assert_not_called()


def test_send_request(rpc_management):
    rpc_manager, message_manager, message_handler = rpc_management

    response_future = rpc_manager.call('request', {})
    message_manager.write_message.assert_called_once()
    assert len(rpc_manager._sent_requests) == 1
    request_id = rpc_manager._sent_requests.keys()[0]

    response = JSONRPC20Response(_id=request_id, result={})
    message_manager.get_messages.configure_mock(return_value=[response])

    rpc_manager.start()
    message_manager.get_messages.assert_any_call()
    assert not rpc_manager._sent_requests
    assert response_future.result() == response.data


def test_send_notification(rpc_management):
    rpc_manager, message_manager, message_handler = rpc_management

    rpc_manager.notify('notify', {})
    message_manager.write_message.assert_called_once_with(JSONRPC20Request(method='notify', params={}).data)

