# Copyright 2017 Palantir Technologies, Inc.
import pytest
from pyls.workspace import Document

DOC_URI = "file://" + __file__
DOC = """import sys

def main():
    print sys.stdin.read()
"""


@pytest.fixture
def doc():
    return Document(DOC_URI, DOC)


def test_document_props(doc):
    assert doc.uri == DOC_URI
    assert doc.path == __file__
    assert doc.source == DOC


def test_document_lines(doc):
    assert len(doc.lines) == 4
    assert doc.lines[0] == 'import sys\n'


def test_word_at_position(doc):
    """ Return the position under the cursor (or last in line if past the end) """
    # import sys
    assert doc.word_at_position({'line': 0, 'character': 8}) == 'sys'
    # Past end of import sys
    assert doc.word_at_position({'line': 0, 'character': 1000}) == 'sys'
    # Empty line
    assert doc.word_at_position({'line': 1, 'character': 5}) == ''
    # def main():
    assert doc.word_at_position({'line': 2, 'character': 0}) == 'def'
