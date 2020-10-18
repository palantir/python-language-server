from pyls import lsp, uris
from pyls.workspace import Document
from pyls.plugins import jedi_lint

DOC_URI = uris.from_fs_path(__file__)
DOC = """import sys

def hello():
\tpass

import json
"""

DOC_SYNTAX_ERR = """def hello()
    pass
"""

DOC_INDENT_ERR = """def hello():
    x = 1
  pass
"""

DOC_ENCODING = u"""# encoding=utf-8
import sys
"""


def test_jedi_lint(workspace):
    doc = Document(DOC_URI, workspace, DOC)
    diags = jedi_lint.pyls_lint(doc)

    assert len(diags) == 0


def test_syntax_error_jedi(workspace):
    doc = Document(DOC_URI, workspace, DOC_SYNTAX_ERR)
    diag = jedi_lint.pyls_lint(doc)[0]

    assert diag['message'] == 'SyntaxError: invalid syntax'
    assert diag['range']['start'] == {'line': 0, 'character': 11}
    assert diag['range']['end'] == {'line': 1, 'character': 0}
    assert diag['severity'] == lsp.DiagnosticSeverity.Error


def test_indent_error_jedi(workspace):
    doc = Document(DOC_URI, workspace, DOC_INDENT_ERR)
    diag = jedi_lint.pyls_lint(doc)[0]

    assert diag['message'] == "IndentationError: unindent does not match \
any outer indentation level"
    assert diag['range']['start'] == {'line': 2, 'character': 0}
    assert diag['range']['end'] == {'line': 2, 'character': 2}
    assert diag['severity'] == lsp.DiagnosticSeverity.Error


def test_encoding_jedi(workspace):
    doc = Document(DOC_URI, workspace, DOC_ENCODING)
    diags = jedi_lint.pyls_lint(doc)

    assert len(diags) == 0
