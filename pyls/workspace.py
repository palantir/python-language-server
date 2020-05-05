# Copyright 2017 Palantir Technologies, Inc.
import io
import logging
import os
import re
import time
import queue
import inspect
import threading

import jedi

from . import lsp, uris, _utils

log = logging.getLogger(__name__)

# TODO: this is not the best e.g. we capture numbers
RE_START_WORD = re.compile('[A-Za-z_0-9]*$')
RE_END_WORD = re.compile('^[A-Za-z_0-9]*')


class Workspace(object):

    M_PUBLISH_DIAGNOSTICS = 'textDocument/publishDiagnostics'
    M_APPLY_EDIT = 'workspace/applyEdit'
    M_SHOW_MESSAGE = 'window/showMessage'

    def __init__(self, root_uri, endpoint, config=None):
        self._config = config
        self._root_uri = root_uri
        self._endpoint = endpoint
        self._root_uri_scheme = uris.urlparse(self._root_uri)[0]
        self._root_path = uris.to_fs_path(self._root_uri)
        self._docs = {}

        # Cache jedi environments
        self._environments = {}

        # Whilst incubating, keep rope private
        self.__rope = None
        self.__rope_config = None

    def rope_project_builder(self, rope_config):
        from rope.base.project import Project

        # TODO: we could keep track of dirty files and validate only those
        if self.__rope is None or self.__rope_config != rope_config:
            rope_folder = rope_config.get('ropeFolder')
            self.__rope = Project(self._root_path, ropefolder=rope_folder)
            self.__rope.prefs.set('extension_modules', rope_config.get('extensionModules', []))
            self.__rope.prefs.set('ignore_syntax_errors', True)
            self.__rope.prefs.set('ignore_bad_imports', True)
        self.__rope.validate()
        return self.__rope

    @property
    def documents(self):
        return self._docs

    @property
    def root_path(self):
        return self._root_path

    @property
    def root_uri(self):
        return self._root_uri

    def is_local(self):
        return (self._root_uri_scheme == '' or self._root_uri_scheme == 'file') and os.path.exists(self._root_path)

    def get_document(self, doc_uri):
        """Return a managed document if-present, else create one pointing at disk.

        See https://github.com/Microsoft/language-server-protocol/issues/177
        """
        doc = self._docs.get(doc_uri)
        if doc is None:
            doc = self._create_document(doc_uri)
            self._docs[doc_uri] = doc
        return doc

    def put_document(self, doc_uri, source, version=None):
        self._docs[doc_uri] = self._create_document(doc_uri, source=source, version=version)

    def rm_document(self, doc_uri):
        doc = self._docs.pop(doc_uri)
        doc.stop()

    def close_all_documents(self):
        documents = list(self._docs.keys())
        for uri in documents:
            doc = self._docs.pop(uri)
            doc.stop()

    def update_document(self, doc_uri, change, version=None):
        self._docs[doc_uri].apply_change(change, version)

    def update_config(self, config):
        self._config = config
        for doc_uri in self.documents:
            self.get_document(doc_uri).update_config(config)

    def apply_edit(self, edit):
        return self._endpoint.request(self.M_APPLY_EDIT, {'edit': edit})

    def publish_diagnostics(self, doc_uri, diagnostics):
        self._endpoint.notify(self.M_PUBLISH_DIAGNOSTICS, params={'uri': doc_uri, 'diagnostics': diagnostics})

    def show_message(self, message, msg_type=lsp.MessageType.Info):
        self._endpoint.notify(self.M_SHOW_MESSAGE, params={'type': msg_type, 'message': message})

    def source_roots(self, document_path):
        """Return the source roots for the given document."""
        files = _utils.find_parents(self._root_path, document_path, ['setup.py', 'pyproject.toml']) or []
        return list(set((os.path.dirname(project_file) for project_file in files))) or [self._root_path]

    def _create_document(self, doc_uri, source=None, version=None):
        path = uris.to_fs_path(doc_uri)
        return Document(
            doc_uri, source=source, version=version,
            extra_sys_path=self.source_roots(path),
            rope_project_builder=self.rope_project_builder,
            config=self._config, workspace=self,
        )


