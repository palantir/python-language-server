# Copyright 2017 Palantir Technologies, Inc.
import logging
from multiprocessing import dummy as multiprocessing
from . import lsp, _utils
from .config import config
from .language_server import LanguageServer
from .workspace import Workspace

log = logging.getLogger(__name__)

PLUGGY_RACE_POOL_SIZE = 5
LINT_DEBOUNCE_S = 0.5  # 500 ms


class PythonLanguageServer(LanguageServer):
    # pylint: disable=too-many-public-methods,redefined-builtin

    workspace = None
    config = None

    _pool = multiprocessing.Pool(PLUGGY_RACE_POOL_SIZE)

    def _hook_caller(self, hook_name):
        return self.config.plugin_manager.subset_hook_caller(hook_name, self.config.disabled_plugins)

    def _hook(self, hook_name, doc_uri=None, **kwargs):
        doc = self.workspace.get_document(doc_uri) if doc_uri else None
        return self._hook_caller(hook_name)(config=self.config, workspace=self.workspace, document=doc, **kwargs)

    def capabilities(self):
        return {
            'codeActionProvider': True,
            'codeLensProvider': {
                'resolveProvider': False,  # We may need to make this configurable
            },
            'completionProvider': {
                'resolveProvider': False,  # We know everything ahead of time
                'triggerCharacters': ['.']
            },
            'documentFormattingProvider': True,
            'documentRangeFormattingProvider': True,
            'documentSymbolProvider': True,
            'definitionProvider': True,
            'executeCommandProvider': {
                'commands': flatten(self._hook('pyls_commands'))
            },
            'hoverProvider': True,
            'referencesProvider': True,
            'renameProvider': True,
            'signatureHelpProvider': {
                'triggerCharacters': ['(', ',']
            },
            'textDocumentSync': lsp.TextDocumentSyncKind.INCREMENTAL
        }

    def initialize(self, root_uri, init_opts, _process_id):
        self.workspace = Workspace(root_uri, lang_server=self)
        self.config = config.Config(root_uri, init_opts)
        self._hook('pyls_initialize')

    def code_actions(self, doc_uri, range, context):
        return flatten(self._hook('pyls_code_actions', doc_uri, range=range, context=context))

    def code_lens(self, doc_uri):
        return flatten(self._hook('pyls_code_lens', doc_uri))

    def completions(self, doc_uri, position):
        completions = _utils.race_hooks(
            self._hook_caller('pyls_completions'), self._pool,
            document=self.workspace.get_document(doc_uri) if doc_uri else None,
            position=position
        )
        return {
            'isIncomplete': False,
            'items': completions or []
        }

    def definitions(self, doc_uri, position):
        return flatten(self._hook('pyls_definitions', doc_uri, position=position))

    def document_symbols(self, doc_uri):
        return flatten(self._hook('pyls_document_symbols', doc_uri))

    def execute_command(self, command, arguments):
        return self._hook('pyls_execute_command', command=command, arguments=arguments)

    def format_document(self, doc_uri):
        return self._hook('pyls_format_document', doc_uri)

    def format_range(self, doc_uri, range):
        return self._hook('pyls_format_range', doc_uri, range=range)

    def hover(self, doc_uri, position):
        return self._hook('pyls_hover', doc_uri, position=position) or {'contents': ''}

    @_utils.debounce(LINT_DEBOUNCE_S)
    def lint(self, doc_uri):
        # Since we're debounced, the document may no longer be open
        if doc_uri in self.workspace.documents:
            self.workspace.publish_diagnostics(doc_uri, flatten(self._hook('pyls_lint', doc_uri)))

    def references(self, doc_uri, position, exclude_declaration):
        return flatten(self._hook(
            'pyls_references', doc_uri, position=position,
            exclude_declaration=exclude_declaration
        ))

    def rename(self, doc_uri, position, new_name):
        return self._hook('pyls_rename', doc_uri, position=position, new_name=new_name)

    def signature_help(self, doc_uri, position):
        return self._hook('pyls_signature_help', doc_uri, position=position)

    def m_text_document__did_close(self, textDocument=None, **_kwargs):
        self.workspace.rm_document(textDocument['uri'])

    def m_text_document__did_open(self, textDocument=None, **_kwargs):
        self.workspace.put_document(textDocument['uri'], textDocument['text'], version=textDocument.get('version'))
        self._hook('pyls_document_did_open', textDocument['uri'])
        self.lint(textDocument['uri'])

    def m_text_document__did_change(self, contentChanges=None, textDocument=None, **_kwargs):
        for change in contentChanges:
            self.workspace.update_document(
                textDocument['uri'],
                change,
                version=textDocument.get('version')
            )
        self.lint(textDocument['uri'])

    def m_text_document__did_save(self, textDocument=None, **_kwargs):
        self.lint(textDocument['uri'])

    def m_text_document__code_action(self, textDocument=None, range=None, context=None, **_kwargs):
        return self.code_actions(textDocument['uri'], range, context)

    def m_text_document__code_lens(self, textDocument=None, **_kwargs):
        return self.code_lens(textDocument['uri'])

    def m_text_document__completion(self, textDocument=None, position=None, **_kwargs):
        return self.completions(textDocument['uri'], position)

    def m_text_document__definition(self, textDocument=None, position=None, **_kwargs):
        return self.definitions(textDocument['uri'], position)

    def m_text_document__hover(self, textDocument=None, position=None, **_kwargs):
        return self.hover(textDocument['uri'], position)

    def m_text_document__document_symbol(self, textDocument=None, **_kwargs):
        return self.document_symbols(textDocument['uri'])

    def m_text_document__formatting(self, textDocument=None, _options=None, **_kwargs):
        # For now we're ignoring formatting options.
        return self.format_document(textDocument['uri'])

    def m_text_document__rename(self, textDocument=None, position=None, newName=None, **_kwargs):
        return self.rename(textDocument['uri'], position, newName)

    def m_text_document__range_formatting(self, textDocument=None, range=None, _options=None, **_kwargs):
        # Again, we'll ignore formatting options for now.
        return self.format_range(textDocument['uri'], range)

    def m_text_document__references(self, textDocument=None, position=None, context=None, **_kwargs):
        exclude_declaration = not context['includeDeclaration']
        return self.references(textDocument['uri'], position, exclude_declaration)

    def m_text_document__signature_help(self, textDocument=None, position=None, **_kwargs):
        return self.signature_help(textDocument['uri'], position)

    def m_workspace__did_change_configuration(self, settings=None):
        self.config.update((settings or {}).get('pyls', {}))
        for doc_uri in self.workspace.documents:
            self.lint(doc_uri)

    def m_workspace__did_change_watched_files(self, **_kwargs):
        # Externally changed files may result in changed diagnostics
        for doc_uri in self.workspace.documents:
            self.lint(doc_uri)

    def m_workspace__execute_command(self, command=None, arguments=None):
        return self.execute_command(command, arguments)


def flatten(list_of_lists):
    return [item for lst in list_of_lists for item in lst]
