# Copyright 2017 Palantir Technologies, Inc.
import logging
import pluggy

from . import hookspecs, plugins, PYLS
from .language_server import LanguageServer
from .lsp import TextDocumentSyncKind

log = logging.getLogger(__name__)


class PythonLanguageServer(LanguageServer):

    def __init__(self, *args, **kwargs):
        # TODO(gatesn): In the future we may need to reconstruct the pm at runtime if configs change
        self._pm = pluggy.PluginManager(PYLS)
        self._pm.trace.root.setwriter(log.debug)
        self._pm.enable_tracing()
        self._pm.add_hookspecs(hookspecs)
        self._pm.load_setuptools_entrypoints(PYLS)
        for plugin in plugins.CORE_PLUGINS:
            self._pm.register(plugin)
        super(PythonLanguageServer, self).__init__(*args, **kwargs)

    def capabilities(self):
        # TODO: support incremental sync instead of full
        return {
            'completionProvider': {
                'resolveProvider': False,  # We know everything ahead of time
                'triggerCharacters': ['.']
            },
            'documentFormattingProvider': True,
            'documentRangeFormattingProvider': True,
            'documentSymbolProvider': True,
            'definitionProvider': True,
            'hoverProvider': True,
            'referencesProvider': True,
            'signatureHelpProvider': {
                'triggerCharacters': ['(', ',']
            },
            'textDocumentSync': TextDocumentSyncKind.FULL
        }

    def _hook(self, hook, doc_uri, **kwargs):
        return hook(workspace=self.workspace, document=self.workspace.get_document(doc_uri), **kwargs)

    def completions(self, doc_uri, position):
        completions = self._hook(self._pm.hook.pyls_completions, doc_uri, position=position)
        return {
            'isIncomplete': False,
            'items': flatten(completions)
        }

    def definitions(self, doc_uri, position):
        return flatten(self._hook(self._pm.hook.pyls_definitions, doc_uri, position=position))

    def document_symbols(self, doc_uri):
        return flatten(self._hook(self._pm.hook.pyls_definitions, doc_uri))

    def format_document(self, doc_uri):
        return self._hook(self._pm.hook.pyls_definitions, doc_uri)

    def format_range(self, doc_uri, range):
        return self._hook(self._pm.hook.pyls_definitions, doc_uri, range=range)

    def hover(self, doc_uri, position):
        return self._hook(self._pm.hook.pyls_hover, doc_uri, position=position) or {'contents': ''}

    def lint(self, doc_uri):
        self.publish_diagnostics(doc_uri, flatten(self._hook(
            self._pm.hook.pyls_lint, doc_uri
        )))

    def references(self, doc_uri, position, exclude_declaration):
        return flatten(self._hook(
            self._pm.hook.pyls_references, doc_uri, position=position,
            exclude_declaration=exclude_declaration
        ))

    def signature_help(self, doc_uri, position):
        return self._hook(self._pm.hook.pyls_signature_help, doc_uri, position=position)

    def m_text_document__did_close(self, textDocument=None, **kwargs):
        self.workspace.rm_document(textDocument['uri'])

    def m_text_document__did_open(self, textDocument=None, **kwargs):
        self.workspace.put_document(textDocument['uri'], textDocument['text'])
        self.lint(textDocument['uri'])

    def m_text_document__did_change(self, contentChanges=None, textDocument=None, **kwargs):
        # Since we're using a FULL document sync, there is only one change containing the whole file
        # TODO: debounce, or should this be someone else's responsibility? Probably
        self.workspace.put_document(textDocument['uri'], contentChanges[0]['text'])
        self.lint(textDocument['uri'])

    def m_text_document__did_save(self, textDocument=None, **kwargs):
        self.lint(textDocument['uri'])

    def m_text_document__completion(self, textDocument=None, position=None, **kwargs):
        return self.completions(textDocument['uri'], position)

    def m_text_document__definition(self, textDocument=None, position=None, **kwarg):
        return self.definitions(textDocument['uri'], position)

    def m_text_document__hover(self, textDocument=None, position=None, **kwargs):
        return self.hover(textDocument['uri'], position)

    def m_text_document__document_symbol(self, textDocument=None, **kwargs):
        return self.document_symbols(textDocument['uri'])

    def m_text_document__formatting(self, textDocument=None, options=None, **kwargs):
        # For now we're ignoring formatting options.
        return self.format_document(textDocument['uri'])

    def m_text_document__range_formatting(self, textDocument=None, range=None, options=None, **kwargs):
        # Again, we'll ignore formatting options for now.
        return self.format_range(textDocument['uri'], range)

    def m_text_document__references(self, textDocument=None, position=None, context=None, **kwargs):
        exclude_declaration = not context['includeDeclaration']
        return self.references(textDocument['uri'], position, exclude_declaration)

    def m_text_document__signature_help(self, textDocument=None, position=None, **kwargs):
        return self.signature_help(textDocument['uri'], position)

    def m_workspace__did_change_watched_files(self, **kwargs):
        pass


def flatten(list_of_lists):
    return [item for lst in list_of_lists for item in lst]