def find_methods_properties(cls):
    """Class decorator that extracts class methods and properties."""
    methods = []
    properties = []
    for member_name in dir(cls):
        if not member_name.startswith('_'):
            member = getattr(cls, member_name)
            if inspect.isfunction(member):
                methods.append(member_name)
            else:
                properties.append(member_name)
    cls.method_registry = frozenset(methods)
    cls.property_registry = frozenset(properties + ['_source'])
    return cls


class DocumentCallWrapper:
    def __init__(self, name, *args, **kwargs):
        self.resolved = False
        self.response = None
        self.cancelled = False
        self.args = args
        self.kwargs = kwargs
        self.name = name


class Document(object):
    """Send concurrent requests to a Document."""

    TIMEOUT = 5000
    LOCAL = {'properties', 'methods', 'stop', 'uri', 'agent', 'sequence'}

    def __init__(self, uri, source=None, version=None, local=True,
                 extra_sys_path=None, rope_project_builder=None,
                 config=None, workspace=None):
        self.uri = uri
        self.sequence = 1
        self.request_queue = queue.PriorityQueue()
        self.agent = DocumentAgent(self.request_queue, uri, source,
                                   version, local, extra_sys_path,
                                   rope_project_builder, config, workspace)
        self.properties = self.agent.properties
        self.methods = self.agent.methods
        self.agent.start()

    def stop(self):
        # self.agent.stop()
        shutdown = DocumentCallWrapper('shutdown')
        self.request_queue.put((0, shutdown))
        # self.request_queue.join()
        self.agent.join()
        self.agent = None
        self.request_queue = None

    def __str__(self):
        return str(self.uri)

    def __getattr__(self, attr):
        if attr not in self.LOCAL:
            def queue_call(*args, **kwargs):
                call_item = DocumentCallWrapper(attr, *args, **kwargs)
                self.request_queue.put((self.sequence, call_item))
                self.sequence += 1
                start_time = time.time()
                while (not call_item.resolved and
                        (start_time - time.time()) < self.TIMEOUT):
                    continue
                if not call_item.resolved:
                    call_item.cancelled = True
                response = call_item.response
                if isinstance(response, Exception):
                    raise response
                return response

            if attr in self.properties:
                return queue_call()
            elif attr in self.methods:
                return queue_call
            else:
                super(Document, self).__getattribute__(attr)
        else:
            super(Document, self).__getattribute__(attr)


class DocumentAgent(threading.Thread):
    """Handle concurrent requests to a Document."""

    def __init__(self, queue, uri, source=None, version=None, local=True,
                 extra_sys_path=None, rope_project_builder=None,
                 config=None, workspace=None):
        self.document = _Document(uri, source, version, local, extra_sys_path,
                                  rope_project_builder, config, workspace)
        self.queue = queue
        self.stopped = False
        super(DocumentAgent, self).__init__()

    @property
    def methods(self):
        return self.document.method_registry

    @property
    def properties(self):
        return self.document.property_registry

    def run(self):
        while True:
            (_, item) = self.queue.get()
            self.queue.task_done()
            if item.name == 'shutdown':
                break
            if item.cancelled:
                continue
            try:
                attr = getattr(self.document, item.name)
                result = attr
                if inspect.ismethod(attr):
                    result = attr(*item.args, **item.kwargs)
                item.response = result
                item.resolved = True
            except Exception as e:
                import traceback
                traceback.print_exc()
                item.response = e
        self.document = None
        while not self.queue.empty():
            item = self.queue.get()
            item.response = None
            item.resolved = True
            self.queue.task_done()
        self.queue = None


