# Copyright 2017 Palantir Technologies, Inc.
import logging
import re
import os

from bisect import bisect
from difflib import SequenceMatcher

from yapf.yapflib import file_resources
from yapf.yapflib.yapf_api import FormatCode
from pyls import hookimpl

log = logging.getLogger(__name__)


@hookimpl
def pyls_format_document(document):
    return _format(document, lines=[(1, len(document.lines))])


@hookimpl
def pyls_format_range(document, range):  # pylint: disable=redefined-builtin
    # From Yapf docs:
    # lines: (list of tuples of integers) A list of tuples of lines, [start, end],
    #   that we want to format. The lines are 1-based indexed. It can be used by
    #   third-party code (e.g., IDEs) when reformatting a snippet of code rather
    #   than a whole file.

    # Add 1 for 1-indexing vs LSP's 0-indexing
    start, end = range['start']['line'], range['end']['line']
    end += (len(document.lines[end]) - 1 == range['end']['character'])
    return _format(document, lines=[(start + 1, end)])


def _to_position(ends, idx):
    pos = bisect(ends, idx)
    return dict(line=pos - 1, character=idx - ends[pos - 1] - (pos > 1))


def _to_index(ends, position):
    idx = ends[position['line']]
    return idx + position['character'] + (position['line'] != 0)


def _make_range(ends, start, end):
    return dict(start=_to_position(ends, start), end=_to_position(ends, end))


def _make_edits(s1, s2):
    ends = [0] + list(m.start() for m in re.finditer('\n', s1))
    return [
        dict(range=_make_range(ends, i1, i2), newText=s2[j1:j2])
        for tag, i1, i2, j1, j2 in SequenceMatcher(None, s1, s2).get_opcodes()
        if tag != 'equal'
    ]


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
    return _make_edits(src, updated)
