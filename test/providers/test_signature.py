# Copyright 2017 Palantir Technologies, Inc.
from pyls.providers.signature import JediSignatureProvider

DOC_URI = __file__
DOC = """import sys

def main(param1, param2):
    \"\"\" Main docstring \"\"\"
    raise Exception()

main(
"""


def test_no_signature(workspace):
    # Over blank line
    sig_position = {'line': 5, 'character': 0}

    workspace.put_document(DOC_URI, DOC)
    provider = JediSignatureProvider(workspace)

    sigs = provider.run(DOC_URI, sig_position)['signatures']
    assert len(sigs) == 0


def test_signature(workspace):
    # Over '( ' in main(
    sig_position = {'line': 6, 'character': 5}

    workspace.put_document(DOC_URI, DOC)
    provider = JediSignatureProvider(workspace)

    sigs = provider.run(DOC_URI, sig_position)['signatures']
    assert len(sigs) == 1
    assert sigs[0]['label'] == 'main(param1, param2)'
    assert sigs[0]['params'][0]['label'] == 'param1'
