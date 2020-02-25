# Copyright 2018 Google LLC.
import contextlib
import os
import tempfile

from pyls import lsp, uris
from pyls.workspace import Document
from pyls.plugins import spark_cost_checker

DOC_URI = uris.from_fs_path(__file__)
DOC = """import sys

def hello():
\tpass

import json
"""

DOC_SYNTAX_ERR = """
df.collect()
"""


@contextlib.contextmanager
def temp_document(doc_text):
    try:
        temp_file = tempfile.NamedTemporaryFile(mode='w', delete=False)
        name = temp_file.name
        temp_file.write(doc_text)
        temp_file.close()
        yield Document(uris.from_fs_path(name))
    finally:
        os.remove(name)


def write_temp_doc(document, contents):
    with open(document.path, 'w') as temp_file:
        temp_file.write(contents)


def test_cost_checker(config):
    with temp_document(DOC) as doc:
        diags = spark_cost_checker.pyls_lint(config, doc, True)

        msg = '[unused-import] Unused import sys'
        unused_import = [d for d in diags if d['message'] == msg][0]

        assert unused_import['range']['start'] == {'line': 0, 'character': 0}
        assert unused_import['severity'] == lsp.DiagnosticSeverity.Warning


def test_lint_free_spark_checker(config):
    # Can't use temp_document because it might give us a file that doesn't
    # match pylint's naming requirements. We should be keeping this file clean
    # though, so it works for a test of an empty lint.
    assert not spark_cost_checker.pyls_lint(
        config, Document(uris.from_fs_path(__file__)), True)


def test_cost_lint_caching():
    # Pylint can only operate on files, not in-memory contents. We cache the
    # diagnostics after a run so we can continue displaying them until the file
    # is saved again.
    #
    # We use PylintLinter.lint directly here rather than pyls_lint so we can
    # pass --disable=invalid-name to pylint, since we want a temporary file but
    # need to ensure that pylint doesn't give us invalid-name when our temp
    # file has capital letters in its name.

    with temp_document(DOC) as doc:
        # Start with a file with errors.
        diags = spark_cost_checker.SparkCostChecker.lint(doc, True)
        assert diags

        # Fix lint errors and write the changes to disk. Run the linter in the
        # in-memory mode to check the cached diagnostic behavior.
        write_temp_doc(doc, '')
        assert spark_cost_checker.SparkCostChecker.lint(doc, False) == diags

        # Now check the on-disk behavior.
        assert not spark_cost_checker.SparkCostChecker.lint(doc, True)

        # Make sure the cache was properly cleared.
        assert not spark_cost_checker.SparkCostChecker.lint(doc, False)


def test_cost_per_file_caching(config):
    # Ensure that diagnostics are cached per-file.
    with temp_document(DOC) as doc:
        assert spark_cost_checker.pyls_lint(config, doc, True)

    assert not pylint_lint.pyls_lint(
        config, Document(uris.from_fs_path(__file__)), False)
