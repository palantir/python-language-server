import sys

from rope.refactor.importutils import ImportOrganizer

from pyls import hookimpl


@hookimpl
def pyls_code_actions(config, workspace, document, range, context):
    return [
        {
            'title': 'Organize imports',
            'command': 'rope-organize-imports',
            'arguments': {'document': str(document)}
        }
    ]


@hookimpl
def pyls_execute_command(config, workspace, command, arguments):
    document = workspace.get_document(arguments['document'])

    rope_config = config.settings(document_path=document.path).get('rope', {})
    rope_project = workspace._rope_project_builder(rope_config)
    organizer = ImportOrganizer(rope_project)

    changes = organizer.organize_imports(document._rope_resource(rope_config))
    rope_project.do(changes)
