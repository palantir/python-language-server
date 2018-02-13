# Copyright 2017 Palantir Technologies, Inc.
import pytest
import os
from pyls import uris
from pyls.rpc_manager import JSONRPCManager
from pyls.config.config import Config
from pyls.python_ls import PythonLanguageServer
from pyls.workspace import Workspace
from StringIO import StringIO


@pytest.fixture
def rpc_manager(tmpdir):
    # JSONRPCManager rx
    manager_rx, tester_tx = os.pipe()
    # Server to client pipe
    tester_rx, manager_tx = os.pipe()

    yield JSONRPCManager(os.fdopen(manager_rx, tester_tx), tester_tx, tester_rx



@pytest.fixture
def pyls(tmpdir):
    """ Return an initialized python LS """
    rfile = StringIO()
    wfile = StringIO()
    ls = PythonLanguageServer(rfile, wfile)

    ls.m_initialize(
        processId=1,
        rootUri=uris.from_fs_path(str(tmpdir)),
        initializationOptions={}
    )

    return ls


@pytest.fixture
def workspace(tmpdir):
    """Return a workspace."""
    return Workspace(uris.from_fs_path(str(tmpdir)))


@pytest.fixture
def config(workspace):
    """Return a config object."""
    return Config(workspace.root_uri, {})
