
from textwrap import dedent

from pyls import uris
from pyls.workspace import Document
from pyls.plugins.folding import pyls_folding_range


DOC_URI = uris.from_fs_path(__file__)
DOC = dedent("""
def func(arg1, arg2, arg3,
         arg4, arg5, default=func(
             2, 3, 4
         )):
    return (2, 3,
            4, 5)

class A():
    def method(self, x1):
        def inner():
            return x1

        if x2:
            func(3, 4, 5, 6,
                 7)
        elif x3 < 2:
            pass
        else:
            more_complex_func(2, 3, 4, 5, 6,
                              8)
        return inner

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
    for j in range(0, i):
        if i % 2 == 1:
            pass

compren = [x for x in range(0, 3)
           if x == 2]

with open('doc', 'r') as f:
    try:
        f / 0
    except:
        pass
    finally:
        raise SomeException()
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
                {'startLine': 8, 'endLine': 21},
                {'startLine': 9, 'endLine': 21},
                {'startLine': 10, 'endLine': 11},
                {'startLine': 13, 'endLine': 15},
                {'startLine': 14, 'endLine': 15},
                {'startLine': 16, 'endLine': 17},
                {'startLine': 18, 'endLine': 20},
                {'startLine': 19, 'endLine': 20},
                {'startLine': 24, 'endLine': 25},
                {'startLine': 27, 'endLine': 29},
                {'startLine': 28, 'endLine': 29},
                {'startLine': 31, 'endLine': 40},
                {'startLine': 33, 'endLine': 37},
                {'startLine': 35, 'endLine': 37},
                {'startLine': 36, 'endLine': 37},
                {'startLine': 38, 'endLine': 40},
                {'startLine': 39, 'endLine': 40},
                {'startLine': 42, 'endLine': 43},
                {'startLine': 45, 'endLine': 51},
                {'startLine': 46, 'endLine': 47},
                {'startLine': 48, 'endLine': 49},
                {'startLine': 50, 'endLine': 51}]
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
