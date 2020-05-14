# Copyright 2017 Palantir Technologies, Inc.
import os
import sys
from test.test_utils import MockWorkspace

import pytest

from pyls import uris
from pyls.lsp import SymbolKind
from pyls.plugins.symbols import pyls_document_symbols
from pyls.workspace import Document

LINUX = sys.platform.startswith('linux')
CI = os.environ.get('CI')
DOC_URI = uris.from_fs_path(__file__)
DOC = """import sys

a = 'hello'

class B:
    def __init__(self):
        x = 2
        self.y = x

def main(x):
    y = 2 * x
    return y

"""


def helper_check_symbols_all_scope(symbols):
    # All eight symbols (import sys, a, B, __init__, x, y, main, y)
    assert len(symbols) == 8

    def sym(name):
        return [s for s in symbols if s['name'] == name][0]

    # Check we have some sane mappings to VSCode constants
    assert sym('a')['kind'] == SymbolKind.Variable
    assert sym('B')['kind'] == SymbolKind.Class
    assert sym('__init__')['kind'] == SymbolKind.Function
    assert sym('main')['kind'] == SymbolKind.Function

    # Not going to get too in-depth here else we're just testing Jedi
    assert sym('a')['location']['range']['start'] == {'line': 2, 'character': 0}


def test_symbols(config, workspace):
    doc = Document(DOC_URI, workspace, DOC)
    config.update({'plugins': {'jedi_symbols': {'all_scopes': False}}})
    symbols = pyls_document_symbols(config, doc)

    # All four symbols (import sys, a, B, main)
    # y is not in the root scope, it shouldn't be returned
    assert len(symbols) == 4

    def sym(name):
        return [s for s in symbols if s['name'] == name][0]

    # Check we have some sane mappings to VSCode constants
    assert sym('a')['kind'] == SymbolKind.Variable
    assert sym('B')['kind'] == SymbolKind.Class
    assert sym('main')['kind'] == SymbolKind.Function

    # Not going to get too in-depth here else we're just testing Jedi
    assert sym('a')['location']['range']['start'] == {'line': 2, 'character': 0}

    # Ensure that the symbol range spans the whole definition
    assert sym('main')['location']['range']['start'] == {'line': 9, 'character': 0}
    assert sym('main')['location']['range']['end'] == {'line': 12, 'character': 0}


def test_symbols_all_scopes(config, workspace):
    doc = Document(DOC_URI, workspace, DOC)
    symbols = pyls_document_symbols(config, doc)
    helper_check_symbols_all_scope(symbols)


@pytest.mark.skipif(not LINUX or not CI, reason="tested on linux and python 3 only")
def test_symbols_all_scopes_with_jedi_environment(config):
    doc = Document(DOC_URI, MockWorkspace(), DOC)

    # Update config extra environment
    env_path = '/tmp/pyenv/bin/python'
    config.update({'plugins': {'jedi': {'environment': env_path}}})
    doc.update_config(config)
    symbols = pyls_document_symbols(config, doc)
    helper_check_symbols_all_scope(symbols)
