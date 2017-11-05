# Copyright 2017 Palantir Technologies, Inc.
import time
from pyls import _utils


def test_debounce():
    interval = 0.1

    @_utils.debounce(0.1)
    def call_m():
        call_m._count += 1

    call_m._count = 0

    call_m()
    call_m()
    call_m()
    assert call_m._count == 0

    time.sleep(interval * 2)
    call_m()
    assert call_m._count == 1

    time.sleep(interval * 2)
    call_m()
    assert call_m._count == 2


def test_list_to_string():
    assert _utils.list_to_string("string") == "string"
    assert _utils.list_to_string(["a", "r", "r", "a", "y"]) == "a,r,r,a,y"


def test_camel_to_underscore():
    assert _utils.camel_to_underscore("camelCase") == "camel_case"
    assert _utils.camel_to_underscore("under_score") == "under_score"


def test_find_parents(tmpdir):
    subsubdir = tmpdir.ensure_dir("subdir", "subsubdir")
    path = subsubdir.ensure("path.py")
    test_cfg = tmpdir.ensure("test.cfg")

    assert _utils.find_parents(tmpdir.strpath, path.strpath, ["test.cfg"]) == [test_cfg.strpath]

