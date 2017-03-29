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
        os.fdopen(csr), os.fdopen(scw, 'w'), PythonLanguageServer
    ))
    server.daemon = True
    server.start()

    client = JSONRPCClient(os.fdopen(scr), os.fdopen(csw, 'w'))

    yield client, server

    try:
        client.call('shutdown')
    except:
        pass


def test_initialize(client_server):
    client, server = client_server

    client.call('initialize', {
        'processId': 1234,
        'rootPath': os.path.dirname(__file__),
        'initializationOptions': {}
    })
    response = _next_message(client)

    assert 'capabilities' in response['result']


def test_file_closed(client_server):
    client, server = client_server
    client.rfile.close()
    with pytest.raises(Exception):
        _next_message(client)


def test_missing_message(client_server):
    client, server = client_server

    client.call('unknown_method')
    response = _next_message(client)
    assert response['error']['code'] == -32601  # Method not implemented error


def test_linting(client_server):
    client, server = client_server

    # Initialize
    client.call('initialize', {
        'processId': 1234,
        'rootPath': os.path.dirname(__file__),
        'initializationOptions': {}
    })
    response = _next_message(client)

    assert 'capabilities' in response['result']

    # didOpen
    client.call('textDocument/didOpen', {
        'textDocument': {'uri': 'file:///test', 'text': 'import sys'}
    })
    response = _next_message(client)

    assert response['method'] == 'textDocument/publishDiagnostics'
    assert len(response['params']['diagnostics']) > 0


def _next_message(client):
    return json.loads(client._read_message())
