from pyls import hookimpl


@hookimpl
def pyls_code_lens():
    return [{
        'range': {
            'start': {'line': 0, 'character': 0},
            'end': {'line': 0, 'character': 0},
        },
        'command': {
            'title': 'My Code Lens',
            'command': 'my.code.lens',
        },
    }]
