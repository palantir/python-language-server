# Copyright 2017 Palantir Technologies, Inc.
from pyls.providers.hover import JediDocStringHoverProvider

DOC_URI = __file__
DOC = """import sys

def main():
    print sys.stdin.read()
    raise Exception()
"""


def test_hover(workspace):
    # Over 'Exception' in raise Exception()
    hov_position = {'line': 4, 'character': 17}
    # Over the blank second line
    no_hov_position = {'line': 1, 'character': 0}

    workspace.put_document(DOC_URI, DOC)
    provider = JediDocStringHoverProvider(workspace)

    assert {
        'contents': 'Common base class for all non-exit exceptions.'
    } == provider.run(DOC_URI, hov_position)

    assert {'contents': ''} == provider.run(DOC_URI, no_hov_position)
