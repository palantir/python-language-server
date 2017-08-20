# Copyright 2017 Palantir Technologies, Inc.
import pytest
from pyls import uris
from test import windows_only


@pytest.mark.parametrize('uri,path', [
    ('file:///foo/bar#frag', '/foo/bar'),
    ('file:/foo/bar#frag', '/foo/bar'),
])
def test_fs_path(uri, path):
    assert uris.fs_path(uri) == path


@windows_only
@pytest.mark.parametrize('uri,path', [
    ('file://shares/c$/far/boo', '\\\\shares\\c$\\far\\boo'),
    ('file:///c:/far/boo', 'c:\\far\\boo'),
    ('file:///C:/far/boo', 'c:\\far\\boo'),
])
def test_win_fs_path(uri, path):
    assert uris.fs_path(uri) == path
