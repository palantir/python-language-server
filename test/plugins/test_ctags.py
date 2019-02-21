# Copyright 2017 Palantir Technologies, Inc.
# pylint: disable=redefined-outer-name
import os
import tempfile

import pytest

import pyls
from pyls import lsp
from pyls.plugins import ctags


@pytest.fixture(scope='session')
def pyls_ctags():
    """Fixture for generating ctags for the Python Langyage Server"""
    fd, tag_file = tempfile.mkstemp()
    os.close(fd)  # Close our handle to the file, we just want the path

    try:
        ctags.execute("ctags", tag_file, os.path.dirname(pyls.__file__))
        yield tag_file
    finally:
        os.unlink(tag_file)


def test_parse_tags(pyls_ctags):
    # Search for CtagsPlugin with the query 'tagsplug'
    plugin_symbol = next(ctags.parse_tags(pyls_ctags, "tagsplug"))

    assert plugin_symbol['name'] == 'CtagsPlugin'
    assert plugin_symbol['kind'] == lsp.SymbolKind.Class
    assert plugin_symbol['location']['uri'].endswith('pyls/plugins/ctags.py')
