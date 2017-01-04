# Copyright 2017 Palantir Technologies, Inc.
import os
import shutil
import tempfile
from pyls.workspace import Workspace
from pyls.providers.lint import PyCodeStyleLinter, PyflakesLinter

DOC_URI = __file__
DOC = """import sys

def hello():
\tpass

import json
"""

DOC_SYNTAX_ERR = """def hello()
    pass
"""


def test_pycodestyle(workspace):
    workspace.put_document(DOC_URI, DOC)
    provider = PyCodeStyleLinter(workspace)

    diags = provider.run(DOC_URI)

    assert all([d['source'] == 'pycodestyle' for d in diags])

    # One we're expecting is:
    msg = 'E402 module level import not at top of file'
    mod_import = filter(lambda d: d['message'] == msg, diags)[0]

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

    provider = PyCodeStyleLinter(workspace)
    workspace.put_document(doc_uri, DOC)

    # Make sure we get a warning for 'indentation contains tabs'
    diags = provider.run(doc_uri)
    assert len(filter(lambda d: d['code'] == 'W191', diags)) > 0

    content = {
        'setup.cfg': ('[pycodestyle]\nignore = W191', True),
        'pep8.cfg': ('[pep8]\nignore = W191', True),
        'tox.ini': ('', False)
    }

    for conf_file, (content, working) in content.items():
        # Now we'll add config file to ignore it
        with open(os.path.join(tmp, conf_file), 'w+') as f:
            f.write(content)

        # And make sure we don't get any warnings
        diags = provider.run(doc_uri)
        assert len(filter(lambda d: d['code'] == 'W191', diags)) == 0 if working else 1

        os.unlink(os.path.join(tmp, conf_file))

    shutil.rmtree(tmp)


def test_pyflakes(workspace):
    workspace.put_document(DOC_URI, DOC)
    provider = PyflakesLinter(workspace)

    diags = provider.run(DOC_URI)

    # One we're expecting is:
    msg = '\'sys\' imported but unused'
    unused_import = filter(lambda d: d['message'] == msg, diags)[0]

    assert unused_import['range']['start'] == {'line': 0, 'character': 0}


def test_syntax_error_pyflakes(workspace):
    workspace.put_document(DOC_URI, DOC_SYNTAX_ERR)
    provider = PyflakesLinter(workspace)

    diag = provider.run(DOC_URI)[0]

    assert diag['message'] == 'invalid syntax'
    assert diag['range']['start'] == {'line': 0, 'character': 12}
