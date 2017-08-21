# Copyright 2017 Palantir Technologies, Inc.
from pyls.config import find_parents


def test_find_parents(tmpdir):
    # Create a workspace in tmp
    subsubdir = tmpdir.ensure_dir("subdir", "subsubdir")
    path = subsubdir.ensure("path.py")
    test_cfg = tmpdir.ensure("test.cfg")

    assert find_parents(tmpdir.strpath, path.strpath, ["test.cfg"]) == [test_cfg.strpath]
