import pytest

from pyls.workspace import Document
from pyls_mypy import plugin

DOC_URI = __file__
DOC_TYPE_ERR = """{}.append(3)
"""
TYPE_ERR_MSG = '"Dict[<nothing>, <nothing>]" has no attribute "append"'

TEST_LINE = 'main.py:279:8: error: "Request" has no attribute "id"'
TEST_LINE_WITHOUT_COL = 'main.py:279: error: "Request" has no attribute "id"'
TEST_LINE_WITHOUT_LINE = 'main.py: error: "Request" has no attribute "id"'


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
    assert diag['range']['start'] == {'line': 0, 'character': 1}
    assert diag['range']['end'] == {'line': 0, 'character': 2}


def test_parse_full_line():
    diag = plugin.parse_line(TEST_LINE)
    assert diag['message'] == '"Request" has no attribute "id"'
    assert diag['range']['start'] == {'line': 278, 'character': 8}
    assert diag['range']['end'] == {'line': 278, 'character': 9}


def test_parse_line_without_col():
    diag = plugin.parse_line(TEST_LINE_WITHOUT_COL)
    assert diag['message'] == '"Request" has no attribute "id"'
    assert diag['range']['start'] == {'line': 278, 'character': 0}
    assert diag['range']['end'] == {'line': 278, 'character': 1}


def test_parse_line_without_line():
    diag = plugin.parse_line(TEST_LINE_WITHOUT_LINE)
    assert diag['message'] == '"Request" has no attribute "id"'
    assert diag['range']['start'] == {'line': 0, 'character': 0}
    assert diag['range']['end'] == {'line': 0, 'character': 1}


@pytest.mark.parametrize('word,bounds', [('', (8, 9)), ('my_var', (8, 14))])
def test_parse_line_with_context(monkeypatch, word, bounds):
    monkeypatch.setattr(Document, 'word_at_position', lambda *args: word)
    doc = Document('file:///some/path')
    diag = plugin.parse_line(TEST_LINE, doc)
    assert diag['message'] == '"Request" has no attribute "id"'
    assert diag['range']['start'] == {'line': 278, 'character': bounds[0]}
    assert diag['range']['end'] == {'line': 278, 'character': bounds[1]}
