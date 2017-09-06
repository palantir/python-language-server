# Copyright 2017 Palantir Technologies, Inc.
import os
from pyls import lsp, uris
from pyls.config import Config
from pyls.workspace import Document
from pyls.plugins import mccabe_lint, pycodestyle_lint, pydocstyle_lint, pyflakes_lint

DOC_URI = uris.from_fs_path(__file__)
DOC = """import sys

def hello():
\tpass

import json
"""

DOC_SYNTAX_ERR = """def hello()
    pass
"""


def test_mccabe(config):
    old_settings = config.settings
    try:
        config.update({'plugins': {'mccabe': {'threshold': 1}}})
        doc = Document(DOC_URI, DOC)
        diags = mccabe_lint.pyls_lint(config, doc)

        assert all([d['source'] == 'mccabe' for d in diags])

        # One we're expecting is:
        msg = 'Cyclomatic complexity too high: 1 (threshold 1)'
        mod_import = [d for d in diags if d['message'] == msg][0]

        assert mod_import['severity'] == lsp.DiagnosticSeverity.Warning
        assert mod_import['range']['start'] == {'line': 3, 'character': 0}
        assert mod_import['range']['end'] == {'line': 3, 'character': 6}
    finally:
        config._settings = old_settings


def test_pycodestyle(config):
    doc = Document(DOC_URI, DOC)
    diags = pycodestyle_lint.pyls_lint(config, doc)

    assert all([d['source'] == 'pycodestyle' for d in diags])

    # One we're expecting is:
    msg = 'W191 indentation contains tabs'
    mod_import = [d for d in diags if d['message'] == msg][0]

    assert mod_import['code'] == 'W191'
    assert mod_import['severity'] == lsp.DiagnosticSeverity.Warning
    assert mod_import['range']['start'] == {'line': 3, 'character': 0}
    assert mod_import['range']['end'] == {'line': 3, 'character': 6}


def test_pycodestyle_config(workspace):
    """ Test that we load config files properly.

    Config files are loaded in the following order:
        tox.ini pep8.cfg setup.cfg pycodestyle.cfg

    Each overriding the values in the last.

    These files are first looked for in the current document's
    directory and then each parent directory until any one is found
    terminating at the workspace root.

    If any section called 'pycodestyle' exists that will be solely used
    and any config in a 'pep8' section will be ignored
    """
    doc_uri = uris.from_fs_path(os.path.join(workspace.root_path, 'test.py'))
    workspace.put_document(doc_uri, DOC)
    doc = workspace.get_document(doc_uri)
    config = Config(workspace.root_uri, {})

    # Make sure we get a warning for 'indentation contains tabs'
    diags = pycodestyle_lint.pyls_lint(config, doc)
    assert [d for d in diags if d['code'] == 'W191']

    content = {
        'setup.cfg': ('[pycodestyle]\nignore = W191', True),
        'pep8.cfg': ('[pep8]\nignore = W191', True),
        'tox.ini': ('', False)
    }

    for conf_file, (content, working) in list(content.items()):
        # Now we'll add config file to ignore it
        with open(os.path.join(workspace.root_path, conf_file), 'w+') as f:
            f.write(content)

        # And make sure we don't get any warnings
        diags = pycodestyle_lint.pyls_lint(config, doc)
        assert len([d for d in diags if d['code'] == 'W191']) == 0 if working else 1

        os.unlink(os.path.join(workspace.root_path, conf_file))


def test_pydocstyle():
    doc = Document(DOC_URI, DOC)
    diags = pydocstyle_lint.pyls_lint(doc)

    assert all([d['source'] == 'pydocstyle' for d in diags])

    # One we're expecting is:
    msg = 'D100: Missing docstring in public module'
    unused_import = [d for d in diags if d['message'] == msg][0]

    assert unused_import['range']['start'] == {'line': 0, 'character': 0}


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
