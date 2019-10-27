# Copyright 2017 Palantir Technologies, Inc.
from distutils.version import LooseVersion

from pyls import uris, _utils
from pyls.plugins.hover import pyls_hover
from pyls.workspace import Document

DOC_URI = uris.from_fs_path(__file__)
DOC = """

def main():
    \"\"\"hello world\"\"\"
    pass
"""


def test_hover():
    # Over 'main' in def main():
    hov_position = {'line': 2, 'character': 6}
    # Over the blank second line
    no_hov_position = {'line': 1, 'character': 0}

    doc = Document(DOC_URI, DOC)

    if LooseVersion(_utils.JEDI_VERSION) >= LooseVersion('0.15.0'):
        contents = [{'language': 'python', 'value': 'main()'}, 'hello world']
    else:
        contents = 'main()\n\nhello world'

    assert {
        'contents': contents
    } == pyls_hover(doc, hov_position)

    assert {'contents': ''} == pyls_hover(doc, no_hov_position)
