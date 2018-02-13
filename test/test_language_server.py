# Copyright 2017 Palantir Technologies, Inc.
import os
from threading import Thread

import jsonrpc
from jsonrpc.exceptions import JSONRPCMethodNotFound
import pytest

from pyls.language_server import start_io_lang_server
from pyls.python_ls import PythonLanguageServer


class JSONRPCClient(PythonLanguageServer):
    """ This is a weird way of testing.. but we're going to have two JSONRPCServers
    talking to each other. One pretending to be a 'VSCode'-like client, the other is
    our language server """
    pass

def start_client(client):
    client.start()

@pytest.fixture
def client_server():
    """ A fixture to setup a client/server """

    # Client to Server pipe
    csr, csw = os.pipe()
    # Server to client pipe
    scr, scw = os.pipe()

    server = Thread(target=start_io_lang_server, args=(
        os.fdopen(csr, 'rb'), os.fdopen(scw, 'wb'), PythonLanguageServer
    ))
    server.daemon = True
    server.start()

    client = JSONRPCClient(os.fdopen(scr, 'rb'), os.fdopen(csw, 'wb'))
    Thread(target=start_client, args=client)

    yield client, server

    def check(completed_future):
        assert completed_future.result() is None
    client.call('shutdown').add_done_callback(check)
    client.notify('exit')


def test_initialize(client_server):
    client, server = client_server

    def check(completed_future):
        assert 'capabilities' in completed_future.result()
    client.call('initialize', {
        'processId': 1234,
        'rootPath': os.path.dirname(__file__),
        'initializationOptions': {}
    }).add_done_callback(check)


def test_missing_message(client_server):
    client, server = client_server

    def check(result):
        assert result['code'] == JSONRPCMethodNotFound.CODE
    client.call('unknown_method').add_done_callback(check)


def test_linting(client_server):
    client, server = client_server

    # Initialize
    def check(result):
        assert 'capabilities' in result
    client.call('initialize', {
        'processId': 1234,
        'rootPath': os.path.dirname(__file__),
        'initializationOptions': {}
    }).add_done_callback(check)

    # didOpen
    client.notify('textDocument/didOpen', {
        'textDocument': {'uri': 'file:///test', 'text': 'import sys'}
    })
    # assert response['method'] == 'textDocument/publishDiagnostics'
    # assert len(response['params']['diagnostics']) > 0


def _get_notification(client):
    request = jsonrpc.jsonrpc.JSONRPCRequest.from_json(client._read_message().decode('utf-8'))
    assert request.is_notification
    return request.data


def _get_response(client):
    return client._message_manager.get_messages().next().data
