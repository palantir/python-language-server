# Copyright 2017 Palantir Technologies, Inc.
from test import unix_only, windows_only
import pytest
from pyls import uris


@unix_only
@pytest.mark.parametrize('uri,path', [
    ('file:///foo/bar#frag', '/foo/bar'),
    ('file:/foo/bar#frag', '/foo/bar'),
    ('file:/foo/space%20%3Fbar#frag', '/foo/space ?bar'),
])
def test_to_fs_path(uri, path):
    assert uris.to_fs_path(uri) == path


@unix_only
@pytest.mark.parametrize('uri,path', [
    # Monaco sends inmemory://name.py, where the name lands in the authority rather than
    # the path. Dropping the authority left these documents with no name at all.
    ('inmemory://dummy.py', '/dummy.py'),
    ('inmemory:///dummy.py', '/dummy.py'),
    ('vscode-notebook-cell://notebook/cell.py', '/notebook/cell.py'),
    ('untitled:Untitled-1', 'Untitled-1'),
])
def test_non_file_uri_to_fs_path(uri, path):
    assert uris.to_fs_path(uri) == path


@pytest.mark.parametrize('uri,is_file', [
    ('file:///foo/bar', True),
    ('/foo/bar', True),
    ('inmemory://dummy.py', False),
    ('untitled:Untitled-1', False),
    ('vscode-notebook-cell://notebook/cell.py', False),
    ('http://example.com/foo.py', False),
])
def test_is_file_uri(uri, is_file):
    assert uris.is_file_uri(uri) is is_file


@windows_only
@pytest.mark.parametrize('uri,path', [
    ('file:///c:/far/boo', 'c:\\far\\boo'),
    ('file:///C:/far/boo', 'c:\\far\\boo'),
    ('file:///C:/far/space%20%3Fboo', 'c:\\far\\space ?boo'),
])
def test_win_to_fs_path(uri, path):
    assert uris.to_fs_path(uri) == path


@unix_only
@pytest.mark.parametrize('path,uri', [
    ('/foo/bar', 'file:///foo/bar'),
    ('/foo/space ?bar', 'file:///foo/space%20%3Fbar'),
])
def test_from_fs_path(path, uri):
    assert uris.from_fs_path(path) == uri


@windows_only
@pytest.mark.parametrize('path,uri', [
    ('c:\\far\\boo', 'file:///c:/far/boo'),
    ('C:\\far\\space ?boo', 'file:///c:/far/space%20%3Fboo')
])
def test_win_from_fs_path(path, uri):
    assert uris.from_fs_path(path) == uri


@pytest.mark.parametrize('uri,kwargs,new_uri', [
    ('file:///foo/bar', {'path': '/baz/boo'}, 'file:///baz/boo'),
    ('file:///D:/hello%20world.py', {'path': 'D:/hello universe.py'}, 'file:///d:/hello%20universe.py')
])
def test_uri_with(uri, kwargs, new_uri):
    assert uris.uri_with(uri, **kwargs) == new_uri
