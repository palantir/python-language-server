# Copyright 2017 Palantir Technologies, Inc.
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


def test_symbols(config):
    doc = Document(DOC_URI, DOC)
    config.update({'plugins': {'jedi_symbols': {'all_scopes': False, 'hide_imports': True}}})
    symbols = pyls_document_symbols(config, doc)

    # Only local symbols (a, B, main, y)
    assert len(symbols) == 4

    config.update({'plugins': {'jedi_symbols': {'all_scopes': False, 'hide_imports': False}}})
    symbols = pyls_document_symbols(config, doc)

    # All five symbols (import sys, a, B, main, y)
    assert len(symbols) == 5

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

    config.update({'plugins': {'jedi_symbols': {'all_scopes': True, 'hide_imports': True}}})
    symbols = pyls_document_symbols(config, doc)

    # Only local symbols (a, B, __init__, x, y, main, y)
    assert len(symbols) == 7

    config.update({'plugins': {'jedi_symbols': {'all_scopes': True, 'hide_imports': False}}})
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

def test_symbols_hierarchical(config):
    doc = Document(DOC_URI, DOC)

    config.update({'plugins': {'jedi_symbols': {'hierarchical_symbols': True, 'hide_imports': True}}})
    symbols = pyls_document_symbols(config, doc)

    # Only local symbols (a, B, main, y)
    assert len(symbols) == 4

    config.update({'plugins': {'jedi_symbols': {'hierarchical_symbols': True, 'hide_imports': False}}})
    symbols = pyls_document_symbols(config, doc)

    # All five symbols (import sys, a, B, main, y)
    assert len(symbols) == 5

    def sym(name):
        return [s for s in symbols if s['name'] == name][0]
    def child_sym(sym, name):
        if not sym['children']:
            return None
        return [s for s in sym['children'] if s['name'] == name][0]

    # Check we have some sane mappings to VSCode constants
    assert sym('a')['kind'] == SymbolKind.Variable
    assert sym('B')['kind'] == SymbolKind.Class
    assert len(sym('B')['children']) == 1
    assert child_sym(sym('B'), '__init__')['kind'] == SymbolKind.Function
    assert child_sym(sym('B'), '__init__')['detail'] == 'B.__init__'
    assert sym('main')['kind'] == SymbolKind.Function