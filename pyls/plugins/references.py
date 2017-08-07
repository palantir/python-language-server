# Copyright 2017 Palantir Technologies, Inc.
import logging
from pyls import hookimpl, workspace

log = logging.getLogger(__name__)


@hookimpl
def pyls_references(document, position, exclude_declaration=False):
    # Note that usages is not that great in a lot of cases: https://github.com/davidhalter/jedi/issues/744
    usages = document.jedi_script(position).usages()

    if exclude_declaration:
        # Filter out if the usage is the actual declaration of the thing
        usages = [d for d in usages if not d.is_definition()]

    return [{
        'uri': workspace.get_uri_like(document.uri, d.module_path) if d.module_path else document.uri,
        'range': {
            'start': {'line': d.line - 1, 'character': d.column},
            'end': {'line': d.line - 1, 'character': d.column + len(d.name)}
        }
    } for d in usages]
