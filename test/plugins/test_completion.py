# Copyright 2017 Palantir Technologies, Inc.
from distutils.version import LooseVersion
import os
import jedi
import pytest

from pyls import uris, lsp
from pyls.workspace import Document
from pyls.plugins.jedi_completion import pyls_completions as pyls_jedi_completions
from pyls.plugins.rope_completion import pyls_completions as pyls_rope_completions

LOCATION = os.path.realpath(
    os.path.join(os.getcwd(), os.path.dirname(__file__))
)

DOC_URI = uris.from_fs_path(__file__)
DOC = """import os
print os.path.isabs("/tmp")

def hello():
    pass

def _a_hello():
    pass

class Hello():

    @property
    def world(self):
        return None

    def everyone(self, a, b, c=None, d=2):
        pass

print Hello().world

print Hello().every
"""


def test_rope_import_completion(config, workspace):
    com_position = {'line': 0, 'character': 7}
    doc = Document(DOC_URI, DOC)
    items = pyls_rope_completions(config, workspace, doc, com_position)
    assert items is None


@pytest.mark.skipif(LooseVersion(jedi.__version__) < LooseVersion('0.14.0'),
                    reason='This test fails with previous versions of jedi')
def test_jedi_completion(config):
    # Over 'i' in os.path.isabs(...)
    com_position = {'line': 1, 'character': 15}
    doc = Document(DOC_URI, DOC)
    items = pyls_jedi_completions(config, doc, com_position)

    assert items
    assert items[0]['label'] == 'isabs(path)'

    # Test we don't throw with big character
    pyls_jedi_completions(config, doc, {'line': 1, 'character': 1000})


def test_rope_completion(config, workspace):
    # Over 'i' in os.path.isabs(...)
    com_position = {'line': 1, 'character': 15}
    workspace.put_document(DOC_URI, source=DOC)
    doc = workspace.get_document(DOC_URI)
    items = pyls_rope_completions(config, workspace, doc, com_position)

    assert items
    assert items[0]['label'] == 'isabs'


def test_jedi_completion_ordering(config):
    # Over the blank line
    com_position = {'line': 8, 'character': 0}
    doc = Document(DOC_URI, DOC)
    completions = pyls_jedi_completions(config, doc, com_position)

    items = {c['label']: c['sortText'] for c in completions}

    # And that 'hidden' functions come after unhidden ones
    assert items['hello()'] < items['_a_hello()']


def test_jedi_property_completion(config):
    # Over the 'w' in 'print Hello().world'
    com_position = {'line': 18, 'character': 15}
    doc = Document(DOC_URI, DOC)
    completions = pyls_jedi_completions(config, doc, com_position)

    items = {c['label']: c['sortText'] for c in completions}

    # Ensure we can complete the 'world' property
    assert 'world' in list(items.keys())[0]


def test_jedi_method_completion(config):
    # Over the 'y' in 'print Hello().every'
    com_position = {'line': 20, 'character': 19}
    doc = Document(DOC_URI, DOC)

    config.capabilities['textDocument'] = {'completion': {'completionItem': {'snippetSupport': True}}}
    config.update({'plugins': {'jedi_completion': {'include_params': True}}})

    completions = pyls_jedi_completions(config, doc, com_position)
    everyone_method = [completion for completion in completions if completion['label'] == 'everyone(a, b, c, d)'][0]

    # Ensure we only generate snippets for positional args
    assert everyone_method['insertTextFormat'] == lsp.InsertTextFormat.Snippet
    assert everyone_method['insertText'] == 'everyone(${1:a}, ${2:b})$0'

    # Disable param snippets
    config.update({'plugins': {'jedi_completion': {'include_params': False}}})

    completions = pyls_jedi_completions(config, doc, com_position)
    everyone_method = [completion for completion in completions if completion['label'] == 'everyone(a, b, c, d)'][0]

    assert 'insertTextFormat' not in everyone_method
    assert everyone_method['insertText'] == 'everyone'
