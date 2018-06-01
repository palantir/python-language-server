# Copyright 2017 Palantir Technologies, Inc.
import os

from pyls import uris
from pyls.workspace import Document
from pyls.plugins.jedi_completion import pyls_completions as pyls_jedi_completions
from pyls.plugins.rope_completion import pyls_completions as pyls_rope_completions

LOCATION = os.path.realpath(
    os.path.join(os.getcwd(), os.path.dirname(__file__))
)

DOC_URI = uris.from_fs_path(__file__)
DOC = """import os
print os.path.isabs("/tmp")

def hello():
    pass

def _a_hello():
    pass

"""


def test_rope_import_completion(config, workspace):
    com_position = {'line': 0, 'character': 7}
    doc = Document(DOC_URI, DOC)
    items = pyls_rope_completions(config, workspace, doc, com_position)
    assert items is None


def test_jedi_completion():
    # Over 'i' in os.path.isabs(...)
    com_position = {'line': 1, 'character': 15}
    doc = Document(DOC_URI, DOC)
    items = pyls_jedi_completions(doc, com_position)

    assert items
    assert items[0]['label'] == 'isabs(s)'

    # Test we don't throw with big character
    pyls_jedi_completions(doc, {'line': 1, 'character': 1000})


def test_rope_completion(config, workspace):
    # Over 'i' in os.path.isabs(...)
    com_position = {'line': 1, 'character': 15}
    workspace.put_document(DOC_URI, source=DOC)
    doc = workspace.get_document(DOC_URI)
    items = pyls_rope_completions(config, workspace, doc, com_position)

    assert items
    assert items[0]['label'] == 'isabs'


def test_jedi_completion_ordering():
    # Over the blank line
    com_position = {'line': 8, 'character': 0}
    doc = Document(DOC_URI, DOC)
    completions = pyls_jedi_completions(doc, com_position)

    items = {c['label']: c['sortText'] for c in completions}

    # And that 'hidden' functions come after unhidden ones
    assert items['hello()'] < items['_a_hello()']
