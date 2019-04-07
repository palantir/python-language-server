# Copyright 2017 Palantir Technologies, Inc.
import logging
from pyls import hookimpl
from pyls.lsp import SymbolKind

log = logging.getLogger(__name__)


@hookimpl
def pyls_document_symbols(config, document):
    if not config.capabilities.get("documentSymbol", {}).get("hierarchicalDocumentSymbolSupport", False):
        return pyls_document_symbols_legacy(config, document)
    # returns DocumentSymbol[]
    hide_imports = config.plugin_settings('jedi_symbols').get('hide_imports', False)
    definitions = document.jedi_names(all_scopes=False)

    def transform(d):
        include_d = _include_def(d, hide_imports)
        if include_d is None:
            return None
        children = [dt for dt in (transform(d1) for d1 in d.defined_names()) if dt] if include_d else None
        detailName = d.full_name
        if detailName and detailName.startswith("__main__."):
            detailName = detailName[9:]
        return {
            'name': d.name,
            'detail': detailName,
            'range': _range(d),
            'selectionRange': _name_range(d),
            'kind': _kind(d),
            'children': children
        }
    return [dt for dt in (transform(d) for d in definitions) if dt]


def pyls_document_symbols_legacy(config, document):
    # returns SymbolInformation[]
    all_scopes = config.plugin_settings('jedi_symbols').get('all_scopes', True)
    hide_imports = config.plugin_settings('jedi_symbols').get('hide_imports', False)
    definitions = document.jedi_names(all_scopes=all_scopes)
    return [{
        'name': d.name,
        'containerName': _container(d),
        'location': {
            'uri': document.uri,
            'range': _range(d),
        },
        'kind': _kind(d),
    } for d in definitions if _include_def(d, hide_imports) is not None]


def _include_def(definition, hide_imports=True):
    # returns
    # True: include def and sub-defs
    # False: include def but do not include sub-defs
    # None: Do not include def or sub-defs
    if (  # Unused vars should also be skipped
            definition.name != '_' and
            definition.is_definition() and
            not definition.in_builtin_module() and
            _kind(definition) is not None
    ):
        if definition._name.is_import():
            return None if hide_imports else False
        # for `statement`, we do not enumerate its child nodes. It tends to cause Error.
        return definition.type not in ("statement",)
    return None


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
    # This gets us more accurate end position
    definition = definition._name.tree_name.get_definition()
    (start_line, start_column) = definition.start_pos
    (end_line, end_column) = definition.end_pos
    return {
        'start': {'line': start_line - 1, 'character': start_column},
        'end': {'line': end_line - 1, 'character': end_column}
    }


def _name_range(definition):
    # Gets the range of symbol name (e.g. function name of a function)
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
    # Don't tend to include parameters as symbols
    # 'param': SymbolKind.Variable,
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
