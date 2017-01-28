# Copyright 2017 Palantir Technologies, Inc.
import logging
from .language_server import LanguageServer

from .providers.completion import JediCompletionProvider
from .providers.definition import JediDefinitionsProvider
from .providers.format import YapfFormatter
from .providers.lint import PyCodeStyleLinter, PyflakesLinter
from .providers.hover import JediDocStringHoverProvider
from .providers.references import JediReferencesProvider
from .providers.signature import JediSignatureProvider
from .providers.symbols import JediDocumentSymbolsProvider
from .vscode import TextDocumentSyncKind

log = logging.getLogger(__name__)


class PythonLanguageServer(LanguageServer):

    # Providers for different things and config chooses which one

    COMPLETION = JediCompletionProvider
    DEFINITIONS = JediDefinitionsProvider
    DOCUMENT_FORMATTER = YapfFormatter
    DOCUMENT_SYMBOLS = JediDocumentSymbolsProvider
    HOVER = JediDocStringHoverProvider
    LINTERS = [PyCodeStyleLinter, PyflakesLinter]
    RANGE_FORMATTER = YapfFormatter
    REFERENCES = JediReferencesProvider
    SIGNATURE = JediSignatureProvider

    def __init__(self, *args, **kwargs):
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
                'triggerCharacters': ['(']
            },
            'textDocumentSync': TextDocumentSyncKind.FULL
        }

    def completions(self, doc_uri, position):
        return self.COMPLETION(self.workspace).run(doc_uri, position)

    def definitions(self, doc_uri, position):
        return self.DEFINITIONS(self.workspace).run(doc_uri, position)

    def document_symbols(self, doc_uri):
        return self.DOCUMENT_SYMBOLS(self.workspace).run(doc_uri)

    def format_document(self, doc_uri):
        return self.DOCUMENT_FORMATTER(self.workspace).run(doc_uri)

    def format_range(self, doc_uri, range):
        return self.RANGE_FORMATTER(self.workspace).run(doc_uri, range)

    def hover(self, doc_uri, position):
        return self.HOVER(self.workspace).run(doc_uri, position) or {'contents': ''}

    def lint(self, doc_uri):
        diagnostics = []
        for linter in self.LINTERS:
            # TODO: combine results from all linters and dedup
            diagnostics.extend(linter(self.workspace).run(doc_uri))
        self.publish_diagnostics(doc_uri, diagnostics)

    def references(self, doc_uri, position, exclude_declaration):
        return self.REFERENCES(self.workspace).run(doc_uri, position, exclude_declaration)

    def signature_help(self, doc_uri, position):
        return self.SIGNATURE(self.workspace).run(doc_uri, position)

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
