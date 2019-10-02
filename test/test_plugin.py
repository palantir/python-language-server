import pytest

from pyls.workspace import Document
from pyls_mypy import plugin

DOC_URI = __file__
DOC_TYPE_ERR = """{}.append(3)
"""
TYPE_ERR_MSG = '"Dict[<nothing>, <nothing>]" has no attribute "append"'

TEST_LINE = 'test_plugin.py:279:8: error: "Request" has no attribute "id"'
TEST_LINE_WITHOUT_COL = ('test_plugin.py:279: '
                         'error: "Request" has no attribute "id"')
TEST_LINE_WITHOUT_LINE = ('test_plugin.py: '
                          'error: "Request" has no attribute "id"')


class FakeConfig(object):
    def plugin_settings(self, plugin, document_path=None):
        return {}


def test_plugin():
    config = FakeConfig()
    doc = Document(DOC_URI, DOC_TYPE_ERR)
    diags = plugin.pyls_lint(config, doc)

    assert len(diags) == 1
    diag = diags[0]
    assert diag['message'] == TYPE_ERR_MSG
    assert diag['range']['start'] == {'line': 0, 'character': 0}
    assert diag['range']['end'] == {'line': 0, 'character': 1}


def test_parse_full_line():
    doc = Document(DOC_URI, DOC_TYPE_ERR)
    diag = plugin.parse_line(TEST_LINE, doc)
    assert diag['message'] == '"Request" has no attribute "id"'
    assert diag['range']['start'] == {'line': 278, 'character': 7}
    assert diag['range']['end'] == {'line': 278, 'character': 8}


def test_parse_line_without_col():
    doc = Document(DOC_URI, DOC_TYPE_ERR)
    diag = plugin.parse_line(TEST_LINE_WITHOUT_COL, doc)
    assert diag['message'] == '"Request" has no attribute "id"'
    assert diag['range']['start'] == {'line': 278, 'character': 0}
    assert diag['range']['end'] == {'line': 278, 'character': 1}


def test_parse_line_without_line():
    doc = Document(DOC_URI, DOC_TYPE_ERR)
    diag = plugin.parse_line(TEST_LINE_WITHOUT_LINE, doc)
    assert diag['message'] == '"Request" has no attribute "id"'
    assert diag['range']['start'] == {'line': 0, 'character': 0}
    assert diag['range']['end'] == {'line': 0, 'character': 1}


@pytest.mark.parametrize('word,bounds', [('', (7, 8)), ('my_var', (7, 13))])
def test_parse_line_with_context(monkeypatch, word, bounds):
    doc = Document(DOC_URI, 'DOC_TYPE_ERR')
    monkeypatch.setattr(Document, 'word_at_position', lambda *args: word)
    diag = plugin.parse_line(TEST_LINE, doc)
    assert diag['message'] == '"Request" has no attribute "id"'
    assert diag['range']['start'] == {'line': 278, 'character': bounds[0]}
    assert diag['range']['end'] == {'line': 278, 'character': bounds[1]}
