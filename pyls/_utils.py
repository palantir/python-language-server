# Copyright 2017 Palantir Technologies, Inc.
import functools
import re
import threading

FIRST_CAP_RE = re.compile('(.)([A-Z][a-z]+)')
ALL_CAP_RE = re.compile('([a-z0-9])([A-Z])')


def debounce(interval_s):
    """Debounce calls to this function until interval_s seconds have passed."""
    def wrapper(func):
        @functools.wraps(func)
        def debounced(*args, **kwargs):
            if hasattr(debounced, '_timer'):
                debounced._timer.cancel()
            debounced._timer = threading.Timer(interval_s, func, args, kwargs)
            debounced._timer.start()
        return debounced
    return wrapper


def camel_to_underscore(string):
    s1 = FIRST_CAP_RE.sub(r'\1_\2', string)
    return ALL_CAP_RE.sub(r'\1_\2', s1).lower()
