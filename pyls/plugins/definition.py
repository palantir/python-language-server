# Copyright 2017 Palantir Technologies, Inc.
import logging
from pyls import hookimpl, uris

log = logging.getLogger(__name__)


@hookimpl
def pyls_definitions(config, document, position):
    settings = config.plugin_settings('jedi_definition')
    definitions = document.jedi_script(position).goto_assignments(
        follow_imports=settings.get('follow_imports', True),
        follow_builtin_imports=settings.get('follow_builtin_imports', True))

    return [
        {
            'uri': uris.uri_with(document.uri, path=d.module_path),
            'range': {
                'start': {'line': d.line - 1, 'character': d.column},
                'end': {'line': d.line - 1, 'character': d.column + len(d.name)},
            }
        }
        for d in definitions
        if d.is_definition() and d.line is not None and d.column is not None and d.module_path is not None
    ]
