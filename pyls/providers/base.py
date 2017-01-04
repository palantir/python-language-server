# Copyright 2017 Palantir Technologies, Inc.
import os
import jedi
import sys


class BaseProvider(object):

    def __init__(self, workspace):
        self.workspace = workspace

    def run(self, *args, **kwargs):
        raise NotImplementedError()  # pragma: no cover


class JediProvider(BaseProvider):

    def jedi_names(self, doc_uri):
        document = self.workspace.get_document(doc_uri)
        return jedi.api.names(source=document.source)

    def jedi_script(self, doc_uri, position=None):
        document = self.workspace.get_document(doc_uri)

        path = None
        sys_path = list(sys.path)  # TODO Load from config

        # If we're local, we can add ourselves to Python path and do clevererer things
        if self.workspace.is_local():
            sys_path.insert(0, self.workspace.root)
            if os.path.exists(document.path):
                path = document.path

        kwargs = {
            'source': document.source,
            'path': path,
            'sys_path': sys_path
        }

        if position:
            kwargs['line'] = position['line'] + 1
            kwargs['column'] = position['character']

        return jedi.Script(**kwargs)
