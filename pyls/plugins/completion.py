# Copyright 2017 Palantir Technologies, Inc.
import logging
from pyls.lsp import CompletionItemKind
from pyls import hookimpl

from threading import Thread, Lock
from rope.contrib.codeassist import code_assist, sorted_proposals

log = logging.getLogger(__name__)


class CompletionThread(Thread):
    def __init__(self, func):
        Thread.__init__(self)
        self.func = func
        self.finish = False
        self.completions = []
        self.lock = Lock()

    def run(self):
        self.completions = self.func()
        with self.lock:
            self.finish = True


@hookimpl
def pyls_completions(document, position):

    def jedi_closure():
        return document.jedi_script(position).completions()

    def rope_closure():
        offset = document.offset_at_position(position)
        return code_assist(
            document._rope_project, document.source,
            offset, document._rope, maxfixes=3)

    jedi_thread = CompletionThread(jedi_closure)
    rope_thread = CompletionThread(rope_closure)

    jedi_thread.start()
    if document.word_at_position(position) == '.':
        rope_thread.start()

    jedi = False
    definitions = []
    while True:
        with jedi_thread.lock:
            if jedi_thread.finish:
                jedi = True
                definitions = jedi_thread.completions
                break
        with rope_thread.lock:
            if rope_thread.finish:
                jedi = False
                definitions = rope_thread.completions
                break

    if jedi:
        definitions = jedi_thread.completions
        log.debug(type(definitions))
        definitions = [{
            'label': d.name,
            'kind': _kind(d),
            'detail': d.description or "",
            'documentation': d.docstring(),
            'sortText': _sort_text(d)
        } for d in definitions]
    else:
        print(definitions)
        definitions = []
    # definitions = document.jedi_script(position).completions()
    return definitions


def _sort_text(definition):
    """ Ensure builtins appear at the bottom.
    Description is of format <type>: <module>.<item>
    """
    if definition.in_builtin_module():
        # It's a builtin, put it last
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
