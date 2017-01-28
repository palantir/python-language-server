# Copyright 2017 Palantir Technologies, Inc.
import logging
from .base import JediProvider

log = logging.getLogger(__name__)


class JediDocStringHoverProvider(JediProvider):
    """ Displays the docstring of whatever is under the cursor, if it's known """

    def run(self, doc_uri, position):
        completions = self.jedi_script(doc_uri, position).completions()
        document = self.workspace.get_document(doc_uri)
        word = document.word_at_position(position)

        # Find an exact match for a completion
        completions = [c for c in completions if c.name == word]

        if len(completions) == 0:
            # :(
            return {'contents': ''}

        # Maybe the docstring could be huuuuuuuuuuge...
        return {'contents': completions[0].docstring() or ""}
