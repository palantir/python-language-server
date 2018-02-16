# Copyright 2018 Palantir Technologies, Inc.
from jsonrpc.jsonrpc2 import JSONRPC20Request, JSONRPC20Response, JSONRPC20BatchRequest


def test_receive_request(json_rpc_server):
    client, server = json_rpc_server
    request = JSONRPC20Request(_id=0, method='initialize', params={})
    client.write_message(request)
    message = next(server.get_messages())
    assert isinstance(message, JSONRPC20Request)
    assert request.data == message.data
    assert not message.is_notification


def test_receive_notification(json_rpc_server):
    client, server = json_rpc_server
    notification = JSONRPC20Request(method='initialize', params={}, is_notification=True)
    client.write_message(notification)
    message = next(server.get_messages())
    assert isinstance(message, JSONRPC20Request)
    assert notification.data == message.data
    assert message.is_notification


def test_receive_response(json_rpc_server):
    client, server = json_rpc_server
    response = JSONRPC20Response(_id=0, result={})
    client.write_message(response)
    message = next(server.get_messages())
    assert isinstance(message, JSONRPC20Response)
    assert response.data == message.data


def test_drop_bad_message(json_rpc_server):
    client, server = json_rpc_server
    response = JSONRPC20Response(_id=0, result={})
    client.write_message(response)
    server.close()
    try:
        next(server.get_messages())
    except StopIteration:
        pass
    else:
        assert False


def test_recieve_batch_request(json_rpc_server):
    client, server = json_rpc_server
    request_1 = JSONRPC20Request(_id=1, method='test_2', params={})
    request_2 = JSONRPC20Request(_id=2, method='test_2', params={})
    request = JSONRPC20BatchRequest(request_1, request_2)
    client.write_message(request)

    messages = server.get_messages()
    message_1 = next(messages)
    message_2 = next(messages)
    assert isinstance(message_1, JSONRPC20Request)
    assert request_1.data == message_1.data
    assert isinstance(message_2, JSONRPC20Request)
    assert request_2.data == message_2.data


def test_send_batch_request_notification(json_rpc_server):
    client, server = json_rpc_server
    request_1 = JSONRPC20Request(_id=1, method='test_1', params={})
    request_2 = JSONRPC20Request(method='test_2', params={})
    request = JSONRPC20BatchRequest(request_1, request_2)
    client.write_message(request)

    # load batch request
    next(server.get_messages())

    response_1 = JSONRPC20Response(_id=1, result='response_1')
    server.write_message(response_1)

    response = next(client.get_messages())
    assert response.data == response_1.data
