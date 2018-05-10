# Copyright 2017 Palantir Technologies, Inc.
import logging
from pyls import hookimpl, lsp, uris

log = logging.getLogger(__name__)


@hookimpl
def pyls_document_highlight(document, position):
    usages = document.jedi_script(position).usages()

    def local_to_document(definition):
        return not definition.module_path or uris.uri_with(document.uri, path=definition.module_path) == document.uri

    return [{
        'range': {
            'start': {'line': d.line - 1, 'character': d.column},
            'end': {'line': d.line - 1, 'character': d.column + len(d.name)}
        },
        'kind': lsp.DocumentHighlightKind.Write if d.is_definition() else lsp.DocumentHighlightKind.Read
    } for d in usages if local_to_document(d)]
