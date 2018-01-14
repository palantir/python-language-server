# Copyright 2017 Palantir Technologies, Inc.
import re

_RE_FIRST_CAP = re.compile('(.)([A-Z][a-z]+)')
_RE_ALL_CAP = re.compile('([a-z0-9])([A-Z])')


class JSONRPCMethodDispatcher(object):
    """JSON RPC method dispatcher that calls methods on itself with params."""

    def __getitem__(self, item):
        """The jsonrpc dispatcher uses getitem to retrieve the RPC method implementation."""
        method_name = "m_" + _method_to_string(item)
        if not hasattr(self, method_name):
            raise KeyError("Cannot find method %s" % method_name)
        func = getattr(self, method_name)

        def wrapped(*args, **kwargs):
            return func(*args, **kwargs)

        return wrapped


def _method_to_string(method):
    return _camel_to_underscore(method.replace("/", "__").replace("$", ""))


def _camel_to_underscore(string):
    s1 = _RE_FIRST_CAP.sub(r'\1_\2', string)
    return _RE_ALL_CAP.sub(r'\1_\2', s1).lower()
