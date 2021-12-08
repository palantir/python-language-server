# Copyright 2017 Palantir Technologies, Inc.
import logging
import os
from yapf.yapflib import file_resources, style
from yapf.yapflib.yapf_api import FormatCode
from pyls import hookimpl

log = logging.getLogger(__name__)


@hookimpl
def pyls_format_document(document):
    return _format(document)



@hookimpl
def pyls_format_range(document, range, options=None):  # pylint: disable=redefined-builtin
    # First we 'round' the range up/down to full lines only
    range['start']['character'] = 0
    range['end']['line'] += 1
    range['end']['character'] = 0

    # From Yapf docs:
    # lines: (list of tuples of integers) A list of tuples of lines, [start, end],
    #   that we want to format. The lines are 1-based indexed. It can be used by
    #   third-party code (e.g., IDEs) when reformatting a snippet of code rather
    #   than a whole file.

    # Add 1 for 1-indexing vs LSP's 0-indexing
    lines = [(range['start']['line'] + 1, range['end']['line'] + 1)]
    return _format(document, lines=lines, options=options)


def _format(document, lines=None, options=None):
    # Get the default styles
    style_config = file_resources.GetDefaultStyleForDir(
            os.path.dirname(document.path)
        )
    if options is not None:
        # If we have options, let's set them
        # First we want to get a dictionary of the styles
        style_config = style.CreateStyleFromConfig(style_config)

        if options.get('insertSpaces') is not None:
            style_config['USE_TABS'] = not (options.get('insertSpaces') in [True, 'true', 'True'])

            if style_config['USE_TABS']:
                # indent width doesn't make sense when using tabs
                # the specifications state: "Size of a tab in spaces"
                style_config['INDENT_WIDTH'] = 1
                style_config['CONTINUATION_INDENT_WIDTH'] = style_config['INDENT_WIDTH']

        print(style_config['USE_TABS'])

        if options.get('tabSize') is not None and not style_config['USE_TABS']:
            style_config['INDENT_WIDTH'] = max(int(options.get('tabSize')), 1)
            style_config['CONTINUATION_INDENT_WIDTH'] = style_config['INDENT_WIDTH']
        

    new_source, changed = FormatCode(
        document.source,
        lines=lines,
        filename=document.filename,
        style_config=style_config
    )

    if not changed:
        return []

    # I'm too lazy at the moment to parse diffs into TextEdit items
    # So let's just return the entire file...
    return [{
        'range': {
            'start': {'line': 0, 'character': 0},
            # End char 0 of the line after our document
            'end': {'line': len(document.lines), 'character': 0}
        },
        'newText': new_source
    }]
