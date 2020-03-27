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

NUMPY_DOC = """

import numpy as np
np.sin

"""

def test_numpy_hover():
    # Over the blank line
    no_hov_position = {'line': 1, 'character': 0}
    # Over 'numpy' in import numpy as np
    numpy_hov_position_1 = {'line': 2, 'character': 8}
    # Over 'np' in import numpy as np
    numpy_hov_position_2 = {'line': 2, 'character': 17}
    # Over 'np' in np.sin
    numpy_hov_position_3 = {'line': 3, 'character': 1}
    # Over 'sin' in np.sin
    numpy_sin_hov_position = {'line': 3, 'character': 4}

    doc = Document(DOC_URI, NUMPY_DOC)

    if LooseVersion(_utils.JEDI_VERSION) >= LooseVersion('0.15.0'):
        contents = [
            {'language': 'python', 'value': 'numpy'},
            'NumPy\n=====\n\nProvides\n\xa0\xa01. '
            'An array object of arbitrary homogeneous items\n\xa0\xa02.']
        assert contents in pyls_hover(doc, numpy_hov_position_1)['contents']

        contents = [
            {'language': 'python', 'value': 'numpy'},
            'NumPy\n=====\n\nProvides\n\xa0\xa01. '
            'An array object of arbitrary homogeneous items\n\xa0\xa02.']
        assert contents in pyls_hover(doc, numpy_hov_position_2)['contents']

        contents = [
            {'language': 'python', 'value': 'numpy'},
            'NumPy\n=====\n\nProvides\n\xa0\xa01. '
            'An array object of arbitrary homogeneous items\n\xa0\xa02.']
        assert contents in pyls_hover(doc, numpy_hov_position_3)['contents']

        contents = [
            {'language': 'python', 'value': 'numpy'},
            'Trigonometric sine, element-wise.\n\n']
        assert contents in pyls_hover(doc, numpy_sin_hov_position)['contents']


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
