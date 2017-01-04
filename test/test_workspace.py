# Copyright 2017 Palantir Technologies, Inc.
import pytest

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
    with pytest.raises(ValueError):
        pyls.workspace.get_document("BAD_URI")


def test_uri_like(pyls):
    assert pyls.workspace.get_uri_like('file:///some-path', '/my/path') == 'file:///my/path'
