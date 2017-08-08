from pyls.workspace import Document
from pyls_mypy import plugin

DOC_URI = __file__
DOC_TYPE_ERR = """{}.append(3)
"""

def test_plugin():
    doc = Document(DOC_URI, DOC_TYPE_ERR)
    diags = plugin.pyls_lint(doc)

    assert len(diags) == 1
    diag = diags[0]
    assert diag['message'] == 'Dict[<nothing>, <nothing>] has no attribute "append"'
    assert diag['range']['start'] == {'line': 0, 'character': 0}
    assert diag['range']['end'] == {'line': 0, 'character': 1}
