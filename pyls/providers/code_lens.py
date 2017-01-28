# Copyright 2017 Palantir Technologies, Inc.
import logging
from .base import JediProvider

log = logging.getLogger(__name__)


class JediReferencesProvider(JediProvider):
    """ Returns the references to whatever is under the cursor, if it's known """

    def run(self, doc_uri, position, exclude_declaration=False):
        usages = self.jedi_script(doc_uri, position).usages()

        if exclude_declaration:
            # Filter out if the usage is the actual declaration of the thing
            usages = [d for d in usages if not d.is_definition()]

        return [{
            'uri': self.workspace.get_uri_like(doc_uri, d.module_path),
            'range': {
                'start': {'line': d.line - 1, 'character': d.column},
                'end': {'line': d.line - 1, 'character': d.column + len(d.name)}
            }
        } for d in usages]
