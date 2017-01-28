# Copyright 2017 Palantir Technologies, Inc.
from configparser import RawConfigParser
import logging
import pycodestyle
from pyflakes import api as pyflakes_api
from .base import BaseProvider

log = logging.getLogger(__name__)


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


class PyCodeStyleLinter(BaseProvider):
    """ Provide linting diagnostics based on the results of pycodestyle (formerly pep8).

    pycodestyle is written in a way that's really hard to plug into...
    Maybe we should just parse stdout of a subprocess call to pycodestyle?! Seriously...
    """

    # Potential config files in reverse order of preference
    CONFIG_FILES = ['tox.ini', 'pep8.cfg', 'setup.cfg', 'pycodestyle.cfg']

    def get_config(self, document):
        """ Parse the pep8/pycodestyle config options. """
        config = RawConfigParser()

        config_files = self.workspace.find_config_files(document, self.CONFIG_FILES)

        if not self.workspace.is_local() or not config_files:
            # If we don't have a local workspace, can't do much.
            # Otherwise we can assume the document is somewhere in the workspace root
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

    def run(self, doc_uri):
        document = self.workspace.get_document(doc_uri)

        # Read config from all over the place
        conf = {k.replace("-", "_"): v for k, v in self.get_config(document)}
        log.debug("Got pycodestyle config: %s", conf)

        # Grab the pycodestyle parser and set the defaults based on the config we found
        parser = pycodestyle.get_parser()
        parser.set_defaults(**conf)
        opts, _args = parser.parse_args([])
        styleguide = pycodestyle.StyleGuide(vars(opts))

        c = pycodestyle.Checker(
            filename=doc_uri, lines=document.lines, options=styleguide.options,
            report=PyCodeStyleDiagnosticReport(styleguide.options)
        )
        c.check_all()
        diagnostics = c.report.diagnostics
        return diagnostics


class PyflakesDiagnosticReport(object):

    def __init__(self, lines):
        self.lines = lines
        self.diagnostics = []

    def unexpectedError(self, filename, msg):  # pragma: no cover
        pass

    def syntaxError(self, filename, msg, lineno, offset, text):
        range = {
            'start': {'line': lineno - 1, 'character': offset},
            'end': {'line': lineno - 1, 'character': offset + len(text)},
        }
        self.diagnostics.append({
            'source': 'pyflakes',
            'range': range,
            'message': msg
        })

    def flake(self, message):
        """ Get message like <filename>:<lineno>: <msg> """
        range = {
            'start': {'line': message.lineno - 1, 'character': message.col},
            'end': {'line': message.lineno - 1, 'character': len(self.lines[message.lineno - 1])},
        }
        self.diagnostics.append({
            'source': 'pyflakes',
            'range': range,
            'message': message.message % message.message_args
        })


class PyflakesLinter(BaseProvider):

    def run(self, doc_uri):
        document = self.workspace.get_document(doc_uri)
        reporter = PyflakesDiagnosticReport(document.lines)
        pyflakes_api.check(document.source, doc_uri, reporter=reporter)
        return reporter.diagnostics
