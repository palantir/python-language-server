# Copyright 2017 Palantir Technologies, Inc.
import logging
import os

from bisect import bisect
from difflib import SequenceMatcher
from itertools import accumulate

from yapf.yapflib import file_resources
from yapf.yapflib.yapf_api import FormatCode
from pyls import hookimpl

log = logging.getLogger(__name__)


@hookimpl
def pyls_format_document(document):
    return _format(document)


@hookimpl
def pyls_format_range(document, range):  # pylint: disable=redefined-builtin
    # First we 'round' the range up/down to full lines only
    start, end = range['start']['line'], range['end']['line']

    # From Yapf docs:
    # lines: (list of tuples of integers) A list of tuples of lines, [start, end],
    #   that we want to format. The lines are 1-based indexed. It can be used by
    #   third-party code (e.g., IDEs) when reformatting a snippet of code rather
    #   than a whole file.

    # Add 1 for 1-indexing vs LSP's 0-indexing
    lines = ((start + 1), end + (start == end)),
    return _format(document, lines=lines)


def _format(document, lines=None):
    src = document.source
    updated, changed = FormatCode(
        src,
        lines=lines,
        filename=document.filename,
        style_config=file_resources.GetDefaultStyleForDir(
            os.path.dirname(document.filename)
        )
    )
    if not changed:
        return []
    positions = [0] + list(accumulate(map(len, src.splitlines(keepends=True))))
    def make_position(i):
        pos = bisect(positions, i)
        return dict(line=pos - 1, character=i - positions[pos - 1])
    opcodes = SequenceMatcher(None, src, updated).get_opcodes()
    return [
        dict(
            range=dict(start=make_position(i1), end=make_position(i2)),
            newText=updated[j1:j2]
        )
        for tag, i1, i2, j1, j2 in opcodes
        if tag != 'equal' or i1 != j1 or i2 != j2
    ]
