# Copyright 2018 Google LLC.
"""Linter plugin for pylint."""
import collections
import logging
import os
import shlex
import subprocess
import sys

from pyls import hookimpl, lsp

try:
    import ujson as json
except Exception:  # pylint: disable=broad-except
    import json

if sys.version_info.major == 2:
    from StringIO import StringIO

    # subprocess.Popen() on Windows expects that env contains only
    # "str" keys/values (= "bytes" for Python2.x, "unicode" for
    # Python3.x), even though pyls treats all path values as "unicode"
    # regardless of Python version
    def stringify(u):
        return u.encode('utf-8')
else:
    from io import StringIO

    def stringify(u):
        return u

log = logging.getLogger(__name__)


def spawn_pylint(document, flags):
    """Spawn pylint process as same as pylint.epylint.py_run
    """
    path = document.path
    if sys.platform.startswith('win'):
        # Now, shlex.split is not applied on path, and Windows path
        # (including '\\') is safe enough. But turn backslashes into
        # forward slashes in order to keep previous behavior.
        path = path.replace('\\', '/')

    env = dict(os.environ)
    env["PYTHONPATH"] = stringify(os.pathsep.join(document.sys_path()))

    # Detect if we use Python as executable or not, else default to `python`
    executable = sys.executable if "python" in sys.executable else "python"

    # Create command line to call pylint
    epylint_part = [executable, "-c", "from pylint import epylint;epylint.Run()"]
    options = shlex.split(flags, posix=not sys.platform.startswith("win"))

    pylint_call = [path, '-f', 'json'] + options
    log.debug("Calling pylint with %r", pylint_call)

    cli = epylint_part + pylint_call

    stdout = stderr = subprocess.PIPE

    # Call pylint in a subprocess
    process = subprocess.Popen(
        cli,
        shell=False,
        stdout=stdout,
        stderr=stderr,
        env=env,
        universal_newlines=True,
    )
    proc_stdout, proc_stderr = process.communicate()
    # Return standard output and error
    return StringIO(proc_stdout), StringIO(proc_stderr)


class PylintLinter(object):
    last_diags = collections.defaultdict(list)

    @classmethod
    def lint(cls, document, is_saved, flags=''):
        """Plugin interface to pyls linter.

        Args:
            document: The document to be linted.
            is_saved: Whether or not the file has been saved to disk.
            flags: Additional flags to pass to pylint. Not exposed to
                pyls_lint, but used for testing.

        Returns:
            A list of dicts with the following format:

                {
                    'source': 'pylint',
                    'range': {
                        'start': {
                            'line': start_line,
                            'character': start_column,
                        },
                        'end': {
                            'line': end_line,
                            'character': end_column,
                        },
                    }
                    'message': msg,
                    'severity': lsp.DiagnosticSeverity.*,
                }
        """
        if not is_saved:
            # Pylint can only be run on files that have been saved to disk.
            # Rather than return nothing, return the previous list of
            # diagnostics. If we return an empty list, any diagnostics we'd
            # previously shown will be cleared until the next save. Instead,
            # continue showing (possibly stale) diagnostics until the next
            # save.
            return cls.last_diags[document.path]

        json_out, err = spawn_pylint(document, flags)

        # Get strings
        json_out = json_out.getvalue()
        err = err.getvalue()

        if err != '':
            log.error("Error calling pylint: '%s'", err)

        # pylint prints nothing rather than [] when there are no diagnostics.
        # json.loads will not parse an empty string, so just return.
        if not json_out.strip():
            cls.last_diags[document.path] = []
            return []

        # Pylint's JSON output is a list of objects with the following format.
        #
        #     {
        #         "obj": "main",
        #         "path": "foo.py",
        #         "message": "Missing function docstring",
        #         "message-id": "C0111",
        #         "symbol": "missing-docstring",
        #         "column": 0,
        #         "type": "convention",
        #         "line": 5,
        #         "module": "foo"
        #     }
        #
        # The type can be any of:
        #
        #  * convention
        #  * error
        #  * fatal
        #  * refactor
        #  * warning
        diagnostics = []
        for diag in json.loads(json_out):
            # pylint lines index from 1, pyls lines index from 0
            line = diag['line'] - 1

            err_range = {
                'start': {
                    'line': line,
                    # Index columns start from 0
                    'character': diag['column'],
                },
                'end': {
                    'line': line,
                    # It's possible that we're linting an empty file. Even an empty
                    # file might fail linting if it isn't named properly.
                    'character': len(document.lines[line]) if document.lines else 0,
                },
            }

            if diag['type'] == 'convention':
                severity = lsp.DiagnosticSeverity.Information
            elif diag['type'] == 'error':
                severity = lsp.DiagnosticSeverity.Error
            elif diag['type'] == 'fatal':
                severity = lsp.DiagnosticSeverity.Error
            elif diag['type'] == 'refactor':
                severity = lsp.DiagnosticSeverity.Hint
            elif diag['type'] == 'warning':
                severity = lsp.DiagnosticSeverity.Warning

            diagnostics.append({
                'source': 'pylint',
                'range': err_range,
                'message': '[{}] {}'.format(diag['symbol'], diag['message']),
                'severity': severity,
                'code': diag['message-id']
            })
        cls.last_diags[document.path] = diagnostics
        return diagnostics


def _build_pylint_flags(settings):
    """Build arguments for calling pylint."""
    pylint_args = settings.get('args')
    if pylint_args is None:
        return ''
    return ' '.join(pylint_args)


@hookimpl
def pyls_settings():
    # Default pylint to disabled because it requires a config
    # file to be useful.
    return {'plugins': {'pylint': {'enabled': False, 'args': []}}}


@hookimpl
def pyls_lint(config, document, is_saved):
    settings = config.plugin_settings('pylint')
    log.debug("Got pylint settings: %s", settings)
    flags = _build_pylint_flags(settings)
    return PylintLinter.lint(document, is_saved, flags=flags)
