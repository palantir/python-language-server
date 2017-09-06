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

        for err in errors:
            if err.code not in checked_codes:
                continue

            lineno = err.definition.start - 1
            line = document.lines[lineno]
            character = len(line) - len(line.lstrip())
            diags.append({
                'source': 'pydocstyle',
                'code': err.code,
                'message': err.message,
                'severity': lsp.DiagnosticSeverity.Warning,
                'range': {
                    'start': {'line': lineno, 'character': character},
                    'end': {'line': lineno, 'character': len(document.lines[lineno])}
                }
            })

    return diags
