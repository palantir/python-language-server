# Copyright 2017 Palantir Technologies, Inc.
import logging
import re
import sys
from concurrent.futures import ThreadPoolExecutor
import importmagic
from pyls import hookimpl, lsp, _utils


log = logging.getLogger(__name__)

SOURCE = 'importmagic'
ADD_IMPORT_COMMAND = 'importmagic.addimport'
REMOVE_IMPORT_COMMAND = 'importmagic.removeimport'
MAX_COMMANDS = 4
UNRES_RE = re.compile(r"Unresolved import '(?P<unresolved>[\w.]+)'")
UNREF_RE = re.compile(r"Unreferenced import '(?P<unreferenced>[\w.]+)'")

_index_cache = None


def _build_index(paths):
    """Build index of symbols from python modules.
    """
    log.info("Started building importmagic index")
    index = importmagic.SymbolIndex()
    index.build_index(paths=paths)
    log.info("Finished building importmagic index")
    return index


def _cache_index_callback(future):
    global _index_cache
    # Cache the index
    _index_cache = future.result()


def _get_index():
    """Get the cached index if built and index project files on each call.
    Return an empty index if not built yet.
    """
    # Index haven't been built yet
    if _index_cache is None:
        return importmagic.SymbolIndex()

    # Index project files
    # TODO(youben) index project files
    #index.build_index(paths=[])
    return _index_cache


def _get_imports_list(source, index=None):
    """Get modules, functions and variables that are imported.
    """
    if index is None:
        index = importmagic.SymbolIndex()
    imports = importmagic.Imports(index, source)
    imported = [i.name for i in list(imports._imports)]
    # Go over from imports
    for from_import in list(imports._imports_from.values()):
        imported.extend([i.name for i in list(from_import)])
    return imported


@hookimpl
def pyls_initialize():
    pool = ThreadPoolExecutor()
    builder = pool.submit(_build_index, (sys.path))
    builder.add_done_callback(_cache_index_callback)


@hookimpl
def pyls_commands():
    return [ADD_IMPORT_COMMAND, REMOVE_IMPORT_COMMAND]


@hookimpl
def pyls_lint(document):
    """Build a diagnostics of unresolved and unreferenced symbols.
    Every entry follows this format:
        {
            'source': 'importmagic',
            'range': {
                'start': {
                    'line': start_line,
                    'character': start_column,
                },
                'end': {
                    'line': end_line,
                    'character': end_column,
                },
            },
            'message': message_to_be_displayed,
            'severity': sevirity_level,
        }

    Args:
        document: The document to be linted.
    Returns:
        A list of dictionaries.
    """
    scope = importmagic.Scope.from_source(document.source)
    unresolved, unreferenced = scope.find_unresolved_and_unreferenced_symbols()

    diagnostics = []

    # Annoyingly, we only get the text of an unresolved import, so we'll look for it ourselves
    for unres in unresolved:
        for line_no, line in enumerate(document.lines):
            pos = line.find(unres)
            if pos < 0:
                continue

            diagnostics.append({
                'source': SOURCE,
                'range': {
                    'start': {'line': line_no, 'character': pos},
                    'end': {'line': line_no, 'character': pos + len(unres)}
                },
                'message': "Unresolved import '%s'" % unres,
                'severity': lsp.DiagnosticSeverity.Hint,
            })

    for unref in unreferenced:
        for line_no, line in enumerate(document.lines):
            pos = line.find(unref)
            if pos < 0:
                continue

            # Find out if the unref is an import or a variable/func
            imports = _get_imports_list(document.source)
            if unref in imports:
                message = "Unreferenced import '%s'" % unref
            else:
                message = "Unreferenced variable/function '%s'" % unref

            diagnostics.append({
                'source': SOURCE,
                'range': {
                    'start': {'line': line_no, 'character': pos},
                    'end': {'line': line_no, 'character': pos + len(unref)}
                },
                'message': message,
                'severity': lsp.DiagnosticSeverity.Warning,
            })

    return diagnostics


@hookimpl
def pyls_code_actions(config, document):
    """Build a list of actions to be suggested to the user. Each action follow this format:
        {
            'title': 'importmagic',
            'command': command,
            'arguments':
                {
                    'uri': document.uri,
                    'version': document.version,
                    'startLine': start_line,
                    'endLine': end_line,
                    'newText': text,
                }
        }
    """
    # Update the style configuration
    conf = config.plugin_settings('importmagic_lint')
    min_score = conf.get('minScore', 1)
    log.debug("Got importmagic settings: %s", conf)
    importmagic.Imports.set_style(**{_utils.camel_to_underscore(k): v for k, v in conf.items()})

    # Get empty index while it's building so we don't block here
    index = _get_index()
    actions = []

    diagnostics = pyls_lint(document)
    for diagnostic in diagnostics:
        message = diagnostic.get('message', '')
        unref_match = UNREF_RE.match(message)
        unres_match = UNRES_RE.match(message)

        if unref_match:
            unref = unref_match.group('unreferenced')
            actions.append(_generate_remove_action(document, index, unref))
        elif unres_match:
            unres = unres_match.group('unresolved')
            actions.extend(_get_actions_for_unres(document, index, min_score, unres))

    return actions


def _get_actions_for_unres(document, index, min_score, unres):
    """Get the list of possible actions to be applied to solve an unresolved symbol.
    Get a maximun of MAX_COMMANDS actions with the highest score, also filter low score actions
    using the min_score value.
    """
    actions = []
    for score, module, variable in sorted(index.symbol_scores(unres)[:MAX_COMMANDS], reverse=True):
        if score < min_score:
            # Skip low score results
            continue
        actions.append(_generate_add_action(document, index, module, variable))

    return actions


def _generate_add_action(document, index, module, variable):
    """Generate the patch we would need to apply to import a module.
    """
    imports = importmagic.Imports(index, document.source)
    if variable:
        imports.add_import_from(module, variable)
    else:
        imports.add_import(module)
    start_line, end_line, text = imports.get_update()

    action = {
        'title': _add_command_title(variable, module),
        'command': ADD_IMPORT_COMMAND,
        'arguments': [{
            'uri': document.uri,
            'version': document.version,
            'startLine': start_line,
            'endLine': end_line,
            'newText': text
        }]
    }
    return action


def _generate_remove_action(document, index, unref):
    """Generate the patch we would need to apply to remove an import.
    """
    imports = importmagic.Imports(index, document.source)
    imports.remove(unref)
    start_line, end_line, text = imports.get_update()

    action = {
        'title': _remove_command_title(unref),
        'command': REMOVE_IMPORT_COMMAND,
        'arguments': [{
            'uri': document.uri,
            'version': document.version,
            'startLine': start_line,
            'endLine': end_line,
            'newText': text
        }]
    }
    return action


@hookimpl
def pyls_execute_command(workspace, command, arguments):
    if command not in [ADD_IMPORT_COMMAND, REMOVE_IMPORT_COMMAND]:
        return

    args = arguments[0]

    edit = {'documentChanges': [{
        'textDocument': {
            'uri': args['uri'],
            'version': args['version']
        },
        'edits': [{
            'range': {
                'start': {'line': args['startLine'], 'character': 0},
                'end': {'line': args['endLine'], 'character': 0},
            },
            'newText': args['newText']
        }]
    }]}
    workspace.apply_edit(edit)


def _add_command_title(variable, module):
    if not variable:
        return 'Import "%s"' % module
    return 'Import "%s" from "%s"' % (variable, module)


def _remove_command_title(import_name):
    return 'Remove unused import of "%s"' % import_name
