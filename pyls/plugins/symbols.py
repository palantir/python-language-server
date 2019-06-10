# Copyright 2017 Palantir Technologies, Inc.
import logging
from pyls import hookimpl
from pyls.lsp import SymbolKind

log = logging.getLogger(__name__)


@hookimpl
def pyls_document_symbols(config, document):
    all_scopes = config.plugin_settings('jedi_symbols').get('all_scopes', True)

    symbols_capabilities = config.capabilities.get('textDocument', {}).get('documentSymbol', {})

    if symbols_capabilities.get('hierarchicalDocumentSymbolSupport', False):
        # Disable all_scopes so we can do our own symbol recursion
        log.debug("Returning hierarchical document symbols for %s", document)
        return _hierarchical_symbols(document.jedi_names(all_scopes=False))
    else:
        return _flat_symbols(document, document.jedi_names(all_scopes=all_scopes))


def _hierarchical_symbols(definitions):
    """Return symbols as recursive DocumentSymbol objects."""
    defs = []
    for definition in definitions:
        if not _include_def(definition):
            continue

        symbol = _document_symbol(definition)
        if symbol is not None:
            defs.append(symbol)

    return defs


def _document_symbol(definition):
    if not _include_def(definition):
        return None

    if definition.type == 'statement':
        # Currently these seem to cause Jedi to error when calling defined_names()
        children = []
    else:
        try:
            children = _hierarchical_symbols(definition.defined_names())
        except Exception:  # pylint: disable=broad-except
            log.exception("Failed to get children of %s symbol: %s", definition.type, definition)
            children = []

    return {
        'name': definition.name,
        'detail': _detail_name(definition),
        'range': _range(definition),
        'selectionRange': _name_range(definition),
        'kind': _kind(definition),
        'children': children
    }


def _flat_symbols(document, definitions):
    """Return symbols as SymbolInformation object."""
    return [{
        'name': d.name,
        'containerName': _container(d),
        'location': {
            'uri': document.uri,
            'range': _range(d),
        },
        'kind': _kind(d),
    } for d in definitions if _include_def(d)]


def _include_def(definition):
    return (
        # Skip built-ins
        not definition.in_builtin_module() and
        # Don't tend to include parameters as symbols
        definition.type != 'param' and
        # Unused vars should also be skipped
        definition.name != '_' and
        # Skip imports, since they're not _really_ defined by us
        not definition._name.is_import() and
        # Only definitions for which we know the "kind"
        _kind(definition) is not None
    )


def _detail_name(definition):
    name = definition.full_name
    if name.startswith('__main__.'):
        name = name[len('__main__.'):]
    return name


def _container(definition):
    try:
        # Jedi sometimes fails here.
        parent = definition.parent()
        # Here we check that a grand-parent exists to avoid declaring symbols
        # as children of the module.
        if parent.parent():
            return parent.name
    except:  # pylint: disable=bare-except
        return None

    return None


def _range(definition):
    """Return the LSP range for the symbol.

    For a function, this would be all lines of code for the function.
    """
    # This gets us more accurate end position
    definition = definition._name.tree_name.get_definition()
    (start_line, start_column) = definition.start_pos
    (end_line, end_column) = definition.end_pos
    return {
        'start': {'line': start_line - 1, 'character': start_column},
        'end': {'line': end_line - 1, 'character': end_column}
    }


def _name_range(definition):
    """Returns the LSP range for the name of the symbol.

    For a function, this would only be the range of the function name.
    """
    # This gets us more accurate end position
    definition = definition._name.tree_name
    (start_line, start_column) = definition.start_pos
    (end_line, end_column) = definition.end_pos
    return {
        'start': {'line': start_line - 1, 'character': start_column},
        'end': {'line': end_line - 1, 'character': end_column}
    }


_SYMBOL_KIND_MAP = {
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


def _kind(d):
    """ Return the VSCode Symbol Type """
    return _SYMBOL_KIND_MAP.get(d.type)
