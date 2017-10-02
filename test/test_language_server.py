# Copyright 2017 Palantir Technologies, Inc.
import json
import os
from threading import Thread

import jsonrpc
import pytest

from pyls.server import JSONRPCServer
from pyls.language_server import start_io_lang_server
from pyls.python_ls import PythonLanguageServer


class JSONRPCClient(JSONRPCServer):
    """ This is a weird way of testing.. but we're going to have two JSONRPCServers
    talking to each other. One pretending to be a 'VSCode'-like client, the other is
    our language server """
    pass


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

    yield client, server

    client.call('shutdown')
    response = _get_response(client)
    assert response['result'] is None
    client.notify('exit')


def test_initialize(client_server):
    client, server = client_server

    client.call('initialize', {
        'processId': 1234,
        'rootPath': os.path.dirname(__file__),
        'initializationOptions': {}
    })
    response = _get_response(client)

    assert 'capabilities' in response['result']


def test_missing_message(client_server):
    client, server = client_server

    client.call('unknown_method')
    response = _get_response(client)
    assert response['error']['code'] == -32601  # Method not implemented error


def test_linting(client_server):
    client, server = client_server

    # Initialize
    client.call('initialize', {
        'processId': 1234,
        'rootPath': os.path.dirname(__file__),
        'initializationOptions': {}
    })
    response = _get_response(client)

    assert 'capabilities' in response['result']

    # didOpen
    client.notify('textDocument/didOpen', {
        'textDocument': {'uri': 'file:///test', 'text': 'import sys'}
    })
    response = _get_notification(client)

    assert response['method'] == 'textDocument/publishDiagnostics'
    assert len(response['params']['diagnostics']) > 0


def _get_notification(client):
    request = jsonrpc.jsonrpc.JSONRPCRequest.from_json(client._read_message().decode('utf-8'))
    assert request.is_notification
    return request.data


def _get_response(client):
    return json.loads(client._read_message().decode('utf-8'))
