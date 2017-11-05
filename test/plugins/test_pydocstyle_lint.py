# Copyright 2017 Palantir Technologies, Inc.
from pyls import uris
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
    msg = 'D100: Missing docstring in public module'
    unused_import = [d for d in diags if d['message'] == msg][0]

    assert unused_import['range']['start'] == {'line': 0, 'character': 0}
