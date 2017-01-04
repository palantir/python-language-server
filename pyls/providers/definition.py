# Copyright 2017 Palantir Technologies, Inc.
import logging
from base import JediProvider

log = logging.getLogger(__name__)


class JediDefinitionsProvider(JediProvider):
    """ Returns the position of the definitions of something under the cursor """

    def run(self, doc_uri, position):
        definitions = self.jedi_script(doc_uri, position).goto_definitions()

        definitions = filter(lambda d: d.is_definition(), definitions)

        return [{
            'uri': self.workspace.get_uri_like(doc_uri, d.module_path),
            'range': {
                'start': {'line': d.line - 1, 'character': d.column},
                'end': {'line': d.line - 1, 'character': d.column + len(d.name)}
            }
        } for d in definitions]
