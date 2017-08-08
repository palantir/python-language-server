from pyls.workspace import Document
from pyls_mypy import plugin

DOC_URI = __file__
DOC_TYPE_ERR = """{}.append(3)
"""

TEST_LINE = 'main.py:279:8: error: "Request" has no attribute "id"'
TEST_LINE_WITHOUT_COL = 'main.py:279: error: "Request" has no attribute "id"'
TEST_LINE_WITHOUT_LINE = 'main.py: error: "Request" has no attribute "id"'


def test_plugin():
    doc = Document(DOC_URI, DOC_TYPE_ERR)
    diags = plugin.pyls_lint(doc)

    assert len(diags) == 1
    diag = diags[0]
    assert diag['message'] == 'Dict[<nothing>, <nothing>] has no attribute "append"'
    assert diag['range']['start'] == {'line': 0, 'character': 0}
    assert diag['range']['end'] == {'line': 0, 'character': 1}


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
