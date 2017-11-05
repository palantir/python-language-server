# Copyright 2017 Palantir Technologies, Inc.
from pyls import uris
from pyls.workspace import Document
from pyls.plugins import pyflakes_lint

DOC_URI = uris.from_fs_path(__file__)
DOC = """import sys

def hello():
\tpass

import json
"""

DOC_SYNTAX_ERR = """def hello()
    pass
"""


def test_pyflakes():
    doc = Document(DOC_URI, DOC)
    diags = pyflakes_lint.pyls_lint(doc)

    # One we're expecting is:
    msg = '\'sys\' imported but unused'
    unused_import = [d for d in diags if d['message'] == msg][0]

    assert unused_import['range']['start'] == {'line': 0, 'character': 0}


def test_syntax_error_pyflakes():
    doc = Document(DOC_URI, DOC_SYNTAX_ERR)
    diag = pyflakes_lint.pyls_lint(doc)[0]

    assert diag['message'] == 'invalid syntax'
    assert diag['range']['start'] == {'line': 0, 'character': 12}
