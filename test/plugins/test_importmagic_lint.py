# Copyright 2019 Palantir Technologies, Inc.
import tempfile
import os
from time import sleep
from pyls import lsp, uris
from pyls.plugins import importmagic_lint
from pyls.workspace import Document

DOC_URI = uris.from_fs_path(__file__)

DOC_LINT = """
import os
time.sleep(10)
t = 5

def useless_func():
    pass
"""

DOC_ADD = """
time.sleep(10)
print("test")
"""

DOC_REMOVE = """
import time
print("useless import")
"""

LINT_DIAGS = {
    "Unresolved import 'time.sleep'": {
        'range': {'start': {'line': 2, 'character': 0}, 'end': {'line': 2, 'character': 10}},
        'severity': lsp.DiagnosticSeverity.Hint,
    },
    "Unreferenced variable/function 'useless_func'": {
        'range': {'start': {'line': 5, 'character': 4}, 'end': {'line': 5, 'character': 16}},
        'severity': lsp.DiagnosticSeverity.Warning,
    },
    "Unreferenced variable/function 't'": {
        'range': {'start': {'line': 3, 'character': 0}, 'end': {'line': 3, 'character': 1}},
        'severity': lsp.DiagnosticSeverity.Warning,
    },
    "Unreferenced import 'os'": {
        'range': {'start': {'line': 1, 'character': 7}, 'end': {'line': 1, 'character': 9}},
        'severity': lsp.DiagnosticSeverity.Warning,
    },
}


def temp_document(doc_text):
    temp_file = tempfile.NamedTemporaryFile(mode='w', delete=False)
    name = temp_file.name
    temp_file.write(doc_text)
    temp_file.close()
    doc = Document(uris.from_fs_path(name))

    return name, doc


def test_importmagic_lint():
    try:
        name, doc = temp_document(DOC_LINT)
        diags = importmagic_lint.pyls_lint(doc)
        importmagic_diags = [d for d in diags if d['source'] == 'importmagic']
        assert len(importmagic_diags) == len(LINT_DIAGS)

        for diag in importmagic_diags:
            expected_diag = LINT_DIAGS.get(diag['message'])
            assert expected_diag is not None, "Didn't expect diagnostic with message '{}'".format(diag['message'])
            assert expected_diag['range'] == diag['range']
            assert expected_diag['severity'] == diag['severity']

    finally:
        os.remove(name)


def test_importmagic_add_import_action(config):
    try:
        importmagic_lint.pyls_initialize()
        name, doc = temp_document(DOC_ADD)
        while importmagic_lint._index_cache.get('default') is None:
            # wait for the index to be ready
            sleep(1)
        actions = importmagic_lint.pyls_code_actions(config, doc)
        action = [a for a in actions if a['title'] == 'Import "time"'][0]
        arguments = action['arguments'][0]

        assert action['command'] == importmagic_lint.ADD_IMPORT_COMMAND
        assert arguments['startLine'] == 1
        assert arguments['endLine'] == 1
        assert arguments['newText'] == 'import time\n\n\n'

    finally:
        os.remove(name)


def test_importmagic_remove_import_action(config):
    try:
        importmagic_lint.pyls_initialize()
        name, doc = temp_document(DOC_REMOVE)
        while importmagic_lint._index_cache.get('default') is None:
            # wait for the index to be ready
            sleep(1)
        actions = importmagic_lint.pyls_code_actions(config, doc)
        action = [a for a in actions if a['title'] == 'Remove unused import "time"'][0]
        arguments = action['arguments'][0]

        assert action['command'] == importmagic_lint.REMOVE_IMPORT_COMMAND
        assert arguments['startLine'] == 1
        assert arguments['endLine'] == 2
        assert arguments['newText'] == ''

    finally:
        os.remove(name)
