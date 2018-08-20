# Copyright 2017 Palantir Technologies, Inc.
import logging
from pyls import hookimpl, uris

log = logging.getLogger(__name__)


@hookimpl
def pyls_definitions(config, document, position):
    expected_settings = {'follow_imports', 'follow_builtin_imports'}
    params = {k: v for k, v in config.settings().items() if k in expected_settings}
    definitions = document.jedi_script(position).goto_assignments(**params)

    definitions = [
        d for d in definitions
        if d.is_definition() and d.line is not None and d.column is not None and d.module_path is not None
    ]

    return [{
        'uri': uris.uri_with(document.uri, path=d.module_path),
        'range': {
            'start': {'line': d.line - 1, 'character': d.column},
            'end': {'line': d.line - 1, 'character': d.column + len(d.name)}
        }
    } for d in definitions]
