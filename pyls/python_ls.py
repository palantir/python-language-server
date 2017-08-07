import logging
from . import config, lsp, plugins
from .language_server import LanguageServer
from .workspace import Workspace

log = logging.getLogger(__name__)


class PythonLanguageServer(LanguageServer):

    _hooks = None
    workspace = None
    config = None

    def capabilities(self):
        # TODO: support incremental sync instead of full
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
                'commands': flatten(self._hook(self._hooks.pyls_commands))
            },
            'hoverProvider': True,
            'referencesProvider': True,
            'signatureHelpProvider': {
                'triggerCharacters': ['(', ',']
            },
            'textDocumentSync': lsp.TextDocumentSyncKind.INCREMENTAL
        }

    def initialize(self, root_uri, init_opts, _process_id):
        self.workspace = Workspace(root_uri, lang_server=self)
        self.config = config.Config(root_uri, init_opts)

        # Register the base set of plugins
        # TODO(gatesn): Make these configurable in init_opts
        for plugin in plugins.CORE_PLUGINS:
            self.config.plugin_manager.register(plugin)

        # Store a reference to the plugin manager's hook relay to keep things neat
        self._hooks = self.config.plugin_manager.hook

        self._hook(self._hooks.pyls_initialize)

    def _hook(self, hook, doc_uri=None, **kwargs):
        doc = self.workspace.get_document(doc_uri) if doc_uri else None
        return hook(config=self.config, workspace=self.workspace, document=doc, **kwargs)

    def code_actions(self, doc_uri, range, context):
        return flatten(self._hook(self._hooks.pyls_code_actions, doc_uri, range=range, context=context))

    def code_lens(self, doc_uri):
        return flatten(self._hook(self._hooks.pyls_code_lens, doc_uri))

    def completions(self, doc_uri, position):
        completions = self._hook(self._hooks.pyls_completions, doc_uri, position=position)
        return {
            'isIncomplete': False,
            'items': flatten(completions)
        }

    def definitions(self, doc_uri, position):
        return flatten(self._hook(self._hooks.pyls_definitions, doc_uri, position=position))

    def document_symbols(self, doc_uri):
        return flatten(self._hook(self._hooks.pyls_document_symbols, doc_uri))

    def execute_command(self, command, arguments):
        return self._hook(self._hooks.pyls_execute_command, command=command, arguments=arguments)

    def format_document(self, doc_uri):
        return self._hook(self._hooks.pyls_format_document, doc_uri)

    def format_range(self, doc_uri, range):
        return self._hook(self._hooks.pyls_format_range, doc_uri, range=range)

    def hover(self, doc_uri, position):
        return self._hook(self._hooks.pyls_hover, doc_uri, position=position) or {'contents': ''}

    def lint(self, doc_uri):
        self.workspace.publish_diagnostics(doc_uri, flatten(self._hook(
            self._hooks.pyls_lint, doc_uri
        )))

    def references(self, doc_uri, position, exclude_declaration):
        return flatten(self._hook(
            self._hooks.pyls_references, doc_uri, position=position,
            exclude_declaration=exclude_declaration
        ))

    def signature_help(self, doc_uri, position):
        return self._hook(self._hooks.pyls_signature_help, doc_uri, position=position)

    def m_text_document__did_close(self, textDocument=None, **_kwargs):
        self.workspace.rm_document(textDocument['uri'])

    def m_text_document__did_open(self, textDocument=None, **_kwargs):
        self.workspace.put_document(textDocument['uri'], textDocument['text'], version=textDocument.get('version'))
        self._hook(self._hooks.pyls_document_did_open, textDocument['uri'])
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

    def m_text_document__formatting(self, textDocument=None, options=None, **_kwargs):
        # For now we're ignoring formatting options.
        return self.format_document(textDocument['uri'])

    def m_text_document__range_formatting(self, textDocument=None, range=None, options=None, **_kwargs):
        # Again, we'll ignore formatting options for now.
        return self.format_range(textDocument['uri'], range)

    def m_text_document__references(self, textDocument=None, position=None, context=None, **_kwargs):
        exclude_declaration = not context['includeDeclaration']
        return self.references(textDocument['uri'], position, exclude_declaration)

    def m_text_document__signature_help(self, textDocument=None, position=None, **_kwargs):
        return self.signature_help(textDocument['uri'], position)

    def m_workspace__did_change_watched_files(self, **_kwargs):
        pass

    def m_workspace__execute_command(self, command=None, arguments=None):
        return self.execute_command(command, arguments)


def flatten(list_of_lists):
    return [item for lst in list_of_lists for item in lst]
