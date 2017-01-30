# Copyright 2017 Palantir Technologies, Inc.
from pyls.providers.hover import JediDocStringHoverProvider

DOC_URI = __file__
DOC = """

def main():
    \"\"\"hello world\"\"\"
    pass
"""


def test_hover(workspace):
    # Over 'main' in def main():
    hov_position = {'line': 2, 'character': 6}
    # Over the blank second line
    no_hov_position = {'line': 1, 'character': 0}

    workspace.put_document(DOC_URI, DOC)
    provider = JediDocStringHoverProvider(workspace)

    assert {
        'contents': 'main()\n\nhello world'
    } == provider.run(DOC_URI, hov_position)

    assert {'contents': ''} == provider.run(DOC_URI, no_hov_position)
