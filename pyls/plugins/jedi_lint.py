from pyls import hookimpl, lsp


@hookimpl
def pyls_lint(document):
    errors = document.jedi_script().get_syntax_errors()
    diagnostics = []

    for error in errors:
        err_range = {
            'start': {
                'line': error.line - 1,
                'character': error.column,
                },
            'end': {
                'line': error.until_line - 1,
                # It's possible that we're linting an empty file. Even an empty
                # file might fail linting if it isn't named properly.
                'character': error.until_column,
                },
            }
        diagnostics.append({
            'source': 'jedi',
            'range': err_range,
            'message': error.get_message(),
            'severity': lsp.DiagnosticSeverity.Error,
        })
    return diagnostics
