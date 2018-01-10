# Copyright 2017 Palantir Technologies, Inc.
import pytest
from pyls import dispatcher


class TestDispatcher(dispatcher.JSONRPCMethodDispatcher):

    def m_test__method(self, **params):
        return params


def test_method_dispatcher():
    td = TestDispatcher()
    params = {'hello': 'world'}
    assert td['test/method'](**params) == params


def test_method_dispatcher_missing_method():
    td = TestDispatcher()
    with pytest.raises(KeyError):
        td['test/noMethod']('hello')
