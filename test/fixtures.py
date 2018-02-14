# Copyright 2017 Palantir Technologies, Inc.
import pytest
import os
from pyls import uris
from pyls.message_manager import MessageManager
from pyls.config.config import Config
from pyls.python_ls import PythonLanguageServer
from pyls.workspace import Workspace
from StringIO import StringIO


@pytest.fixture
def message_manager(tmpdir):
    manager_rx, tester_tx = os.pipe()
    tester_rx, manager_tx = os.pipe()

    rx, tx, = os.fdopen(tester_rx, 'rb'), os.fdopen(tester_tx, 'wb')

    yield MessageManager(os.fdopen(manager_rx, 'rb'), os.fdopen(tester_tx, 'wb')), rx, tx

    rx.close()
    tx.close()


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
