# Copyright 2017 Palantir Technologies, Inc.
import logging
from pyls import hookimpl

log = logging.getLogger(__name__)


@hookimpl
def pyls_hover(document, position):
    definitions = document.jedi_script(position).goto_definitions()
    word = document.word_at_position(position)

    # Find an exact match for a completion
    definitions = [d for d in definitions if d.name == word]

    if len(definitions) == 0:
        # :(
        return {'contents': ''}

    # Maybe the docstring could be huuuuuuuuuuge...
    return {'contents': _format_docstring(definitions[0].docstring()) or ""}


def _format_docstring(contents):
    """Python doc strings come in a number of formats, but LSP wants markdown.

    Until we can find a fast enough way of discovering and parsing each format,
    we can do a little better by at least preserving indentation.
    """
    contents = contents.replace('\t', '\u00A0' * 4)
    contents = contents.replace('  ', '\u00A0' * 2)
    return contents
