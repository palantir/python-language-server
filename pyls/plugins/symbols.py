# Copyright 2017 Palantir Technologies, Inc.
import logging
from pyls import hookimpl
from pyls.lsp import SymbolKind

log = logging.getLogger(__name__)


@hookimpl
def pyls_document_symbols(config, document):
    all_scopes = config.plugin_settings('jedi_symbols').get('all_scopes', True)
    names = document.jedi_names(all_scopes=all_scopes)
    return list(filter(None, [serialize_name(n, document.uri) for n in names]))


def serialize_name(name, uri):
    result = {}
    parent = None

    try:
        # Jedi sometimes fails here.
        parent = name.parent()
    except:
        pass

    # - Only include global assignments in outline.
    # - Don't include underscore assignments in outline.
    # - Don't include function parameters in outline.
    if (name.type == 'statement' and
        (name.name == '_' or parent is None or
         (parent and parent.parent()))) or name.type == 'param':
        return None
    else:
        result['name'] = name.name

    result['location'] = {'uri': uri, 'range': _range(name)}
    result['kind'] = _kind(name)

    # All assignments have the filename as a there toplevel parent.
    if parent and parent.parent():
        result['containerName'] = parent.name

    return result


def _range(name):
    definition = name._name.tree_name.get_definition()
    (start_line, start_column) = definition.start_pos
    (end_line, end_column) = definition.end_pos
    return {
        'start': {'line': start_line - 1, 'character': start_column},
        'end': {'line': end_line - 1, 'character': end_column}
    }


def _kind(d):
    """ Return the VSCode Symbol Type """
    MAP = {
        'none': SymbolKind.Variable,
        'type': SymbolKind.Class,
        'tuple': SymbolKind.Class,
        'dict': SymbolKind.Class,
        'dictionary': SymbolKind.Class,
        'function': SymbolKind.Function,
        'lambda': SymbolKind.Function,
        'generator': SymbolKind.Function,
        'class': SymbolKind.Class,
        'instance': SymbolKind.Class,
        'method': SymbolKind.Method,
        'builtin': SymbolKind.Class,
        'builtinfunction': SymbolKind.Function,
        'module': SymbolKind.Module,
        'file': SymbolKind.File,
        'xrange': SymbolKind.Array,
        'slice': SymbolKind.Class,
        'traceback': SymbolKind.Class,
        'frame': SymbolKind.Class,
        'buffer': SymbolKind.Array,
        'dictproxy': SymbolKind.Class,
        'funcdef': SymbolKind.Function,
        'property': SymbolKind.Property,
        'import': SymbolKind.Module,
        'keyword': SymbolKind.Variable,
        'constant': SymbolKind.Constant,
        'variable': SymbolKind.Variable,
        'value': SymbolKind.Variable,
        'param': SymbolKind.Variable,
        'statement': SymbolKind.Variable,
        'boolean': SymbolKind.Boolean,
        'int': SymbolKind.Number,
        'longlean': SymbolKind.Number,
        'float': SymbolKind.Number,
        'complex': SymbolKind.Number,
        'string': SymbolKind.String,
        'unicode': SymbolKind.String,
        'list': SymbolKind.Array,
    }

    return MAP.get(d.type)
