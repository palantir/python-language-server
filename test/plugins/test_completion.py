# Copyright 2017 Palantir Technologies, Inc.
from pyls import uris
from pyls.plugins.completion import pyls_completions
from pyls.workspace import Document

DOC_URI = uris.from_fs_path(__file__)
DOC = """import sys
print sys.stdin.read()

def hello():
    pass

def _a_hello():
    pass

"""


def test_completion():
    # Over 'r' in sys.stdin.read()
    com_position = {'line': 1, 'character': 17}
    doc = Document(DOC_URI, DOC)
    items = pyls_completions(doc, com_position)

    assert len(items) > 0
    assert items[0]['label'] == 'read'


def test_completion_ordering():
    # Over the blank line
    com_position = {'line': 8, 'character': 0}
    doc = Document(DOC_URI, DOC)
    completions = pyls_completions(doc, com_position)

    items = {c['label']: c['sortText'] for c in completions}

    # Assert that builtins come after our own functions even if alphabetically they're before
    assert items['hello'] < items['dict']
    # And that 'hidden' functions come after unhidden ones
    assert items['hello'] < items['_a_hello']
