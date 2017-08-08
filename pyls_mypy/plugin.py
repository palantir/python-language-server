# Copyright 2017 Mikael Knutsson
from mypy import api as mypy_api
from pyls import hookimpl


@hookimpl
def pyls_lint(document):
    args = ('--ignore-missing-imports',
            '--incremental',
            '--show-column-numbers',
            '--command', document.source)

    report, errors, _ = mypy_api.run(args)
    diagnostics = []
    for line in report.splitlines():
        split = line.split(':', 4)
        if len(split) == 5:
            _, lineno, offset, severity, msg = split
        else:
            _, lineno, severity, msg = split
            offset = 0
        lineno = int(lineno)
        offset = int(offset)
        errno = 2
        if severity.strip() == 'error':
            errno = 1
        diagnostics.append({
            'source': 'mypy',
            'range': {
                'start': {'line': lineno - 1, 'character': offset},
                # There may be a better solution, but mypy does not provide end
                'end': {'line': lineno - 1, 'character': offset + 1}
            },
            'message': msg.strip(),
            'severity': errno
        })

    return diagnostics
