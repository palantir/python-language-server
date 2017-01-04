# Copyright 2017 Palantir Technologies, Inc.
from pyls.providers.completion import JediCompletionProvider

DOC_URI = __file__
DOC = """import sys
print sys.stdin.read()

def hello():
    pass

def _a_hello():
    pass

"""


def test_completion(workspace):
    # Over 'r' in sys.stdin.read()
    com_position = {'line': 1, 'character': 17}

    workspace.put_document(DOC_URI, DOC)
    provider = JediCompletionProvider(workspace)

    items = provider.run(DOC_URI, com_position)['items']

    assert len(items) > 0
    assert items[0]['label'] == 'read'


def test_completion_ordering(workspace):
    # Over the blank line
    com_position = {'line': 8, 'character': 0}

    workspace.put_document(DOC_URI, DOC)
    provider = JediCompletionProvider(workspace)

    completions = provider.run(DOC_URI, com_position)['items']

    items = {c['label']: c['sortText'] for c in completions}

    # Assert that builtins come after our own functions even if alphabetically they're before
    assert items['hello'] < items['assert']
    # And that 'hidden' functions come after unhidden ones
    assert items['hello'] < items['_a_hello']
