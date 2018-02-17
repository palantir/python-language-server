# Copyright 2018 Palantir Technologies, Inc.
from test.fixtures import BASE_HANDLED_RESPONSE
from jsonrpc.jsonrpc2 import JSONRPC20Request, JSONRPC20Response


def test_handle_request_sync(rpc_management):
    rpc_manager, message_manager, message_handler = rpc_management

    rpc_manager.start()
    message_manager.write_message.assert_called_once()
    message_handler.assert_called_once_with('test', {})
    (sent_message, ), _ = message_manager.write_message.call_args
    assert sent_message.data == BASE_HANDLED_RESPONSE.data


def test_handle_request_async(rpc_management):
    rpc_manager, message_manager, message_handler = rpc_management
    response = JSONRPC20Response(_id=1, result="async")

    def wrapper():
        return 'async'
    message_handler.configure_mock(return_value=wrapper)

    rpc_manager.start()
    message_manager.get_messages.assert_any_call()
    message_handler.assert_called_once_with('test', {})

    if rpc_manager._sent_requests:
        rpc_manager._sent_requests.values()[0].result(timeout=1)
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
    rpc_manager, message_manager, _ = rpc_management

    response_future = rpc_manager.call('request', {})
    message_manager.write_message.assert_called_once()
    assert len(rpc_manager._sent_requests) == 1
    request_id = list(rpc_manager._sent_requests.keys())[0]

    response = JSONRPC20Response(_id=request_id, result={})
    message_manager.get_messages.configure_mock(return_value=[response])

    rpc_manager.start()
    message_manager.get_messages.assert_any_call()
    assert not rpc_manager._sent_requests
    assert response_future.result() == response.data


def test_send_notification(rpc_management):
    rpc_manager, message_manager, _ = rpc_management

    rpc_manager.notify('notify', {})
    message_manager.write_message.assert_called_once()
    (sent_message, ), _ = message_manager.write_message.call_args
    assert sent_message.data == (JSONRPC20Request(method='notify', params={}, is_notification=True)).data
