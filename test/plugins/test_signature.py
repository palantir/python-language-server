# Copyright 2017 Palantir Technologies, Inc.
from pyls import uris
from pyls.plugins.signature import pyls_signature_help
from pyls.workspace import Document

DOC_URI = uris.from_fs_path(__file__)
DOC = """import sys

def main(param1, param2):
    \"\"\" Main docstring \"\"\"
    raise Exception()

main(
"""


def test_no_signature():
    # Over blank line
    sig_position = {'line': 5, 'character': 0}
    doc = Document(DOC_URI, DOC)

    sigs = pyls_signature_help(doc, sig_position)['signatures']
    assert len(sigs) == 0


def test_signature():
    # Over '( ' in main(
    sig_position = {'line': 6, 'character': 5}
    doc = Document(DOC_URI, DOC)

    sigs = pyls_signature_help(doc, sig_position)['signatures']
    assert len(sigs) == 1
    assert sigs[0]['label'] == 'main(param1, param2)'
    assert sigs[0]['parameters'][0]['label'] == 'param1'