@find_methods_properties
class _Document(object):

    def __init__(self, uri, source=None, version=None, local=True, extra_sys_path=None, rope_project_builder=None,
                 config=None, workspace=None):
        self._uri = uri
        self._version = version
        self._path = uris.to_fs_path(uri)
        self._filename = os.path.basename(self.path)

        self._config = config
        self._workspace = workspace
        self._local = local
        self._source = source
        self._extra_sys_path = extra_sys_path or []
        self._rope_project_builder = rope_project_builder

    def __str__(self):
        return str(self.uri)

    def rope_resource(self, rope_config):
        from rope.base import libutils
        return libutils.path_to_resource(self._rope_project_builder(rope_config), self.path)

    @property
    def uri(self):
        return self._uri

    @property
    def version(self):
        return self._version

    @property
    def path(self):
        return self._path

    @property
    def filename(self):
        return self._filename

    @property
    def lines(self):
        return self.source.splitlines(True)

    @property
    def source(self):
        if self._source is None:
            with io.open(self.path, 'r', encoding='utf-8') as f:
                return f.read()
        return self._source

    def update_config(self, config):
        self._config = config

    def apply_change(self, change, version):
        """Apply a change to the document."""
        self._version = version
        text = change['text']
        change_range = change.get('range')

        if not change_range:
            # The whole file has changed
            self._source = text
            return

        start_line = change_range['start']['line']
        start_col = change_range['start']['character']
        end_line = change_range['end']['line']
        end_col = change_range['end']['character']

        # Check for an edit occuring at the very end of the file
        if start_line == len(self.lines):
            self._source = self.source + text
            return

        new = io.StringIO()

        # Iterate over the existing document until we hit the edit range,
        # at which point we write the new text, then loop until we hit
        # the end of the range and continue writing.
        for i, line in enumerate(self.lines):
            if i < start_line:
                new.write(line)
                continue

            if i > end_line:
                new.write(line)
                continue

            if i == start_line:
                new.write(line[:start_col])
                new.write(text)

            if i == end_line:
                new.write(line[end_col:])

        self._source = new.getvalue()

    def offset_at_position(self, position):
        """Return the byte-offset pointed at by the given position."""
        return position['character'] + len(''.join(self.lines[:position['line']]))

    def word_at_position(self, position):
        """Get the word under the cursor returning the start and end positions."""
        if position['line'] >= len(self.lines):
            return ''

        line = self.lines[position['line']]
        i = position['character']
        # Split word in two
        start = line[:i]
        end = line[i:]

        # Take end of start and start of end to find word
        # These are guaranteed to match, even if they match the empty string
        m_start = RE_START_WORD.findall(start)
        m_end = RE_END_WORD.findall(end)

        return m_start[0] + m_end[-1]

    def jedi_names(self, all_scopes=False, definitions=True, references=False):
        environment_path = None
        if self._config:
            jedi_settings = self._config.plugin_settings('jedi', document_path=self.path)
            environment_path = jedi_settings.get('environment')
        environment = self.get_enviroment(environment_path) if environment_path else None

        return jedi.api.names(
            source=self.source, path=self.path, all_scopes=all_scopes,
            definitions=definitions, references=references, environment=environment,
        )

    def jedi_script(self, position=None):
        extra_paths = []
        environment_path = None

        if self._config:
            jedi_settings = self._config.plugin_settings('jedi', document_path=self.path)
            environment_path = jedi_settings.get('environment')
            extra_paths = jedi_settings.get('extra_paths') or []

        sys_path = self.sys_path(environment_path) + extra_paths
        environment = self.get_enviroment(environment_path) if environment_path else None

        kwargs = {
            'source': self.source,
            'path': self.path,
            'sys_path': sys_path,
            'environment': environment,
        }

        if position:
            kwargs['line'] = position['line'] + 1
            kwargs['column'] = _utils.clip_column(position['character'], self.lines, position['line'])

        return jedi.Script(**kwargs)

    def get_enviroment(self, environment_path=None):
        # TODO(gatesn): #339 - make better use of jedi environments, they seem pretty powerful
        if environment_path is None:
            environment = jedi.api.environment.get_cached_default_environment()
        else:
            if environment_path in self._workspace._environments:
                environment = self._workspace._environments[environment_path]
            else:
                environment = jedi.api.environment.create_environment(path=environment_path, safe=False)
                self._workspace._environments[environment_path] = environment

        return environment

    def sys_path(self, environment_path=None):
        # Copy our extra sys path
        path = list(self._extra_sys_path)
        environment = self.get_enviroment(environment_path=environment_path)
        path.extend(environment.get_sys_path())
        return path
