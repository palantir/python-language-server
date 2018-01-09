# Copyright 2017 Palantir Technologies, Inc.
import logging
import pycodestyle
from pyls import hookimpl, lsp

log = logging.getLogger(__name__)


@hookimpl
def pyls_lint(config, document):
    settings = config.plugin_settings('pycodestyle')
    log.debug("Got pycodestyle settings: %s", settings)

    opts = {
        'exclude': ','.join(settings.get('exclude', [])),
        'filename': ','.join(settings.get('filename', [])),
        'hang_closing': settings.get('hangClosing'),
        'ignore': ','.join(settings.get('ignore', [])),
        'max_line_length': settings.get('maxLineLength'),
        'select': ','.join(settings.get('select', [])),
    }

    styleguide = pycodestyle.StyleGuide({k: v for k, v in opts.items() if v is not None})
    c = pycodestyle.Checker(
        filename=document.uri, lines=document.lines, options=styleguide.options,
        report=PyCodeStyleDiagnosticReport(styleguide.options)
    )
    c.check_all()
    diagnostics = c.report.diagnostics

    return diagnostics


class PyCodeStyleDiagnosticReport(pycodestyle.BaseReport):

    def __init__(self, options=None):
        self.diagnostics = []
        super(PyCodeStyleDiagnosticReport, self).__init__(options=options)

    def error(self, line_number, offset, text, check):
        # PyCodeStyle will sometimes give you an error the line after the end of the file
        #   e.g. no newline at end of file
        # In that case, the end offset should just be some number ~100
        # (because why not? There's nothing to underline anyways)
        err_range = {
            'start': {'line': line_number - 1, 'character': offset},
            'end': {
                # FIXME: It's a little naiive to mark until the end of the line, can we not easily do better?
                'line': line_number - 1,
                'character': 100 if line_number > len(self.lines) else len(self.lines[line_number - 1])
            },
        }
        code, _message = text.split(" ", 1)

        self.diagnostics.append({
            'source': 'pycodestyle',
            'range': err_range,
            'message': text,
            'code': code,
            # Are style errors really ever errors?
            'severity': lsp.DiagnosticSeverity.Warning
        })
