# Copyright 2017 Palantir Technologies, Inc.
from configparser import RawConfigParser
import logging
import pycodestyle
from pyls import hookimpl

log = logging.getLogger(__name__)

# Potential config files in reverse order of preference
CONFIG_FILES = ['tox.ini', 'pep8.cfg', 'setup.cfg', 'pycodestyle.cfg']


@hookimpl
def pyls_lint(workspace, document):
    # Read config from all over the place
    conf = {k.replace("-", "_"): v for k, v in _get_config(workspace, document)}
    log.debug("Got pycodestyle config: %s", conf)

    # Grab the pycodestyle parser and set the defaults based on the config we found
    parser = pycodestyle.get_parser()
    parser.set_defaults(**conf)
    opts, _args = parser.parse_args([])
    styleguide = pycodestyle.StyleGuide(vars(opts))

    c = pycodestyle.Checker(
        filename=document.uri, lines=document.lines, options=styleguide.options,
        report=PyCodeStyleDiagnosticReport(styleguide.options)
    )
    c.check_all()
    diagnostics = c.report.diagnostics
    return diagnostics


def _get_config(workspace, document):
    """ Parse the pep8/pycodestyle config options. """
    config = RawConfigParser()
    config_files = workspace.find_parent_files(document.path, CONFIG_FILES)

    if not config_files:
        # If no config files match, we can't do much
        return []

    # Find out which section header is used, pep8 or pycodestyle
    files_read = config.read(config_files)
    log.debug("Using pycodestyle config from %s", files_read)

    if config.has_section('pycodestyle'):
        return config.items('pycodestyle')
    if config.has_section('pep8'):
        log.warning("The 'pep8' section is deprecated, use 'pycodestyle' instead")
        return config.items('pep8')

    return []


class PyCodeStyleDiagnosticReport(pycodestyle.BaseReport):

    def __init__(self, options=None, **kwargs):
        self.diagnostics = []
        super(PyCodeStyleDiagnosticReport, self).__init__(options=options, **kwargs)

    def error(self, lineno, offset, text, check):
        # PyCodeStyle will sometimes give you an error the line after the end of the file
        #   e.g. no newline at end of file
        # In that case, the end offset should just be some number ~100
        # (because why not? There's nothing to underline anyways)
        log.info("Got pycodestyle error at %d:%d %s", lineno, offset, text)
        range = {
            'start': {'line': lineno - 1, 'character': offset},
            'end': {
                # FIXME: It's a little naiive to mark until the end of the line, can we not easily do better?
                'line': lineno - 1, 'character': 100 if lineno > len(self.lines) else len(self.lines[lineno - 1])
            },
        }
        code, _message = text.split(" ", 1)
        severity = self._get_severity(code)

        self.diagnostics.append({
            'source': 'pycodestyle',
            'range': range,
            'message': text,
            'code': code,
            'severity': severity
        })

    def _get_severity(self, code):
        """ VSCode Severity Mapping
        ERROR: 1,
        WARNING: 2,
        INFO: 3,
        HINT: 4
        """
        if code[0] == 'E':
            return 1
        elif code[0] == 'W':
            return 2
