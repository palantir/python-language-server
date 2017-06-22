# Copyright 2017 Palantir Technologies, Inc.
import os
import pytest
import shutil
import tempfile
from pyls.workspace import Document, Workspace
from pyls.plugins.references import pyls_references


DOC1_NAME = 'test1.py'
DOC2_NAME = 'test2.py'

DOC1 = """class Test1():
    pass
"""

DOC2 = """from test1 import Test1

Test1()
"""


@pytest.fixture
def tmp_workspace():
    tmp = tempfile.mkdtemp()
    workspace = Workspace(tmp)

    def create_file(name, content):
        fn = os.path.join(tmp, name)
        with open(fn, 'w') as f:
            f.write(content)
        workspace.put_document('file://' + fn, content)

    create_file(DOC1_NAME, DOC1)
    create_file(DOC2_NAME, DOC2)

    yield workspace
    shutil.rmtree(tmp)


def test_references(tmp_workspace):
    # Over 'Test1' in class Test1():
    position = {'line': 0, 'character': 8}
    DOC1_URI = 'file://' + os.path.join(tmp_workspace.root, DOC1_NAME)
    doc1 = Document(DOC1_URI)

    refs = pyls_references(doc1, position)

    # Definition, the import and the instantiation
    assert len(refs) == 3

    # Briefly check excluding the definitions (also excludes imports, only counts uses)
    no_def_refs = pyls_references(doc1, position, exclude_declaration=True)
    assert len(no_def_refs) == 1

    # Make sure our definition is correctly located
    doc1_ref = [u for u in refs if u['uri'] == DOC1_URI][0]
    assert doc1_ref['range']['start'] == {'line': 0, 'character': 6}
    assert doc1_ref['range']['end'] == {'line': 0, 'character': 11}

    # Make sure our import is correctly located
    doc2_import_ref = [u for u in refs if u['uri'] != DOC1_URI][0]
    assert doc2_import_ref['range']['start'] == {'line': 0, 'character': 18}
    assert doc2_import_ref['range']['end'] == {'line': 0, 'character': 23}

    doc2_usage_ref = [u for u in refs if u['uri'] != DOC1_URI][1]
    assert doc2_usage_ref['range']['start'] == {'line': 2, 'character': 0}
    assert doc2_usage_ref['range']['end'] == {'line': 2, 'character': 5}
