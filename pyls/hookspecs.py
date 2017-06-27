# Copyright 2017 Palantir Technologies, Inc.
# pylint: disable=redefined-builtin, unused-argument
from pyls import hookspec


@hookspec
def pyls_code_actions(workspace, document, range, context):
    pass


@hookspec
def pyls_commands(workspace):
    """The list of command strings supported by the server.

    Returns:
        List[str]: The supported commands.
    """


@hookspec
def pyls_completions(workspace, document, position):
    pass


@hookspec
def pyls_definitions(workspace, document, position):
    pass


@hookspec
def pyls_document_symbols(workspace, document):
    pass


@hookspec(firstresult=True)
def pyls_execute_command(workspace, command, arguments):
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
