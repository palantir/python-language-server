# Copyright 2017 Palantir Technologies, Inc.
import logging
import time
from pyls import hookimpl, lsp, _utils
from contextlib import contextmanager
import signal

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

COMPLETION_CACHE = {}

@contextmanager
def timeout(time):
    # Register a function to raise a TimeoutError on the signal.
    signal.signal(signal.SIGALRM, raise_timeout)
    # Schedule the signal to be sent after ``time``.
    signal.setitimer(signal.SIGALRM, time)

    try:
        yield
    except TimeoutError:
        pass
    finally:
        # Unregister the signal so it won't be triggered
        # if the timeout is not reached.
        signal.signal(signal.SIGALRM, signal.SIG_IGN)


def raise_timeout(signum, frame):
    raise TimeoutError

@hookimpl
def pyls_completions(config, document, position):
    definitions = document.jedi_script(position).completions()
    if not definitions:
        return None

    if len(definitions) > 40:
      definitions = definitions[:40]

    completion_capabilities = config.capabilities.get('textDocument', {}).get('completion', {})
    snippet_support = completion_capabilities.get('completionItem', {}).get('snippetSupport')

    settings = config.plugin_settings('jedi_completion', document_path=document.path)
    should_include_params = settings.get('include_params')

    result = [_format_completion(d, i, snippet_support and should_include_params) for i, d in enumerate(definitions)] or None
    return result

@hookimpl
def pyls_completion_detail(config, item):
    d = COMPLETION_CACHE.get(item)
    if d:
      completion = {
        'label': '', #_label(d),
        'kind': _TYPE_MAP[d.type],
        'detail': '', #_detail(d),
        'documentation': _utils.format_docstring(d.docstring()),
        'sortText': '', #_sort_text(d),
        'insertText': d.name
      }
      return completion
    else:
      print('Completion missing')
      return None

def _format_completion(d, i, include_params=True):
    COMPLETION_CACHE[d.name] = d
    completion = {
        'label': '', #_label(d),
        'kind': '',
        'detail': '', #_detail(d),
        'documentation': _utils.format_docstring(d.docstring()) if i == 0 else '',
        'sortText': '', #_sort_text(d),
        'insertText': d.name
    }
#     if include_params and hasattr(d, 'params') and d.params:
        # positional_args = [param for param in d.params if '=' not in param.description]

        # # For completions with params, we can generate a snippet instead
        # completion['insertTextFormat'] = lsp.InsertTextFormat.Snippet
        # snippet = d.name + '('
        # for i, param in enumerate(positional_args):
            # snippet += '${%s:%s}' % (i + 1, param.name)
            # if i < len(positional_args) - 1:
                # snippet += ', '
        # snippet += ')$0'
        # completion['insertText'] = snippet

    return completion


def _label(definition):
    if definition.type in ('function', 'method') and hasattr(definition, 'params'):
        params = ', '.join([param.name for param in definition.params])
        return '{}({})'.format(definition.name, params)

    return definition.name


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
