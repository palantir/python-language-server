
from pyls import uris
from pyls.workspace import Document
from pyls.plugins.folding import pyls_folding_range

from textwrap import dedent

DOC_URI = uris.from_fs_path(__file__)
DOC = dedent("""
def func(arg1, arg2, arg3,
         arg4, arg5, default=func(
             2, 3, 4
         )):
    return (2, 3,
            4, 5)

class A():
    pass

a = 2
operation = (a_large_variable_that_fills_all_space +
             other_embarrasingly_long_variable - 2 * 3 / 5)

(a, b, c,
 d, e, f) = func(3, 4, 5, 6,
                 7, 8, 9, 10)

for i in range(0, 3):
    i += 1
    while x < i:
        expr = (2, 4)
        a = func(expr + i, arg2, arg3, arg4,
                 arg5, var(2, 3, 4,
                           5))

compren = [x for x in range(0, 3)
           if x == 2]

with open('doc', 'r') as f:
    try:
        f / 0
    except:
        pass
""")

SYNTAX_ERR = dedent("""
def func(arg1, arg2, arg3,
         arg4, arg5, default=func(
             2, 3, 4
         )):
    return (2, 3,
            4, 5)

class A():
    pass

a = 2
operation = (a_large_variable_that_fills_all_space +
             other_embarrasingly_long_variable - 2 * 3 / 5)

(a, b, c,
 d, e, f) = func(3, 4, 5, 6,
                 7, 8, 9, 10

for i in range(0, 3):
    i += 1
    while x < i:
        expr = (2, 4)
""")


def test_folding():
    doc = Document(DOC_URI, DOC)
    ranges = pyls_folding_range(doc)
    expected = [{'startLine': 1, 'endLine': 6},
                {'startLine': 2, 'endLine': 3},
                {'startLine': 5, 'endLine': 6},
                {'startLine': 8, 'endLine': 9},
                {'startLine': 12, 'endLine': 13},
                {'startLine': 15, 'endLine': 17},
                {'startLine': 16, 'endLine': 17},
                {'startLine': 19, 'endLine': 25},
                {'startLine': 21, 'endLine': 25},
                {'startLine': 23, 'endLine': 25},
                {'startLine': 24, 'endLine': 25},
                {'startLine': 27, 'endLine': 28},
                {'startLine': 30, 'endLine': 34},
                {'startLine': 31, 'endLine': 34}]
    assert ranges == expected


def test_folding_syntax_error():
    doc = Document(DOC_URI, SYNTAX_ERR)
    ranges = pyls_folding_range(doc)
    expected = [{'startLine': 1, 'endLine': 6},
                {'startLine': 2, 'endLine': 3},
                {'startLine': 5, 'endLine': 6},
                {'startLine': 8, 'endLine': 9},
                {'startLine': 12, 'endLine': 13}]
    assert ranges == expected
