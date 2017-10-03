# Copyright 2017 Palantir Technologies, Inc.
from pyls import uris
from pyls.plugins.definition import pyls_definitions
from pyls.workspace import Document

DOC_URI = uris.from_fs_path(__file__)
DOC = """def a():
    pass

print a()
"""


def test_definitions():
    # Over 'a' in print a
    cursor_pos = {'line': 3, 'character': 6}

    # The definition of 'a'
    range = {
        'start': {'line': 0, 'character': 4},
        'end': {'line': 0, 'character': 5}
    }

    doc = Document(DOC_URI, DOC)
    assert [{'uri': DOC_URI, 'range': range}] == pyls_definitions(doc, cursor_pos)
