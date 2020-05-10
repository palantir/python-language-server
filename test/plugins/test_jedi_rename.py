# Copyright 2020 Palantir Technologies, Inc.
import os
import sys

from test.test_utils import MockWorkspace

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


@pytest.fixture
def tmp_workspace(workspace):
    def create_file(name, content):
        fn = os.path.join(workspace.root_path, name)
        with open(fn, 'w') as f:
            f.write(content)
        workspace.put_document(uris.from_fs_path(fn), content)

    create_file(DOC_NAME, DOC)
    return workspace


@pytest.mark.skipif(LT_PY36, reason='Jedi refactoring isnt supported on Python 2.x/3.5')
def test_jedi_rename(tmp_workspace, config):  # pylint: disable=redefined-outer-name
    position = {'line': 0, 'character': 6}
    DOC_URI = uris.from_fs_path(os.path.join(tmp_workspace.root_path, DOC_NAME))
    doc = Document(DOC_URI, MockWorkspace())

    result = pyls_rename(config, tmp_workspace, doc, position, 'ShouldBeRenamed')
    assert len(result.keys()) == 1

    changes = result.get('documentChanges')
    assert len(changes) == 1
    changes = changes[0]

    assert changes.get('edits') == [
        {
            'range': {
                'start': {'line': 0, 'character': 0},
                'end': {'line': 5, 'character': 0},
            },
            'newText': 'class ShouldBeRenamed():\n    pass\n\nclass Test2(ShouldBeRenamed):\n    pass\n',
        }
    ]
