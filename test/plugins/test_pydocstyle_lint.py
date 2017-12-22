# Copyright 2017 Palantir Technologies, Inc.
from pyls import lsp, uris
from pyls.workspace import Document
from pyls.plugins import pydocstyle_lint

DOC_URI = uris.from_fs_path(__file__)
DOC = """import sys

def hello():
\tpass

import json
"""


def test_pydocstyle():
    doc = Document(DOC_URI, DOC)
    diags = pydocstyle_lint.pyls_lint(doc)

    assert all([d['source'] == 'pydocstyle' for d in diags])

    # One we're expecting is:
    assert diags[0] == {
        'code': 'D100',
        'message': 'D100: Missing docstring in public module',
        'severity': lsp.DiagnosticSeverity.Warning,
        'range': {
            'start': {'line': 0, 'character': 0},
            'end': {'line': 0, 'character': 11},
        },
        'source': 'pydocstyle'
    }


def test_pydocstyle_empty_source():
    doc = Document(DOC_URI, "")
    diags = pydocstyle_lint.pyls_lint(doc)
    assert diags[0]['message'] == 'D100: Missing docstring in public module'
    assert len(diags) == 1


def test_pydocstyle_invalid_source():
    doc = Document(DOC_URI, "bad syntax")
    diags = pydocstyle_lint.pyls_lint(doc)
    # We're unable to parse the file, so can't get any pydocstyle diagnostics
    assert not diags
