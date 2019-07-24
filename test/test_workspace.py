# Copyright 2017 Palantir Technologies, Inc.
import os
import os.path as osp
import sys
from pyls import uris

PY2 = sys.version_info.major == 2

if PY2:
    import pathlib2 as pathlib
else:
    import pathlib


DOC_URI = uris.from_fs_path(__file__)


def path_as_uri(path):
    return pathlib.Path(osp.abspath(path)).as_uri()


def test_local(pyls):
    """ Since the workspace points to the test directory """
    assert pyls.workspace.is_local()


def test_put_document(pyls):
    pyls.workspace.put_document(DOC_URI, 'content')
    assert DOC_URI in pyls.workspace._docs


def test_get_document(pyls):
    pyls.workspace.put_document(DOC_URI, 'TEXT')
    assert pyls.workspace.get_document(DOC_URI).source == 'TEXT'


def test_get_missing_document(tmpdir, pyls):
    source = 'TEXT'
    doc_path = tmpdir.join("test_document.py")
    doc_path.write(source)
    doc_uri = uris.from_fs_path(str(doc_path))
    assert pyls.workspace.get_document(doc_uri).source == 'TEXT'


def test_rm_document(pyls):
    pyls.workspace.put_document(DOC_URI, 'TEXT')
    assert pyls.workspace.get_document(DOC_URI).source == 'TEXT'
    pyls.workspace.rm_document(DOC_URI)
    assert pyls.workspace.get_document(DOC_URI)._source is None


def test_non_root_project(pyls):
    repo_root = os.path.join(pyls.workspace.root_path, 'repo-root')
    os.mkdir(repo_root)
    project_root = os.path.join(repo_root, 'project-root')
    os.mkdir(project_root)

    with open(os.path.join(project_root, 'setup.py'), 'w+') as f:
        f.write('# setup.py')

    test_uri = uris.from_fs_path(os.path.join(project_root, 'hello/test.py'))
    pyls.workspace.put_document(test_uri, 'assert True')
    test_doc = pyls.workspace.get_document(test_uri)
    assert project_root in test_doc.sys_path()


def test_multiple_workspaces(tmpdir, pyls):
    workspace1_dir = tmpdir.mkdir('workspace1')
    workspace2_dir = tmpdir.mkdir('workspace2')
    file1 = workspace1_dir.join('file1.py')
    file2 = workspace2_dir.join('file1.py')
    file1.write('import os')
    file2.write('import sys')

    msg = {
        'uri': path_as_uri(str(file1)),
        'version': 1,
        'text': 'import os'
    }

    pyls.m_text_document__did_open(textDocument=msg)
    assert msg['uri'] in pyls.workspace._docs

    added_workspaces = [{'uri': path_as_uri(str(x))}
                        for x in (workspace1_dir, workspace2_dir)]
    pyls.m_workspace__did_change_workspace_folders(
        added=added_workspaces, removed=[])

    for workspace in added_workspaces:
        assert workspace['uri'] in pyls.workspaces

    workspace1_uri = added_workspaces[0]['uri']
    assert msg['uri'] not in pyls.workspace._docs
    assert msg['uri'] in pyls.workspaces[workspace1_uri]._docs

    msg = {
        'uri': path_as_uri(str(file2)),
        'version': 1,
        'text': 'import sys'
    }
    pyls.m_text_document__did_open(textDocument=msg)

    workspace2_uri = added_workspaces[1]['uri']
    assert msg['uri'] in pyls.workspaces[workspace2_uri]._docs

    pyls.m_workspace__did_change_workspace_folders(
        added=[], removed=[added_workspaces[0]])
    assert workspace1_uri not in pyls.workspaces
