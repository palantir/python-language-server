# Copyright 2017 Palantir Technologies, Inc.
import os
import shutil
import tempfile
from pyls.config import Config
from pyls.workspace import Document, Workspace
from pyls.plugins import pycodestyle_lint, pyflakes_lint

DOC_URI = __file__
DOC = """import sys

def hello():
\tpass

import json
"""

DOC_SYNTAX_ERR = """def hello()
    pass
"""


def test_pycodestyle(config, workspace):
    doc = Document(DOC_URI, DOC)
    diags = pycodestyle_lint.pyls_lint(config, workspace, doc)

    assert all([d['source'] == 'pycodestyle' for d in diags])

    # One we're expecting is:
    msg = 'E402 module level import not at top of file'
    mod_import = [d for d in diags if d['message'] == msg][0]

    assert mod_import['code'] == 'E402'
    assert mod_import['range']['start'] == {'line': 5, 'character': 0}


def test_pycodestyle_config():
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
    # Create a workspace in tmp
    tmp = tempfile.mkdtemp()
    workspace = Workspace(tmp)
    doc_uri = 'file://' + tmp + '/' + 'test.py'
    workspace.put_document(doc_uri, DOC)
    doc = workspace.get_document(doc_uri)
    config = Config(workspace.root, {})

    # Make sure we get a warning for 'indentation contains tabs'
    diags = pycodestyle_lint.pyls_lint(config, workspace, doc)
    assert [d for d in diags if d['code'] == 'W191']

    content = {
        'setup.cfg': ('[pycodestyle]\nignore = W191', True),
        'pep8.cfg': ('[pep8]\nignore = W191', True),
        'tox.ini': ('', False)
    }

    for conf_file, (content, working) in list(content.items()):
        # Now we'll add config file to ignore it
        with open(os.path.join(tmp, conf_file), 'w+') as f:
            f.write(content)

        # And make sure we don't get any warnings
        diags = pycodestyle_lint.pyls_lint(config, workspace, doc)
        assert len([d for d in diags if d['code'] == 'W191']) == 0 if working else 1

        os.unlink(os.path.join(tmp, conf_file))

    shutil.rmtree(tmp)


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
