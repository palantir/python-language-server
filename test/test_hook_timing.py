# Copyright 2017 Palantir Technologies, Inc.
import logging
import time

try:
    from unittest import mock
except ImportError:
    import mock

from pyls import python_ls
from pyls.python_ls import PythonLanguageServer


class FakeHookCaller(object):
    """Stands in for a pluggy hook caller so a hook can be made slow on demand."""

    def __init__(self, delay=0.0, plugin_names=(), exception=None):
        self.delay = delay
        self.plugin_names = list(plugin_names)
        self.exception = exception

    def __call__(self, **_kwargs):
        if self.delay:
            time.sleep(self.delay)
        if self.exception:
            raise self.exception
        return ['result']

    def get_hookimpls(self):
        return [mock.Mock(plugin_name=name) for name in self.plugin_names]


def _server(hook_caller):
    server = PythonLanguageServer(mock.Mock(), mock.Mock())
    server.config = mock.Mock()
    server.config.disabled_plugins = []
    server.config.plugin_manager.subset_hook_caller.return_value = hook_caller
    workspace = mock.Mock()
    workspace.get_document.return_value = None
    server._match_uri_to_workspace = lambda _uri: workspace  # pylint: disable=protected-access
    return server


def test_fast_hook_is_not_warned_about(caplog):
    server = _server(FakeHookCaller(plugin_names=['jedi_hover']))
    with caplog.at_level(logging.DEBUG, logger=python_ls.__name__):
        result = server._hook('pyls_hover', 'file:///tmp/a.py')  # pylint: disable=protected-access

    assert result == ['result']
    assert not [r for r in caplog.records if r.levelno >= logging.WARNING]
    assert any('pyls_hover' in r.getMessage() for r in caplog.records)


def test_slow_hook_is_reported_with_the_plugins_that_ran(caplog, monkeypatch):
    # Lowered so the test does not have to actually be slow.
    monkeypatch.setattr(python_ls, 'SLOW_HOOK_S', 0.01)
    server = _server(FakeHookCaller(delay=0.02, plugin_names=['pyflakes', 'pycodestyle']))

    with caplog.at_level(logging.DEBUG, logger=python_ls.__name__):
        server._hook('pyls_lint', 'file:///tmp/a.py')  # pylint: disable=protected-access

    warnings = [r.getMessage() for r in caplog.records if r.levelno >= logging.WARNING]
    assert len(warnings) == 1
    assert 'pyls_lint' in warnings[0]
    assert 'file:///tmp/a.py' in warnings[0]
    # The point of the message: which plugins could be responsible.
    assert 'pycodestyle' in warnings[0]
    assert 'pyflakes' in warnings[0]


def test_slow_hook_is_reported_even_when_it_raises(caplog, monkeypatch):
    """An exception after a long wait is exactly the case worth seeing in a log."""
    monkeypatch.setattr(python_ls, 'SLOW_HOOK_S', 0.01)
    server = _server(FakeHookCaller(delay=0.02, plugin_names=['pylint'],
                                    exception=ValueError('plugin failed')))

    with caplog.at_level(logging.DEBUG, logger=python_ls.__name__):
        try:
            server._hook('pyls_lint', 'file:///tmp/a.py')  # pylint: disable=protected-access
            raise AssertionError('expected the hook exception to propagate')
        except ValueError:
            pass

    warnings = [r.getMessage() for r in caplog.records if r.levelno >= logging.WARNING]
    assert len(warnings) == 1
    assert 'pyls_lint' in warnings[0]


def test_attribution_failure_does_not_break_the_request(caplog, monkeypatch):
    """Naming the plugins is a nicety and must never fail the request."""
    monkeypatch.setattr(python_ls, 'SLOW_HOOK_S', 0.01)
    hook_caller = FakeHookCaller(delay=0.02, plugin_names=['pyflakes'])
    hook_caller.get_hookimpls = mock.Mock(side_effect=RuntimeError('pluggy changed'))
    server = _server(hook_caller)

    with caplog.at_level(logging.DEBUG, logger=python_ls.__name__):
        result = server._hook('pyls_lint', 'file:///tmp/a.py')  # pylint: disable=protected-access

    assert result == ['result']
    warnings = [r.getMessage() for r in caplog.records if r.levelno >= logging.WARNING]
    assert len(warnings) == 1
    assert 'unknown' in warnings[0]
