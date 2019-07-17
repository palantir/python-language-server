# Copyright 2017 Palantir Technologies, Inc.
import logging
from pyls import hookimpl, _utils

log = logging.getLogger(__name__)


@hookimpl
def pyls_hover(document, position):
    definitions = document.jedi_script(position).goto_definitions()
    word = document.word_at_position(position)

    # Find first exact matching definition
    definition = next((x for x in definitions if x.name == word), None)

    if not definition:
        return {'contents': ''}

    # raw docstring returns only doc, without signature
    doc = _utils.format_docstring(definition.docstring(raw=True))

    # Find first exact matching signature
    signature = next((x.to_string() for x in definition.get_signatures() if x.name == word), '')

    contents = []
    if signature:
        contents.append({
            'language': 'python',
            'value': signature,
        })
    if doc:
        contents.append(doc)
    if not contents:
        return {'contents': ''}
    return {'contents': contents}
