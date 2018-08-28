# Copyright 2017 Palantir Technologies, Inc.
import os
from threading import Thread

from jsonrpc.exceptions import JsonRpcMethodNotFound
import pytest

from pyls.python_ls import start_io_lang_server, PythonLanguageServer

CALL_TIMEOUT = 2


def start_client(client):
    client.start()


class _ClientServer(object):
    """ A class to setup a client/server pair """
    def __init__(self):
        # Client to Server pipe
        csr, csw = os.pipe()
        # Server to client pipe
        scr, scw = os.pipe()

        self.server_thread = Thread(target=start_io_lang_server, args=(
            os.fdopen(csr, 'rb'), os.fdopen(scw, 'wb'), PythonLanguageServer
        ))
        self.server_thread.daemon = True
        self.server_thread.start()

        self.client = PythonLanguageServer(os.fdopen(scr, 'rb'), os.fdopen(csw, 'wb'))
        self.client_thread = Thread(target=start_client, args=[self.client])
        self.client_thread.daemon = True
        self.client_thread.start()


@pytest.fixture
def client_server():
    """ A fixture that sets up a client/server pair and shuts down the server """
    client_server_pair = _ClientServer()

    yield client_server_pair.client

    shutdown_response = client_server_pair.client._endpoint.request('shutdown').result(timeout=CALL_TIMEOUT)
    assert shutdown_response is None
    client_server_pair.client._endpoint.notify('exit')


@pytest.fixture
def client_exited_server():
    """ A fixture that sets up a client/server pair and assert the server has already exited """
    client_server_pair = _ClientServer()

    yield client_server_pair.client

    assert client_server_pair.server_thread.is_alive() is False


def test_initialize(client_server):  # pylint: disable=redefined-outer-name
    response = client_server._endpoint.request('initialize', {
        'rootPath': os.path.dirname(__file__),
        'initializationOptions': {}
    }).result(timeout=CALL_TIMEOUT)
    assert 'capabilities' in response


def test_exit_with_parent_process_died(client_exited_server):  # pylint: disable=redefined-outer-name
    # language server should have already exited before responding
    with pytest.raises(Exception):
        client_exited_server._endpoint.request('initialize', {
            'processId': 1234,
            'rootPath': os.path.dirname(__file__),
            'initializationOptions': {}
        }).result(timeout=CALL_TIMEOUT)


def test_missing_message(client_server):  # pylint: disable=redefined-outer-name
    with pytest.raises(JsonRpcMethodNotFound):
        client_server._endpoint.request('unknown_method').result(timeout=CALL_TIMEOUT)
