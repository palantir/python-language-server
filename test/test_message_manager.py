# Copyright 2018 Palantir Technologies, Inc.
import pytest
import os
from jsonrpc.jsonrpc2 import JSONRPC20Request, JSONRPC20Response
from pyls.message_manager import MessageManager

@pytest.fixture
def message_manager(tmpdir):
    manager_rx, tester_tx = os.pipe()
    tester_rx, manager_tx = os.pipe()

    client = MessageManager(os.fdopen(manager_rx, 'rb'), os.fdopen(manager_tx, 'wb'))
    server = MessageManager(os.fdopen(tester_rx, 'rb'), os.fdopen(tester_tx, 'wb'))

    yield client, server

    client.close()
    server.close()


def test_receive_request(message_manager):
    client, server = message_manager
    request = {'jsonrpc': '2.0', 'id': 0, 'method': 'initialize', 'params': {}}
    client.write_message(request)
    message = server.get_messages().next()
    assert isinstance(message, JSONRPC20Request)
    assert request == message.data
    assert not message.is_notification


def test_receive_notification(message_manager):
    client, server = message_manager
    notification = {'jsonrpc': '2.0', 'method': 'notify', 'params': {}}
    client.write_message(notification)
    message = server.get_messages().next()
    assert isinstance(message, JSONRPC20Request)
    assert notification == message.data
    assert message.is_notification


def test_receive_response(message_manager):
    client, server = message_manager
    response = {'jsonrpc': '2.0', 'id': 0, 'result': {}}
    client.write_message(response)
    message = server.get_messages().next()
    assert isinstance(message, JSONRPC20Response )
    assert response == message.data


def test_drop_bad_message(message_manager):
    client, server = message_manager
    response = {'jsonrpc': '2.0', 'id': 0, 'result': {}}
    client.write_message(response)
    server.close()
    try:
        server.get_messages().next()
    except StopIteration:
        pass
    else:
        assert False
