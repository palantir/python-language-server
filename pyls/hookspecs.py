# Copyright 2017 Palantir Technologies, Inc.
from pyls import hookspec


@hookspec
def pyls_completions(workspace, document, position):
    pass


@hookspec
def pyls_definitions(workspace, document, position):
    pass


@hookspec()
def pyls_document_symbols(workspace, document):
    pass


@hookspec(firstresult=True)
def pyls_format_document(workspace, document):
    pass


@hookspec(firstresult=True)
def pyls_format_range(workspace, document, range):
    pass


@hookspec(firstresult=True)
def pyls_hover(workspace, document, position):
    pass


@hookspec
def pyls_lint(workspace, document):
    pass


@hookspec
def pyls_references(workspace, document, position, exclude_declaration):
    pass


@hookspec(firstresult=True)
def pyls_signature_help(workspace, document, position):
    pass
