import re
from mypy import api as mypy_api
from pyls import hookimpl

line_pattern = r"([^:]+):(?:(\d+):)?(?:(\d+):)? (\w+): (.*)"


def parse_line(line, document=None):
    '''
    Return a language-server diagnostic from a line of the Mypy error report;
    optionally, use the whole document to provide more context on it.
    '''
    result = re.match(line_pattern, line)
    if result:
        _, lineno, offset, severity, msg = result.groups()
        lineno = int(lineno or 1)
        offset = int(offset or 0)
        errno = 2
        if severity == 'error':
            errno = 1
        diag = {
            'source': 'mypy',
            'range': {
                'start': {'line': lineno - 1, 'character': offset},
                # There may be a better solution, but mypy does not provide end
                'end': {'line': lineno - 1, 'character': offset + 1}
            },
            'message': msg,
            'severity': errno
        }
        if document:
            # although mypy does not provide the end of the affected range, we
            # can make a good guess by highlighting the word that Mypy flagged
            word = document.word_at_position(diag['range']['start'])
            if word:
                diag['range']['end']['character'] = (
                    diag['range']['start']['character'] + len(word))

        return diag


@hookimpl
def pyls_lint(config, document):
    live_mode = config.plugin_settings('pyls_mypy').get('live_mode', True)
    if live_mode:
        args = ['--incremental',
                '--show-column-numbers',
                '--follow-imports', 'silent',
                '--command', document.source]
    else:
        args = ['--incremental',
                '--show-column-numbers',
                '--follow-imports', 'silent',
                document.path]

    report, errors, _ = mypy_api.run(args)

    diagnostics = []
    for line in report.splitlines():
        diag = parse_line(line, document)
        if diag:
            diagnostics.append(diag)

    return diagnostics
