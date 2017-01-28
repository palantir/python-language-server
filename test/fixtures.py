# Copyright 2017 Palantir Technologies, Inc.
import os
import pytest
from pyls.python_ls import PythonLanguageServer
from pyls.workspace import Workspace
from io import StringIO


@pytest.fixture
def pyls():
    """ Return an initialized python LS """
    rfile = StringIO()
    wfile = StringIO()
    ls = PythonLanguageServer(rfile, wfile)

    ls.m_initialize(
        processId=1,
        rootPath=os.path.dirname(__file__),
        initializationOptions={}
    )

    return ls


@pytest.fixture
def workspace():
    """ Return a workspace """
    return Workspace(os.path.dirname(__file__))
