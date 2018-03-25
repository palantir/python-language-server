# Copyright 2017 Palantir Technologies, Inc.
import os
from threading import Thread
import pytest
from pyls.python_ls import start_io_lang_server, PythonLanguageServer
from pyls.jsonrpc.exceptions import JsonRpcMethodNotFound

CALL_TIMEOUT = 2


def start_client(client):
    client.start()


@pytest.fixture
def client_server():
    """ A fixture to setup a client/server """

    # Client to Server pipe
    csr, csw = os.pipe()
    # Server to client pipe
    scr, scw = os.pipe()

    server_thread = Thread(target=start_io_lang_server, args=(
        os.fdopen(csr, 'rb'), os.fdopen(scw, 'wb'), PythonLanguageServer
    ))
    server_thread.daemon = True
    server_thread.start()

    client = PythonLanguageServer(os.fdopen(scr, 'rb'), os.fdopen(csw, 'wb'))
    client_thread = Thread(target=start_client, args=[client])
    client_thread.daemon = True
    client_thread.start()

    yield client

    shutdown_response = client._endpoint.request('shutdown').result(timeout=CALL_TIMEOUT)
    assert shutdown_response is None
    client._endpoint.notify('exit')


def test_initialize(client_server):  # pylint: disable=redefined-outer-name
    response = client_server._endpoint.request('initialize', {
        'processId': 1234,
        'rootPath': os.path.dirname(__file__),
        'initializationOptions': {}
    }).result(timeout=CALL_TIMEOUT)
    assert 'capabilities' in response


def test_missing_message(client_server):  # pylint: disable=redefined-outer-name
    with pytest.raises(JsonRpcMethodNotFound):
        client_server._endpoint.request('unknown_method').result(timeout=CALL_TIMEOUT)
