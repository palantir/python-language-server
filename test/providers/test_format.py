# Copyright 2017 Palantir Technologies, Inc.
from pyls.providers.format import YapfFormatter

DOC_URI = __file__
DOC = """A = [
    'h',   'w',

    'a'
      ]

B = ['h',


'w']
"""

GOOD_DOC = """A = ['hello', 'world']\n"""


def test_format(workspace):
    workspace.put_document(DOC_URI, DOC)
    provider = YapfFormatter(workspace)

    res = provider.run(DOC_URI)

    assert len(res) == 1
    assert res[0]['newText'] == "A = ['h', 'w', 'a']\n\nB = ['h', 'w']\n"


def test_range_format(workspace):
    workspace.put_document(DOC_URI, DOC)
    provider = YapfFormatter(workspace)

    range = {
        'start': {'line': 0, 'character': 0},
        'end': {'line': 4, 'character': 10}
    }

    res = provider.run(DOC_URI, range)

    assert len(res) == 1

    # Make sure B is still badly formatted
    assert res[0]['newText'] == "A = ['h', 'w', 'a']\n\nB = ['h',\n\n\n'w']\n"


def test_no_change(workspace):
    workspace.put_document(DOC_URI, GOOD_DOC)
    provider = YapfFormatter(workspace)

    assert len(provider.run(DOC_URI)) == 0
