# Copyright 2020 Palantir Technologies, Inc.
import logging

from pyls import hookimpl, uris, _utils

log = logging.getLogger(__name__)


@hookimpl
def pyls_rename(config, workspace, document, position, new_name):  # pylint: disable=unused-argument
    log.debug('Executing rename of %s to %s', document.word_at_position(position), new_name)
    kwargs = _utils.position_to_jedi_linecolumn(document, position)
    kwargs['new_name'] = new_name
    try:
        refactoring = document.jedi_script().rename(**kwargs)
    except NotImplementedError:
        raise Exception('No support for renaming in Python 2/3.5 with Jedi. '
                        'Consider using the rope_rename plugin instead')
    log.debug('Finished rename: %s', refactoring.get_diff())
    changes = []
    for file_path, changed_file in refactoring.get_changed_files().items():
        uri = uris.from_fs_path(str(file_path))
        doc = workspace.get_maybe_document(uri)
        changes.append({
            'textDocument': {
                'uri': uri,
                'version': doc.version if doc else None
            },
            'edits': [
                {
                    'range': {
                        'start': {'line': 0, 'character': 0},
                        'end': {
                            'line': _num_lines(changed_file.get_new_code()),
                            'character': 0,
                        },
                    },
                    'newText': changed_file.get_new_code(),
                }
            ],
        })
    return {'documentChanges': changes}


def _num_lines(file_contents):
    'Count the number of lines in the given string.'
    return len(file_contents.splitlines())
