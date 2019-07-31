# Copyright 2017 Palantir Technologies, Inc.
from distutils.version import LooseVersion
import jedi
import pytest

from pyls import uris
from pyls.plugins.symbols import pyls_document_symbols
from pyls.lsp import SymbolKind
from pyls.workspace import Document

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


@pytest.mark.skipif(LooseVersion(jedi.__version__) < LooseVersion('0.14.0'),
                    reason='This test fails with previous versions of jedi')
def test_symbols(config):
    doc = Document(DOC_URI, DOC)
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


def test_symbols_all_scopes(config):
    doc = Document(DOC_URI, DOC)
    symbols = pyls_document_symbols(config, doc)

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
