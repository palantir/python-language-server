import pytest
import pyls.plugins.mypy_lint as plugin
from pyls.workspace import Document

DOC_URI = __file__
DOC_TYPE_ERR = """{}.append(3)
"""
TYPE_ERR_MSG = '"Dict[<nothing>, <nothing>]" has no attribute "append"'

TEST_LINE = 'test_mypy_lint.py:279:8: error: "Request" has no attribute "id"'
TEST_LINE_WITHOUT_COL = ('test_mypy_lint.py:279: '
                         'error: "Request" has no attribute "id"')
TEST_LINE_WITHOUT_LINE = ('test_mypy_lint.py: '
                          'error: "Request" has no attribute "id"')


class FakeConfig(object):
    def plugin_settings(self, plugin, document_path=None):
        return {}


@pytest.fixture
def tmp_workspace(temp_workspace_factory):
    return temp_workspace_factory({
        DOC_URI: DOC_TYPE_ERR
    })


def test_plugin(tmp_workspace):
    config = FakeConfig()
    doc = Document(DOC_URI, tmp_workspace, DOC_TYPE_ERR)
    workspace = tmp_workspace
    diags = plugin.pyls_lint(config, workspace, doc, is_saved=False)

    assert len(diags) == 1
    diag = diags[0]
    assert diag['message'] == TYPE_ERR_MSG
    assert diag['range']['start'] == {'line': 0, 'character': 0}
    assert diag['range']['end'] == {'line': 0, 'character': 1}


def test_parse_full_line(tmp_workspace):
    doc = Document(DOC_URI, tmp_workspace, DOC_TYPE_ERR)
    diag = plugin.parse_line(TEST_LINE, doc)
    assert diag['message'] == '"Request" has no attribute "id"'
    assert diag['range']['start'] == {'line': 278, 'character': 7}
    assert diag['range']['end'] == {'line': 278, 'character': 8}


def test_parse_line_without_col(tmp_workspace):
    doc = Document(DOC_URI, tmp_workspace, DOC_TYPE_ERR)
    diag = plugin.parse_line(TEST_LINE_WITHOUT_COL, doc)
    assert diag['message'] == '"Request" has no attribute "id"'
    assert diag['range']['start'] == {'line': 278, 'character': 0}
    assert diag['range']['end'] == {'line': 278, 'character': 1}


def test_parse_line_without_line(tmp_workspace):
    doc = Document(DOC_URI, tmp_workspace, DOC_TYPE_ERR)
    diag = plugin.parse_line(TEST_LINE_WITHOUT_LINE, doc)
    assert diag['message'] == '"Request" has no attribute "id"'
    assert diag['range']['start'] == {'line': 0, 'character': 0}
    assert diag['range']['end'] == {'line': 0, 'character': 1}


@pytest.mark.parametrize('word,bounds', [('', (7, 8)), ('my_var', (7, 13))])
def test_parse_line_with_context(tmp_workspace, monkeypatch, word, bounds):
    doc = Document(DOC_URI, tmp_workspace, 'DOC_TYPE_ERR')
    monkeypatch.setattr(Document, 'word_at_position', lambda *args: word)
    diag = plugin.parse_line(TEST_LINE, doc)
    assert diag['message'] == '"Request" has no attribute "id"'
    assert diag['range']['start'] == {'line': 278, 'character': bounds[0]}
    assert diag['range']['end'] == {'line': 278, 'character': bounds[1]}
