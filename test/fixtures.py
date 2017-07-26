# Copyright 2017 Palantir Technologies, Inc.
import os
import pytest
from pyls.config import Config
from pyls.python_ls import PythonLanguageServer
from pyls.workspace import Workspace
from io import StringIO
from urllib.parse import urljoin
from urllib.request import pathname2url


def path2uri(path):
    return urljoin(u"file://", pathname2url(path))

@pytest.fixture
def pyls(tmpdir):
    """ Return an initialized python LS """
    rfile = StringIO()
    wfile = StringIO()
    ls = PythonLanguageServer(rfile, wfile)

    ls.m_initialize(
        processId=1,
        rootUri=path2uri(str(tmpdir)),
        initializationOptions={}
    )

    return ls


@pytest.fixture
def workspace():
    """Return a workspace."""
    return Workspace(path2uri(os.path.dirname(__file__)))


@pytest.fixture
def config(workspace):
    """Return a config object."""
    return Config(workspace.root, {})
