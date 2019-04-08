# Copyright 2018 Google LLC.
"""Linter plugin for pylint."""
import collections
import json
import logging
import sys

from pylint.epylint import py_run
from pyls import hookimpl, lsp

log = logging.getLogger(__name__)

CONFIG_FILE = 'rcfile'


class PylintLinter(object):
    last_diags = collections.defaultdict(list)

    @staticmethod
    def add_rc_to_flags(config, flags):
        log.debug("Trying to set config file flags.")
        rcfile = config.plugin_settings('pylint').get(CONFIG_FILE, None)
        if rcfile:
            log.debug("Setting pylint configuration file «%s».", rcfile)
            return flags + ' --rcfile ' + rcfile
        return flags

    @classmethod
    def lint(cls, config, document, is_saved, flags=''):
        """Plugin interface to pyls linter.

        Args:
            config: The configuration. Used to get configuration file setting.
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

        # py_run will call shlex.split on its arguments, and shlex.split does
        # not handle Windows paths (it will try to perform escaping). Turn
        # backslashes into forward slashes first to avoid this issue.
        path = document.path
        if sys.platform.startswith('win'):
            path = path.replace('\\', '/')

        flags = PylintLinter.add_rc_to_flags(config, flags)

        out, _err = py_run(
            '{} -f json {}'.format(path, flags), return_std=True
        )

        # pylint prints nothing rather than [] when there are no diagnostics.
        # json.loads will not parse an empty string, so just return.
        json_str = out.getvalue()
        if not json_str.strip():
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
        for diag in json.loads(json_str):
            # pylint lines index from 1, pyls lines index from 0
            line = diag['line'] - 1
            # But both index columns from 0
            err_range = {
                'start': {
                    'line': line,
                    'character': diag['column']
                },
                'end': {
                    'line': line,
                    # It's possible that we're linting an empty file. Even an empty
                    # file might fail linting if it isn't named properly.
                    'character': len(document.lines[line]) if document.lines else 0
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


@hookimpl
def pyls_lint(config, document, is_saved):
    return PylintLinter.lint(config, document, is_saved)