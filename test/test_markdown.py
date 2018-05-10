# Copyright 2017 Palantir Technologies, Inc.
import os
import pytest
from pyls import markdown

from . import markdown_files

MD_FILES_DIR = os.path.dirname(markdown_files.__file__)
FILES = [os.path.splitext(filename)[0] for filename in os.listdir(MD_FILES_DIR) if filename.endswith(".pydoc")]


@pytest.mark.parametrize('basename', FILES)
def test_rst2markdown(basename):
    md_file = os.path.join(MD_FILES_DIR, basename + ".md")
    pydoc_file = os.path.join(MD_FILES_DIR, basename + ".pydoc")

    expected = open(md_file).read().rstrip('\n')
    actual = markdown.rst2markdown(open(pydoc_file).read())

    if basename == "numpy.linspace":
        with open(md_file + ".test.md", 'w+') as f:
            f.write(actual)
    assert actual == expected
