# Copyright 2019 Palantir Technologies, Inc.
import tempfile
import os
from pyls import lsp, uris
from pyls.plugins import importmagic_lint
from pyls.workspace import Document

DOC_URI = uris.from_fs_path(__file__)
DOC = """
files = listdir()
print(files)
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

        assert unres_symbol['message'] == "Unresolved import 'listdir'"
        assert unres_symbol['range']['start'] == {'line': 1, 'character': 8}
        assert unres_symbol['range']['end'] == {'line': 1, 'character': 15}
        assert unres_symbol['severity'] == lsp.DiagnosticSeverity.Hint

    finally:
        os.remove(name)


def test_importmagic_actions(config):
    context = {
        'diagnostics': [
            {
                'range':
                {
                    'start': {'line': 1, 'character': 8},
                    'end': {'line': 1, 'character': 15}
                },
                'message': "Unresolved import 'listdir'",
                'severity': 4,
                'source': 'importmagic'
            }
        ]
    }

    try:
        name, doc = temp_document(DOC)
        actions = importmagic_lint.pyls_code_actions(config, doc, context)
        action = [a for a in actions if a['title'] == 'Import "listdir" from "os"'][0]
        arguments = action['arguments']

        assert action['command'] == 'importmagic.addimport'
        assert arguments['startLine'] == 1
        assert arguments['endLine'] == 1
        assert arguments['newText'] == 'from os import listdir\n\n\n'

    finally:
        os.remove(name)