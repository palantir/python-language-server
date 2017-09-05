# Copyright 2017 Palantir Technologies, Inc.
import logging
import pycodestyle
from pyls import config as pyls_config, hookimpl, lsp

log = logging.getLogger(__name__)

# Potential config files in reverse order of preference
CONFIG_FILES = ['tox.ini', 'pep8.cfg', 'setup.cfg', 'pycodestyle.cfg']


@hookimpl
def pyls_lint(config, document):
    # Read config from all over the place
    config_files = config.find_parents(document.path, CONFIG_FILES)
    if pycodestyle.USER_CONFIG:
        config_files = [pycodestyle.USER_CONFIG] + config_files
    pycodestyle_conf = pyls_config.build_config('pycodestyle', config_files)
    pep8_conf = pyls_config.build_config('pep8', config_files)

    conf_to_use = pycodestyle_conf if pycodestyle_conf else pep8_conf

    conf = {k.replace("-", "_"): v for k, v in conf_to_use.items()}
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

        self.diagnostics.append({
            'source': 'pycodestyle',
            'range': range,
            'message': text,
            'code': code,
            # Are style errors really ever errors?
            'severity': lsp.DiagnosticSeverity.Warning
        })
