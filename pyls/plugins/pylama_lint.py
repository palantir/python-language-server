# Copyright 2017 Palantir Technologies, Inc.
from pyls import hookimpl, lsp


@hookimpl
def pyls_settings():
    # Disable pylama by default
    return {'plugins': {'pylama': {'enabled': False}}}


@hookimpl
def pyls_lint(document):
    """PyLama does a couple of odd things:
        * Sets up a log handler to write to stdout
        * Patches PyFlakes (and other linters?) to change message strings etc.

    So we lazily import pylama only if it used, in which case you probably don't care
    that other linters may stop working.
    """
    from pylama import config
    from pylama.main import check_path, parse_options

    # Pylama sets up a stdout stream handler... which is bizarre
    if config.STREAM in config.LOGGER.handlers:
        config.LOGGER.removeHandler(config.STREAM)

    options = parse_options([document.path])
    errors = check_path(options, code=document.source)
    return [{
        'source': 'pylama',
        'range': {
            'start': {'line': error.lnum - 1, 'character': error.col - 1},
            'end': {'line': error.lnum - 1, 'character': len(document.lines[error.lnum - 1])},
        },
        'message': error.text,
        'code': error.number,
        'severity': _severity(error.type),
    } for error in errors]


def _severity(error_type):
    if error_type == 'E':
        return lsp.DiagnosticSeverity.Error
    elif error_type == 'W':
        return lsp.DiagnosticSeverity.Warning
