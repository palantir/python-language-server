# Copyright 2017 Palantir Technologies, Inc.
import logging
from pyls import hookimpl, lsp, _utils

log = logging.getLogger(__name__)


@hookimpl
def pyls_hover(document, position):
    definitions = document.jedi_script(position).goto_definitions()
    word = document.word_at_position(position)

    # Find an exact match for a completion
    definitions = [d for d in definitions if d.name == word]

    if not definitions:
        return None

    md_docstring = _utils.format_docstring(definitions[0].docstring())
    return {'contents': {
        'type': lsp.MarkupKind.Markdown,
        'value': md_docstring
    }} if md_docstring else None
