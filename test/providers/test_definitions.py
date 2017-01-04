# Copyright 2017 Palantir Technologies, Inc.
from pyls.providers.definition import JediDefinitionsProvider

DOC_URI = __file__
DOC = """def a():
    pass

print a()
"""


def test_definitions(workspace):
    # Over 'a' in print a
    cursor_pos = {'line': 3, 'character': 6}

    # The definition of 'a'
    range = {
        'start': {'line': 0, 'character': 4},
        'end': {'line': 0, 'character': 5}
    }

    workspace.put_document(DOC_URI, DOC)
    provider = JediDefinitionsProvider(workspace)

    assert [{'uri': DOC_URI, 'range': range}] == provider.run(DOC_URI, cursor_pos)
