# Copyright 2017 Palantir Technologies, Inc.
from pyls.config import find_parents, _merge_dicts


def test_find_parents(tmpdir):
    subsubdir = tmpdir.ensure_dir("subdir", "subsubdir")
    path = subsubdir.ensure("path.py")
    test_cfg = tmpdir.ensure("test.cfg")

    assert find_parents(tmpdir.strpath, path.strpath, ["test.cfg"]) == [test_cfg.strpath]


def test_merge_dicts():
    assert _merge_dicts(
        {'a': True, 'b': {'x': 123, 'y': {'hello': 'world'}}},
        {'a': False, 'b': {'y': [], 'z': 987}}
    ) == {'a': False, 'b': {'x': 123, 'y': [], 'z': 987}}
