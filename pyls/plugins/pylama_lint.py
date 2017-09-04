# Copyright 2017 Palantir Technologies, Inc.
import logging
from pylama import config
from pylama.main import check_path, parse_options
from pyls import hookimpl, lsp

log = logging.getLogger(__name__)


# Pylama sets up a stdout stream handler... which is bizarre
config.LOGGER.removeHandler(config.STREAM)


@hookimpl
def pyls_lint(document):
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
