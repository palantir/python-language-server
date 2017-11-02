# Copyright 2017 Palantir Technologies, Inc.
import logging
from pyls.lsp import CompletionItemKind
from pyls import hookimpl

from rope.contrib.codeassist import code_assist, sorted_proposals

log = logging.getLogger(__name__)


@hookimpl
def pyls_completions(document, position):
    log.debug('Launching Rope')
    mock_position = dict(position)
    mock_position['character'] -= 1
    word = document.word_at_position(mock_position)
    if word == 'import':
        return None

    offset = document.offset_at_position(position)
    definitions = code_assist(
        document._rope_project, document.source,
        offset, document._rope, maxfixes=3)

    definitions = sorted_proposals(definitions)
    new_definitions = []
    for d in definitions:
        try:
            doc = d.get_doc()
        except AttributeError:
            doc = None
        new_definitions.append({
            'label': d.name,
            'kind': _kind(d),
            'detail': '{0} {1}'.format(d.scope or "", d.name),
            'documentation': doc or "",
            'sortText': _sort_text(d)})
    definitions = new_definitions
    log.debug('Rope finished')
    return definitions


def _sort_text(definition):
    """ Ensure builtins appear at the bottom.
    Description is of format <type>: <module>.<item>
    """
    if definition.scope == 'builtin':
        return 'z' + definition.name

    if definition.name.startswith("_"):
        # It's a 'hidden' func, put it next last
        return 'y' + definition.name

    # Else put it at the front
    return 'a' + definition.name


def _kind(d):
    """ Return the VSCode type """
    MAP = {
        'none': CompletionItemKind.Value,
        'type': CompletionItemKind.Class,
        'tuple': CompletionItemKind.Class,
        'dict': CompletionItemKind.Class,
        'dictionary': CompletionItemKind.Class,
        'function': CompletionItemKind.Function,
        'lambda': CompletionItemKind.Function,
        'generator': CompletionItemKind.Function,
        'class': CompletionItemKind.Class,
        'instance': CompletionItemKind.Reference,
        'method': CompletionItemKind.Method,
        'builtin': CompletionItemKind.Class,
        'builtinfunction': CompletionItemKind.Function,
        'module': CompletionItemKind.Module,
        'file': CompletionItemKind.File,
        'xrange': CompletionItemKind.Class,
        'slice': CompletionItemKind.Class,
        'traceback': CompletionItemKind.Class,
        'frame': CompletionItemKind.Class,
        'buffer': CompletionItemKind.Class,
        'dictproxy': CompletionItemKind.Class,
        'funcdef': CompletionItemKind.Function,
        'property': CompletionItemKind.Property,
        'import': CompletionItemKind.Module,
        'keyword': CompletionItemKind.Keyword,
        'constant': CompletionItemKind.Variable,
        'variable': CompletionItemKind.Variable,
        'value': CompletionItemKind.Value,
        'param': CompletionItemKind.Variable,
        'statement': CompletionItemKind.Keyword,
    }

    return MAP.get(d.type)
