# Copyright 2017 Palantir Technologies, Inc.
import logging
from .base import BaseProvider
from yapf.yapflib.yapf_api import FormatCode

log = logging.getLogger(__name__)


class YapfFormatter(BaseProvider):

    def run(self, doc_uri, range=None):
        document = self.workspace.get_document(doc_uri)

        lines = None
        if range:
            # First we 'round' the range up/down to full lines only
            range['start']['character'] = 0
            range['end']['line'] += 1
            range['end']['character'] = 0

            # From Yapf docs:
            # lines: (list of tuples of integers) A list of tuples of lines, [start, end],
            #   that we want to format. The lines are 1-based indexed. It can be used by
            #   third-party code (e.g., IDEs) when reformatting a snippet of code rather
            #   than a whole file.

            # Add 1 for 1-indexing vs VSCode's 0-indexing
            lines = [(range['start']['line'] + 1, range['end']['line'] + 1)]

        new_source, changed = FormatCode(document.source, lines=lines, filename=document.filename)

        if not changed:
            return []

        # I'm too lazy at the moment to parse diffs into TextEdit items
        # So let's just return the entire file...
        return [{
            'range': {
                'start': {'line': 0, 'character': 0},
                # End char 0 of the line after our document
                'end': {'line': len(document.lines), 'character': 0}
            },
            'newText': new_source
        }]
