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
    return {'contents': definitions[0].docstring() or ""}
