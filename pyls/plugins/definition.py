# Copyright 2017 Palantir Technologies, Inc.
import logging
from pyls import hookimpl, uris

log = logging.getLogger(__name__)


@hookimpl
def pyls_definitions(document, position, config):
    follow_imports = config.settings().get('plugins').get('jedi', {}).get('follow_imports', False)
    definitions = document.jedi_script(position).goto_assignments(follow_imports=follow_imports)

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
