# Copyright 2017 Palantir Technologies, Inc.
import os
import sys
from pyls import uris
from pyls.workspace import Document
import os.path as osp
from rope.base import libutils
from rope.base.project import Project
from pyls.workspace import Document, get_preferred_submodules
from pyls.plugins.jedi_completion import pyls_completions as pyls_jedi_completions
from pyls.plugins.rope_completion import pyls_completions as pyls_rope_completions

LOCATION = osp.realpath(osp.join(os.getcwd(),
                                 osp.dirname(__file__)))

DOC_URI = uris.from_fs_path(__file__)
DOC = """import sys
print sys.stdin.read()

def hello():
    pass

def _a_hello():
    pass

"""


def test_rope_import_completion():
    com_position = {'line': 0, 'character': 7}
    doc = Document(DOC_URI, DOC)
    items = pyls_rope_completions(doc, com_position)
    assert items is None


def test_jedi_completion():
    # Over 'r' in sys.stdin.read()
    com_position = {'line': 1, 'character': 17}
    doc = Document(DOC_URI, DOC)
    items = pyls_jedi_completions(doc, com_position)

    assert len(items) > 0
    if (sys.version_info > (3, 0)):
        assert items[0]['label'] == 'read(args)'
    else:
        assert items[0]['label'] == 'read()'


def test_rope_completion():
    # Over 'r' in sys.stdin.read()
    com_position = {'line': 1, 'character': 17}
    rope = Project(LOCATION)
    rope.prefs.set('extension_modules', get_preferred_submodules())
    doc = Document(DOC_URI, DOC, rope=rope)
    items = pyls_rope_completions(doc, com_position)

    assert len(items) > 0
    assert items[0]['label'] == 'read'


def test_jedi_completion_ordering():
    # Over the blank line
    com_position = {'line': 8, 'character': 0}
    doc = Document(DOC_URI, DOC)
    completions = pyls_jedi_completions(doc, com_position)

    items = {c['label']: c['sortText'] for c in completions}

    # Assert that builtins come after our own functions even if alphabetically they're before
    assert items['hello()'] < items['dict']
    # And that 'hidden' functions come after unhidden ones
    assert items['hello()'] < items['_a_hello()']
