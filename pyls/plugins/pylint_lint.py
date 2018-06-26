# Copyright 2018 SUSE, Inc.
import os
import logging
import pylint.config
import pylint.lint
import pylint.reporters
from pyls import hookimpl, lsp

log = logging.getLogger(__name__)


@hookimpl
def pyls_lint(config, document, on_change):
    settings = config.plugin_settings('pylint')
    log.debug("Got pylint settings: %s", settings)

    collector = DiagCollector()
    if not on_change:
        log.debug('Running pylint on \'%s\' in \'%s\'', document.path, os.getcwd())
        pylint.lint.Run(args=[document.path], reporter=collector, exit=False)

    return [map_diagnostic(diag, document.lines) for diag in collector.messages]


class DiagCollector(pylint.reporters.CollectingReporter):

    def display_reports(self, layout):
        """do nothing"""

    def _display(self, layout):
        """do nothing"""


def map_diagnostic(message, lines):
    severity = lsp.DiagnosticSeverity.Warning
    if message.category in ['fatal', 'error']:
        severity = lsp.DiagnosticSeverity.Error

    # LSP lines start at 0, while pylint starts at 1
    err_range = {
        'start': {'line': message.line - 1, 'character': message.column},
        'end': {
            # FIXME: It's a little naive to mark until the end of the line, can we not easily do better?
            'line': message.line - 1,
            'character': len(lines[message.line - 1]) - 1
        },
    }

    return {
        'source': 'pylint',
        'range': err_range,
        'message': message.msg.split('\n')[0],
        'code': message.symbol,
        'severity': severity
    }
