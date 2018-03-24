# Copyright 2017 Palantir Technologies, Inc.
import os
import sys
from mock import Mock
import pytest
from jsonrpc.jsonrpc2 import JSONRPC20Response, JSONRPC20Request

from pyls import uris
from pyls.config.config import Config
from pyls.json_rpc.manager import JSONRPCManager
from pyls.json_rpc.server import JSONRPCServer
from pyls.python_ls import PythonLanguageServer
from pyls.workspace import Workspace, Document

if sys.version_info[0] < 3:
    from StringIO import StringIO
else:
    from io import StringIO

BASE_HANDLED_RESPONSE_CONTENT = 'handled'
BASE_HANDLED_RESPONSE = JSONRPC20Response(_id=1, result=BASE_HANDLED_RESPONSE_CONTENT)

DOC_URI = uris.from_fs_path(__file__)
DOC = """import sys

def main():
    print sys.stdin.read()
"""


@pytest.fixture
def pyls(tmpdir):
    """ Return an initialized python LS """
    ls = PythonLanguageServer(StringIO, StringIO)

    ls.m_initialize(
        processId=1,
        rootUri=uris.from_fs_path(str(tmpdir)),
        initializationOptions={}
    )

    return ls


@pytest.fixture
def workspace(tmpdir):
    """Return a workspace."""
    return Workspace(uris.from_fs_path(str(tmpdir)), Mock())


@pytest.fixture
def rpc_management():
    message_manager = Mock(**{'get_messages.return_value': [JSONRPC20Request(_id=1, method='test', params={})]})
    message_handler = Mock(return_value=BASE_HANDLED_RESPONSE_CONTENT)
    rpc_manager = JSONRPCManager(message_manager, message_handler)

    yield rpc_manager, message_manager, message_handler,

    rpc_manager.exit()


@pytest.fixture
def json_rpc_server():
    manager_rx, tester_tx = os.pipe()
    tester_rx, manager_tx = os.pipe()

    client = JSONRPCServer(os.fdopen(manager_rx, 'rb'), os.fdopen(manager_tx, 'wb'))
    server = JSONRPCServer(os.fdopen(tester_rx, 'rb'), os.fdopen(tester_tx, 'wb'))

    yield client, server

    client.close()
    server.close()


@pytest.fixture
def config(workspace):  # pylint: disable=redefined-outer-name
    """Return a config object."""
    return Config(workspace.root_uri, {})


@pytest.fixture
def doc():
    return Document(DOC_URI, DOC)
