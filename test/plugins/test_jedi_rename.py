# Copyright 2020 Palantir Technologies, Inc.
import os
import sys

import pytest
from pyls import uris
from pyls.plugins.jedi_rename import pyls_rename
from pyls.workspace import Document

LT_PY36 = sys.version_info.major < 3 or (sys.version_info.major == 3 and sys.version_info.minor < 6)

DOC_NAME = 'test1.py'
DOC = '''class Test1():
    pass

class Test2(Test1):
    pass
'''

DOC_NAME_EXTRA = 'test2.py'
DOC_EXTRA = '''from test1 import Test1
x = Test1()
'''


@pytest.fixture
def tmp_workspace(temp_workspace_factory):
    return temp_workspace_factory({
        DOC_NAME: DOC,
        DOC_NAME_EXTRA: DOC_EXTRA
    })


@pytest.mark.skipif(LT_PY36, reason='Jedi refactoring isnt supported on Python 2.x/3.5')
def test_jedi_rename(tmp_workspace, config):  # pylint: disable=redefined-outer-name
    # rename the `Test1` class
    position = {'line': 0, 'character': 6}
    DOC_URI = uris.from_fs_path(os.path.join(tmp_workspace.root_path, DOC_NAME))
    doc = Document(DOC_URI, tmp_workspace)

    result = pyls_rename(config, tmp_workspace, doc, position, 'ShouldBeRenamed')
    assert len(result.keys()) == 1

    changes = result.get('documentChanges')
    assert len(changes) == 2

    assert changes[0]['textDocument']['uri'] == doc.uri
    assert changes[0]['textDocument']['version'] == doc.version
    assert changes[0].get('edits') == [
        {
            'range': {
                'start': {'line': 0, 'character': 0},
                'end': {'line': 5, 'character': 0},
            },
            'newText': 'class ShouldBeRenamed():\n    pass\n\nclass Test2(ShouldBeRenamed):\n    pass\n',
        }
    ]
    path = os.path.join(tmp_workspace.root_path, DOC_NAME_EXTRA)
    uri_extra = uris.from_fs_path(path)
    assert changes[1]['textDocument']['uri'] == uri_extra
    # This also checks whether documents not yet added via textDocument/didOpen
    # but that do need to be renamed in the project have a `null` version
    # number.
    assert changes[1]['textDocument']['version'] is None
    assert changes[1].get('edits') == [
        {
            'range': {
                'start': {'line': 0, 'character': 0},
                'end': {'line': 2, 'character': 0}},
            'newText': 'from test1 import ShouldBeRenamed\nx = ShouldBeRenamed()\n'
        }
    ]
