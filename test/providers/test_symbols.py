# Copyright 2017 Palantir Technologies, Inc.
from pyls.providers.symbols import JediDocumentSymbolsProvider
from pyls.vscode import SymbolKind

DOC_URI = __file__
DOC = """import sys

a = 'hello'

class B(object):
    pass

def main():
    pass
"""


def test_symbols(workspace):
    workspace.put_document(DOC_URI, DOC)
    provider = JediDocumentSymbolsProvider(workspace)

    symbols = provider.run(DOC_URI)

    # All four symbols (import sys, a, B, main)
    assert len(symbols) == 4

    def sym(name):
        return [s for s in symbols if s['name'] == name][0]

    # Check we have some sane mappings to VSCode constants
    assert sym('sys')['kind'] == SymbolKind.Module
    assert sym('a')['kind'] == SymbolKind.Variable
    assert sym('B')['kind'] == SymbolKind.Class
    assert sym('main')['kind'] == SymbolKind.Function

    # Not going to get too in-depth here else we're just testing Jedi
    assert sym('a')['location']['range']['start'] == {'line': 2, 'character': 0}
