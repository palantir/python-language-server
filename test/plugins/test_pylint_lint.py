# Copyright 2018 SUSE, Inc
import tempfile
import os
import pytest
from pyls import lsp, uris
from pyls.workspace import Document
from pyls.plugins import pylint_lint

DOC_URI = uris.from_fs_path(__file__)
DOC = """import sys

def hello():
\tpass

import json
"""

DOC_SYNTAX_ERR = """def hello()
    pass
"""

DOC_UNDEFINED_NAME_ERR = "a = b\n"


@pytest.fixture
def make_document():
    created_files = []

    def _make_document(content):
        tmp = tempfile.NamedTemporaryFile(prefix='pylstest', mode='w', delete=False)
        tmp.write(content)
        tmp.close()
        created_files.append(tmp.name)
        return Document(uris.from_fs_path(tmp.name), content)

    yield _make_document

    for path in created_files:
        os.remove(path)


def test_pylint(config, make_document):  # pylint: disable=redefined-outer-name
    doc = make_document(DOC)
    diags = pylint_lint.pyls_lint(config, doc, on_change=False)

    # One we're expecting is:
    msg = 'Unused import sys'
    unused_import = [d for d in diags if d['message'] == msg][0]

    assert unused_import['range']['start'] == {'line': 0, 'character': 0}
    assert unused_import['severity'] == lsp.DiagnosticSeverity.Warning
    assert unused_import['code'] == 'unused-import'


def test_pylint_onchange(config, make_document):  # pylint: disable=redefined-outer-name
    doc = make_document(DOC)
    diags = pylint_lint.pyls_lint(config, doc, on_change=True)

    assert diags == []


def test_syntax_error_pylint(config, make_document):  # pylint: disable=redefined-outer-name
    doc = make_document(DOC_SYNTAX_ERR)
    diag = pylint_lint.pyls_lint(config, doc, on_change=False)[0]

    assert diag['message'] == 'invalid syntax (<string>, line 1)'
    # sadly, pylint, always outputs column to 0 for these errors...
    assert diag['range']['start'] == {'line': 0, 'character': 0}
    assert diag['severity'] == lsp.DiagnosticSeverity.Error
    assert diag['code'] == 'syntax-error'


def test_undefined_name_pylint(config, make_document):  # pylint: disable=redefined-outer-name
    doc = make_document(DOC_UNDEFINED_NAME_ERR)
    diag = pylint_lint.pyls_lint(config, doc, on_change=False)[0]

    assert diag['message'] == 'Undefined variable \'b\''
    assert diag['range']['start'] == {'line': 0, 'character': 4}
    assert diag['severity'] == lsp.DiagnosticSeverity.Error
    assert diag['code'] == 'undefined-variable'
