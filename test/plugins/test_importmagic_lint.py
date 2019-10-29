# Copyright 2019 Palantir Technologies, Inc.
import tempfile
import os
from pyls import lsp, uris
from pyls.plugins import importmagic_lint
from pyls.workspace import Document

DOC_URI = uris.from_fs_path(__file__)
DOC = """
time.sleep(10)
print("test")
"""


def temp_document(doc_text):
    temp_file = tempfile.NamedTemporaryFile(mode='w', delete=False)
    name = temp_file.name
    temp_file.write(doc_text)
    temp_file.close()
    doc = Document(uris.from_fs_path(name))

    return name, doc


def test_importmagic_lint():
    try:
        name, doc = temp_document(DOC)
        diags = importmagic_lint.pyls_lint(doc)
        unres_symbol = [d for d in diags if d['source'] == 'importmagic'][0]

        assert unres_symbol['message'] == "Unresolved import 'time.sleep'"
        assert unres_symbol['range']['start'] == {'line': 1, 'character': 0}
        assert unres_symbol['range']['end'] == {'line': 1, 'character': 10}
        assert unres_symbol['severity'] == lsp.DiagnosticSeverity.Hint

    finally:
        os.remove(name)


def test_importmagic_actions(config):
    context = {
        'diagnostics': [
            {
                'range':
                {
                    'start': {'line': 1, 'character': 0},
                    'end': {'line': 1, 'character': 10}
                },
                'message': "Unresolved import 'time.sleep'",
                'severity': lsp.DiagnosticSeverity.Hint,
                'source': importmagic_lint.SOURCE
            }
        ]
    }

    try:
        name, doc = temp_document(DOC)
        actions = importmagic_lint.pyls_code_actions(config, doc, context)
        action = [a for a in actions if a['title'] == 'Import "time"'][0]
        arguments = action['arguments'][0]

        assert action['command'] == importmagic_lint.ADD_IMPORT_COMMAND
        assert arguments['startLine'] == 1
        assert arguments['endLine'] == 1
        assert arguments['newText'] == 'import time\n\n\n'

    finally:
        os.remove(name)
