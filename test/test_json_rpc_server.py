# Copyright 2018 Palantir Technologies, Inc.
from jsonrpc.jsonrpc2 import JSONRPC20Request, JSONRPC20Response


def test_receive_request(json_rpc_server):
    client, server = json_rpc_server
    request = {'jsonrpc': '2.0', 'id': 0, 'method': 'initialize', 'params': {}}
    client.write_message(request)
    message = next(server.get_messages())
    assert isinstance(message, JSONRPC20Request)
    assert request == message.data
    assert not message.is_notification


def test_receive_notification(json_rpc_server):
    client, server = json_rpc_server
    notification = {'jsonrpc': '2.0', 'method': 'notify', 'params': {}}
    client.write_message(notification)
    message = next(server.get_messages())
    assert isinstance(message, JSONRPC20Request)
    assert notification == message.data
    assert message.is_notification


def test_receive_response(json_rpc_server):
    client, server = json_rpc_server
    response = {'jsonrpc': '2.0', 'id': 0, 'result': {}}
    client.write_message(response)
    message = next(server.get_messages())
    assert isinstance(message, JSONRPC20Response)
    assert response == message.data


def test_drop_bad_message(json_rpc_server):
    client, server = json_rpc_server
    response = {'jsonrpc': '2.0', 'id': 0, 'result': {}}
    client.write_message(response)
    server.close()
    try:
        next(server.get_messages())
    except StopIteration:
        pass
    else:
        assert False
