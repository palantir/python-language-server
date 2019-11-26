# Copyright 2017 Palantir Technologies, Inc.
import logging
from itertools import chain
import parso
from pyls import hookimpl, lsp, _utils

log = logging.getLogger(__name__)

# Map to the VSCode type
_TYPE_MAP = {
    'none': lsp.CompletionItemKind.Value,
    'type': lsp.CompletionItemKind.Class,
    'tuple': lsp.CompletionItemKind.Class,
    'dict': lsp.CompletionItemKind.Class,
    'dictionary': lsp.CompletionItemKind.Class,
    'function': lsp.CompletionItemKind.Function,
    'lambda': lsp.CompletionItemKind.Function,
    'generator': lsp.CompletionItemKind.Function,
    'class': lsp.CompletionItemKind.Class,
    'instance': lsp.CompletionItemKind.Reference,
    'method': lsp.CompletionItemKind.Method,
    'builtin': lsp.CompletionItemKind.Class,
    'builtinfunction': lsp.CompletionItemKind.Function,
    'module': lsp.CompletionItemKind.Module,
    'file': lsp.CompletionItemKind.File,
    'xrange': lsp.CompletionItemKind.Class,
    'slice': lsp.CompletionItemKind.Class,
    'traceback': lsp.CompletionItemKind.Class,
    'frame': lsp.CompletionItemKind.Class,
    'buffer': lsp.CompletionItemKind.Class,
    'dictproxy': lsp.CompletionItemKind.Class,
    'funcdef': lsp.CompletionItemKind.Function,
    'property': lsp.CompletionItemKind.Property,
    'import': lsp.CompletionItemKind.Module,
    'keyword': lsp.CompletionItemKind.Keyword,
    'constant': lsp.CompletionItemKind.Variable,
    'variable': lsp.CompletionItemKind.Variable,
    'value': lsp.CompletionItemKind.Value,
    'param': lsp.CompletionItemKind.Variable,
    'statement': lsp.CompletionItemKind.Keyword,
}

# Types of parso nodes for which snippet is not included in the completion
_IMPORTS = ('import_name', 'import_from')


@hookimpl
def pyls_completions(config, document, position):
    definitions = document.jedi_script(position).completions()
    if not definitions:
        return None

    completion_capabilities = config.capabilities.get('textDocument', {}).get('completion', {})
    snippet_support = completion_capabilities.get('completionItem', {}).get('snippetSupport')

    settings = config.plugin_settings('jedi_completion', document_path=document.path)
    should_include_params = settings.get('include_params')
    include_params = (snippet_support and should_include_params and
                      use_snippets(document, position))

    return list(chain.from_iterable(_format_completions(d, include_params) for d in definitions))


def use_snippets(document, position):
    """
    Determine if it's necessary to return snippets in code completions.

    This returns `False` if a completion is being requested on an import
    statement, `True` otherwise.
    """
    line = position['line']
    lines = document.source.split('\n', line)
    act_lines = [lines[line][:position['character']]]
    line -= 1
    while line > -1:
        act_line = lines[line]
        if act_line.rstrip().endswith('\\'):
            act_lines.insert(0, act_line)
            line -= 1
        else:
            break
    tokens = parso.parse('\n'.join(act_lines).split(';')[-1].strip())
    return tokens.children[0].type not in _IMPORTS


def _format_completions(d, include_params):
    yield _format_completion(d, False)
    if hasattr(d, 'params'):
        yield _format_completion(d, True)


def _format_completion(d, include_params):
    completion = {
        'label': d.name,
        'kind': _TYPE_MAP.get(d.type),
        'detail': _detail(d),
        'documentation': _utils.format_docstring(d.docstring()),
        'sortText': _sort_text(d),
        'insertText': d.name
    }

    if include_params:
        # For completions with params, we can generate a snippet instead

        def fix_name(name):
            return '\\/' if name == '/' else name

        names = [fix_name(param.name) for param in d.params if '=' not in param.description]
        snippets = ('${{{}:{}}}'.format(i + 1, p) for i, p in enumerate(names))
        completion.update(
            insertTextFormat=lsp.InsertTextFormat.Snippet,
            label='{}({})'.format(d.name, ', '.join(names)),
            insertText='{}({})$0'.format(d.name, ', '.join(snippets))
        )

    return completion


def _detail(definition):
    try:
        return definition.parent().full_name or ''
    except AttributeError:
        return definition.full_name or ''


def _sort_text(definition):
    """ Ensure builtins appear at the bottom.
    Description is of format <type>: <module>.<item>
    """

    # If its 'hidden', put it next last
    prefix = 'z{}' if definition.name.startswith('_') else 'a{}'
    return prefix.format(definition.name)
