# Copyright 2017 Palantir Technologies, Inc.
import logging
import re
import importmagic
from pyls import hookimpl, lsp

log = logging.getLogger(__name__)

SOURCE = 'importmagic'
ADD_IMPORT_COMMAND = 'importmagic/addimport'
MAX_COMMANDS = 4
UNRES_RE = re.compile("Unresolved import '(?P<unresolved>[\w.]+)'")

_index_cache = {}


def _get_index(sys_path):
    key = tuple(sys_path)
    if key not in _index_cache:
        index = importmagic.SymbolIndex()
        index.build_index(paths=sys_path)
        _index_cache[key] = index
    return _index_cache[key]


@hookimpl
def pyls_commands():
    return [ADD_IMPORT_COMMAND]


@hookimpl
def pyls_lint(document):
    scope = importmagic.Scope.from_source(document.source)
    unresolved, _unreferenced = scope.find_unresolved_and_unreferenced_symbols()

    diagnostics = []

    # Annoyingly, we only get the text of an unresolved import, so we'll look for it ourselves
    for unres in unresolved:
        if unres not in document.source:
            continue

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
                'severity': lsp.DiagnosticSeverity.Error,
            })

    return diagnostics


@hookimpl
def pyls_code_actions(workspace, document, context):
    actions = []
    diagnostics = context.get('diagnostics', [])
    for diagnostic in diagnostics:
        if diagnostic.get('source') != SOURCE:
            continue
        m = UNRES_RE.match(diagnostic['message'])
        if not m:
            continue

        unres = m.group('unresolved')
        index = _get_index(workspace.syspath_for_path(document.path))

        for score, module, variable in sorted(index.symbol_scores(unres)[:MAX_COMMANDS], reverse=True):
            if score < 1:
                # These tend to be terrible
                continue

            actions.append({
                'title': _command_title(variable, module),
                'command': ADD_IMPORT_COMMAND,
                'arguments': {
                    'unresolved': unres,
                    'module': module,
                    'variable': variable,
                    'score': score
                }
            })
    return actions


def _command_title(variable, module):
    if not variable:
        return 'Import %s' % module
    return 'Import %s from %s' % (variable, module)
