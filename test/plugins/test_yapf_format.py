# Copyright 2017 Palantir Technologies, Inc.

import re

from functools import reduce, partial
from itertools import groupby
from operator import itemgetter
from unicodedata import category


from hypothesis import given
from hypothesis import strategies as st

from pyls import uris
from pyls.plugins.yapf_format import (
    pyls_format_document,
    pyls_format_range,
    _make_edits,
    _make_range,
    _to_position,
    _to_index,
)
from pyls.workspace import Document

DOC_URI = uris.from_fs_path(__file__)



@given(st.lists(st.integers(min_value=1), unique=True), st.data())
def test_position(ends, data):
    ends.sort()
    ends.insert(0, 0)
    index = data.draw(st.integers(min_value=0, max_value=ends[-1]))
    assert _to_index(ends, _to_position(ends, index)) == index


@given(st.text(), st.data())
def test_make_edits(s1, data):
    ends = [0] + list(m.start() for m in re.finditer('\n', s1))
    s2 = ''.join(data.draw(st.permutations(s1 + data.draw(st.text()))))
    edits = _make_edits(s1, s2)
    assert apply_edits(s1, ends, edits) == s2



def apply_edits(text, ends, edits):
    pos = itemgetter('line', 'character')
    def apply_edit(acc, edit):
        range = edit['range']
        start, end = map(partial(_to_index, ends), (range['start'], range['end']))
        return ''.join((acc[:start], edit['newText'], acc[end - 1:]))
    return reduce(apply_edit, reversed(edits), text) 
