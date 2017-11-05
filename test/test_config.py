# Copyright 2017 Palantir Technologies, Inc.
from pyls._utils import find_parents
from pyls.config._utils import merge_dicts


def test_merge_dicts():
    assert merge_dicts(
        {'a': True, 'b': {'x': 123, 'y': {'hello': 'world'}}},
        {'a': False, 'b': {'y': [], 'z': 987}}
    ) == {'a': False, 'b': {'x': 123, 'y': [], 'z': 987}}
