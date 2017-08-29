# Copyright 2017 Palantir Technologies, Inc.
import functools
import threading


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
