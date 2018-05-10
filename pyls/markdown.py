# Copyright 2017 Palantir Technologies, Inc.
#
# Based on https://github.com/Microsoft/vscode-python/blob/29a0caea60354ac24232bc038d1f5af23db29732 \
#   /src/client/common/markdown/restTextConverter.ts


def rst2markdown(docstring):
    """Translates reStructruredText (Python doc syntax) to markdown.

    It only translates as much as needed to display nice-ish hovers. See https://en.wikipedia.org/wiki/ReStructuredText
    """
    return _Rst2Markdown().convert(docstring)


_STATE_DEFAULT = "default"
_STATE_PREFORMATTED = "preformatted"
_STATE_CODE = "code"
_STATE_DOCTEST = "doctest"


class _Rst2Markdown(object):

    def __init__(self):
        self._md = []
        self._state = _STATE_DEFAULT

    def convert(self, docstring):
        lines = docstring.splitlines()
        i = 0

        while i < len(lines):
            line = lines[i]

            # Ignore leading empty lines
            if not self._md and not line:
                i += 1
                continue

            if self._state == _STATE_DEFAULT:
                i += self._default(lines, i)
            elif self._state == _STATE_PREFORMATTED:
                i += self._preformatted(lines, i)
            elif self._state == _STATE_CODE:
                self._code(line)
            elif self._state == _STATE_DOCTEST:
                self._doctest(line)

            i += 1

        self._end_code()
        self._end_doctest()
        self._end_preformatted()

        return '\n'.join(self._md).strip()

    def _default(self, lines, i):
        line = lines[i]

        if line.startswith('```'):
            self._start_code()
            return 0

        if line.startswith('>>>') or line.startswith('...'):
            self._start_doctest()
            return -1

        if line.startswith('===') or line.startswith('---'):
            # Eat standalone === or --- lines
            return 0

        if self._double_colon(line):
            return 0

        if _is_ignorable(line):
            return 0

        if self._section_header(lines, i):
            # Eat line with === or ---
            return 1

        result = self._check_pre_content(lines, i)
        if self._state != _STATE_DEFAULT:
            return result

        line = _cleanup(line)
        # Convert double backticks to single
        line = line.replace('``', '`')
        line = _escape_markdown(line)
        self._md.append(line)

        return 0

    def _preformatted(self, lines, i):
        line = lines[i]
        if _is_ignorable(line):
            return 0

        # Preformatted block terminates by a line without leading whitespace
        if line and not _is_whitespace(line[0]) and not _is_list_item(line):
            self._end_preformatted()
            return -1

        prev_line = self._md[-1] if self._md else None
        if not line and prev_line is not None and (not prev_line or prev_line.startswith('```')):
            # Avoid more than one empty line in a row
            return 0

        # Since we use HTML blocks for preformatted text, drop angle brackets
        line = line.replace('<', ' ').replace('>', ' ').rstrip()
        # Convert double backticks to single
        line = line.replace('``', '`')

        self._md.append(line)

        return 0

    def _code(self, line):
        prev_line = self._md[-1] if self._md else None
        if not line and prev_line is not None and (not prev_line or prev_line.startswith('```')):
            # Avoid more than one empty line in a row
            return

        if line.startswith('```'):
            self._end_code()
        else:
            self._md.append(line)

    def _doctest(self, line):
        if not line:
            self._end_doctest()
        else:
            self._md.append(line)

    def _check_pre_content(self, lines, i):
        line = lines[i]
        if i == 0 or not line.strip():
            return 0

        if not _is_whitespace(line[0]) and not _is_list_item(line):
            # Regular line, do nothing
            return 0

        # Indented content is considered to be preformatted
        self._start_preformatted()
        return -1

    def _section_header(self, lines, i):
        line = lines[i]
        if i >= len(lines) - 1:
            # No next line
            return False

        next_line = lines[i + 1]
        if next_line.startswith("==="):
            # Section title -> heading level 3
            self._md.append('### ' + _cleanup(line))
            return True
        elif next_line.startswith("---"):
            # Subsection title -> heading level 4
            self._md.append('#### ' + _cleanup(line))
            return True
        else:
            return False

    def _double_colon(self, line):
        if not line.endswith("::"):
            return False

        # Literal blocks being with `::`
        if len(line) > 2 and not line.startswith(".."):
            # Ignore lines like .. autosummary:: blah
            # Trim trailing : so :: turns into :
            self._md.append(line[:-1])

        self._start_preformatted()
        return True

    def _start_doctest(self):
        self._try_remove_preceeding_empty_lines()
        self._md.append('```pydocstring')
        self._state = _STATE_DOCTEST

    def _start_code(self):
        # Remove previous empty line so we avoid double empties
        self._try_remove_preceeding_empty_lines()
        self._md.append('```python')
        self._state = _STATE_CODE

    def _end_code(self):
        if self._state == _STATE_CODE:
            self._try_remove_preceeding_empty_lines()
            self._md.append('```')
            self._state = _STATE_DEFAULT

    def _end_doctest(self):
        if self._state == _STATE_DOCTEST:
            self._try_remove_preceeding_empty_lines()
            self._md.append('```')
            self._state = _STATE_DEFAULT

    def _start_preformatted(self):
        # Remove previous empty line so we avoid double empties
        self._try_remove_preceeding_empty_lines()
        # Lie about the language since we don't want preformatted text
        # to be colorized as Python. HTML is more 'appropriate' as it does
        # not colorize - - or + or keywords like 'from'.
        self._md.append('```html')
        self._state = _STATE_PREFORMATTED

    def _end_preformatted(self):
        if self._state == _STATE_PREFORMATTED:
            self._try_remove_preceeding_empty_lines()
            self._md.append('```')
            self._state = _STATE_DEFAULT

    def _try_remove_preceeding_empty_lines(self):
        while self._md and not len(self._md[-1].strip()):
            self._md.pop()


def _is_ignorable(line):
    if 'generated/' in line:
        # Drop generated content
        return True

    trimmed = line.strip()
    if trimmed.startswith("..") and '::' in trimmed:
        # Ignore lines like .. sectionauthor:: blah
        return True

    return False


def _is_list_item(line):
    """True if the line is part of a list."""
    trimmed = line.strip()
    if trimmed:
        char = trimmed[0]
        return char == "*" or char == "-" or _is_decimal(char)
    return False


def _is_whitespace(string):
    return not string or string.isspace()


def _is_decimal(string):
    try:
        int(string)
        return True
    except ValueError:
        return False


def _cleanup(line):
    return line.replace(':mod:', 'module:')


def _escape_markdown(string):
    return string.replace('#', '\\#').replace('*', '\\*').replace(' _', ' \\_')
