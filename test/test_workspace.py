# Copyright 2017 Palantir Technologies, Inc.
import os
import pytest
from pyls import workspace

DOC_URI = 'file://' + __file__


def test_local(pyls):
    """ Since the workspace points to the test directory """
    assert pyls.workspace.is_local()


def test_put_document(pyls):
    pyls.workspace.put_document(DOC_URI, 'content')
    assert DOC_URI in pyls.workspace._docs


def test_get_document(pyls):
    pyls.workspace.put_document(DOC_URI, 'TEXT')
    assert pyls.workspace.get_document(DOC_URI).source == 'TEXT'


def test_rm_document(pyls):
    pyls.workspace.put_document(DOC_URI, 'TEXT')
    assert pyls.workspace.get_document(DOC_URI).source == 'TEXT'
    pyls.workspace.rm_document(DOC_URI)
    with pytest.raises(KeyError):
        pyls.workspace.get_document(DOC_URI)


def test_bad_get_document(pyls):
    with pytest.raises(KeyError):
        pyls.workspace.get_document("BAD_URI")


def test_uri_like():
    assert workspace.get_uri_like('file:///some-path', '/my/path') == 'file:///my/path'
    win_doc_uri = r'file:///D:/hello%20world.py'
    win_doc_path = r'D:\hello world.py'
    win_uri = workspace.get_uri_like(win_doc_uri, win_doc_path)
    assert win_uri == win_doc_uri


def test_non_root_project(pyls):
    repo_root = os.path.join(pyls.workspace.root, 'repo-root')
    os.mkdir(repo_root)
    project_root = os.path.join(repo_root, 'project-root')
    os.mkdir(project_root)

    with open(os.path.join(project_root, 'setup.py'), 'w+') as f:
        f.write('# setup.py')

    test_uri = 'file://' + os.path.join(project_root, 'hello/test.py')
    pyls.workspace.put_document(test_uri, 'assert True')
    test_doc = pyls.workspace.get_document(test_uri)
    assert project_root in pyls.workspace.syspath_for_path(test_doc.path)


def test_urlencoded_paths():
    root_uri = "file:///Encoded%20%3FSpace/"
    file_uri = root_uri + "test.py"

    ws = workspace.Workspace(root_uri)
    assert ws.root == "/Encoded ?Space/"

    ws.put_document(file_uri, "")
    doc = ws.get_document(file_uri)
    assert doc.path == '/Encoded ?Space/test.py'
