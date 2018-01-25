# Copyright 2017 Palantir Technologies, Inc.
import logging
import pydocstyle
from pyls import hookimpl, lsp

log = logging.getLogger(__name__)

# PyDocstyle is a little verbose in debug message
pydocstyle_logger = logging.getLogger(pydocstyle.utils.__name__)
pydocstyle_logger.setLevel(logging.INFO)


@hookimpl
def pyls_settings():
    # Default pydocstyle to disabled
    return {'plugins': {'pydocstyle': {'enabled': False}}}


@hookimpl
def pyls_lint(document):
    conf = pydocstyle.config.ConfigurationParser()
    conf.parse()
    conf._arguments = [document.path]

    # Will only yield a single filename, the document path
    diags = []
    for filename, checked_codes, ignore_decorators in conf.get_files_to_check():
        errors = pydocstyle.checker.ConventionChecker().check_source(
            document.source, filename, ignore_decorators=ignore_decorators
        )

        try:
            for error in errors:
                if error.code not in checked_codes:
                    continue
                diags.append(_parse_diagnostic(document, error))
        except pydocstyle.parser.ParseError:
            # In the case we cannot parse the Python file, just continue
            pass

    log.info("Got pydocstyle errors: %s", diags)
    return diags


def _parse_diagnostic(document, error):
    lineno = error.definition.start - 1
    line = document.lines[0] if document.lines else ""

    start_character = len(line) - len(line.lstrip())
    end_character = len(line)

    return {
        'source': 'pydocstyle',
        'code': error.code,
        'message': error.message,
        'severity': lsp.DiagnosticSeverity.Warning,
        'range': {
            'start': {
                'line': lineno,
                'character': start_character
            },
            'end': {
                'line': lineno,
                'character': end_character
            }
        }
    }
