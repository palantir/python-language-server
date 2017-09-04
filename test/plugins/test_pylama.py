# Copyright 2017 Palantir Technologies, Inc.
from pyls import lsp, uris
from pyls.workspace import Document
from pyls.plugins import pylama_lint

DOC_URI = uris.from_fs_path(__file__)
DOC = """import sys

def hello():
\tpass

import json
"""

DOC_SYNTAX_ERR = """def hello()
    pass
"""


def test_pylama(config):
    doc = Document(DOC_URI, DOC)
    diags = pylama_lint.pyls_lint(doc)

    assert all([d['source'] == 'pylama' for d in diags])

    # One PyFlakes error we're expecting is:
    msg = "W0611 'json' imported but unused [pyflakes]"
    mod_import = [d for d in diags if d['message'] == msg][0]

    assert mod_import['code'] == 'W0611'
    assert mod_import['severity'] == lsp.DiagnosticSeverity.Warning
    assert mod_import['range']['start'] == {'line': 5, 'character': 0}
    assert mod_import['range']['end'] == {'line': 5, 'character': 12}

    # One PyCodeStyle error we're expecting is:
    msg = "W191 indentation contains tabs [pycodestyle]"
    mod_import = [d for d in diags if d['message'] == msg][0]

    assert mod_import['code'] == 'W191'
    assert mod_import['severity'] == lsp.DiagnosticSeverity.Warning
    assert mod_import['range']['start'] == {'line': 3, 'character': 0}
    assert mod_import['range']['end'] == {'line': 3, 'character': 6}
