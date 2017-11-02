# Copyright 2017 Palantir Technologies, Inc.
import functools
import logging
import re
import threading

log = logging.getLogger(__name__)

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


def list_to_string(value):
    return ",".join(value) if type(value) == list else value


def race_hooks(hook_caller, pool, **kwargs):
    """Given a pluggy hook spec, execute impls in parallel returning the first non-None result.

    Note this does not support a lot of pluggy functionality, e.g. hook wrappers.
    """
    impls = hook_caller._nonwrappers + hook_caller._wrappers
    log.debug("Racing hook impls for hook %s: %s", hook_caller, impls)

    if not impls:
        return None

    def _apply(impl):
        return impl, impl.function(**kwargs)

    # imap unordered gives us an iterator over the items in the order they finish.
    # We have to be careful to set chunksize to 1 to ensure hooks each get their own thread.
    # Unfortunately, there's no way to interrupt these threads, so we just have to leave them be.
    first_impl, result = next(pool.imap_unordered(_apply, impls, chunksize=1))
    log.debug("Hook from plugin %s returned: %s", first_impl.plugin_name, result)
    return result
