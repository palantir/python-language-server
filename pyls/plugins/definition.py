# Copyright 2017 Palantir Technologies, Inc.
import logging
from pyls import hookimpl, uris

log = logging.getLogger(__name__)


@hookimpl
def pyls_definitions(document, position):
    definitions = document.jedi_script(position).goto_definitions()
    definitions = [
        d for d in definitions
        if d.is_definition() and d.line is not None and d.column is not None
    ]

    return [{
        'uri': uris.uri_with(document.uri, path=d.module_path) if d.module_path else document.uri,
        'range': {
            'start': {'line': d.line - 1, 'character': d.column},
            'end': {'line': d.line - 1, 'character': d.column + len(d.name)}
        }
    } for d in definitions]
