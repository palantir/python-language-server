# Copyright 2019 Palantir Technologies, Inc.
"""Linter pluging for flake8"""
import logging
from flake8.api import legacy as flake8
from pyls import hookimpl, lsp

log = logging.getLogger(__name__)


@hookimpl
def pyls_settings():
    # Default flake8 to disabled
    return {'plugins': {'flake8': {'enabled': False}}}


@hookimpl
def pyls_lint(config, document):
    settings = config.plugin_settings('flake8')
    log.debug("Got flake8 settings: %s", settings)

    opts = {
        'exclude': settings.get('exclude'),
        'filename': settings.get('filename'),
        'hang_closing': settings.get('hangClosing'),
        'ignore': settings.get('ignore'),
        'max_line_length': settings.get('maxLineLength'),
        'select': settings.get('select'),
    }

    # Build the flake8 checker and use it to generate a report from the document
    kwargs = {k: v for k, v in opts.items() if v}
    style_guide = flake8.get_style_guide(quiet=4, verbose=0, **kwargs)
    report = style_guide.check_files([document.path])

    return parse_report(document, report)


def parse_report(document, report):
    """
    Build a diagnostics from a report, it should extract every result and format
    it into a dict that looks like this:
        {
            'source': 'flake8',
            'code': code, # 'E501'
            'range': {
                'start': {
                    'line': start_line,
                    'character': start_column,
                },
                'end': {
                    'line': end_line,
                    'character': end_column,
                },
            },
            'message': msg,
            'severity': lsp.DiagnosticSeverity.*,
        }

    Args:
        document: The document to be linted.
        report: A Report object returned by checking the document.
    Returns:
        A list of dictionaries.
    """

    file_checkers = report._application.file_checker_manager.checkers
    # No file have been checked
    if not file_checkers:
        return []
    # There should be only a filechecker since we are parsing using a path and not a pattern
    if len(file_checkers) > 1:
        log.error("Flake8 parsed more than a file for '%s'", document.path)

    diagnostics = []
    file_checker = file_checkers[0]
    for error in file_checker.results:
        code, line, character, msg, physical_line = error
        diagnostics.append(
            {
                'source': 'flake8',
                'code': code,
                'range': {
                    'start': {
                        'line': line - 1,
                        'character': character
                    },
                    'end': {
                        'line': line - 1,
                        # no way to determine the column
                        'character': len(physical_line)
                    }
                },
                'message': msg,
                # no way to determine the severity using the legacy api
                'severity': lsp.DiagnosticSeverity.Warning,
            }
        )

    return diagnostics
