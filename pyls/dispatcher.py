# Copyright 2018 Palantir Technologies, Inc.
import re

from .rpc_manager import MissingMethodException

_RE_FIRST_CAP = re.compile('(.)([A-Z][a-z]+)')
_RE_ALL_CAP = re.compile('([a-z0-9])([A-Z])')


class JSONRPCMethodDispatcher(object):
    """JSON RPC method dispatcher that calls methods on itself with params."""

    def __init__(self, delegate):
        self._delegate = delegate

    def __call__(self, method, params):
        method_name = "m_" + _method_to_string(method)
        if not hasattr(self._delegate, method_name):
            raise MissingMethodException(method_name)

        return getattr(self._delegate, method_name)(**params)


def _method_to_string(method):
    return _camel_to_underscore(method.replace("/", "__").replace("$", ""))


def _camel_to_underscore(string):
    s1 = _RE_FIRST_CAP.sub(r'\1_\2', string)
    return _RE_ALL_CAP.sub(r'\1_\2', s1).lower()
