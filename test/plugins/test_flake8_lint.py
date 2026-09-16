# Copyright 2019 Palantir Technologies, Inc.
import logging
import sys
import tempfile
import os
from mock import patch
from pyls import lsp, uris
from pyls.plugins import flake8_lint
from pyls.workspace import Document


DOC_URI = uris.from_fs_path(__file__)
DOC = """import pyls

t = "TEST"

def using_const():
\ta = 8 + 9
\treturn t
"""


def temp_document(doc_text, workspace):
    temp_file = tempfile.NamedTemporaryFile(mode='w', delete=False)
    name = temp_file.name
    temp_file.write(doc_text)
    temp_file.close()
    doc = Document(uris.from_fs_path(name), workspace)

    return name, doc


def test_flake8_unsaved(workspace):
    doc = Document('', workspace, DOC)
    diags = flake8_lint.pyls_lint(workspace, doc)
    msg = 'F841 local variable \'a\' is assigned to but never used'
    unused_var = [d for d in diags if d['message'] == msg][0]

    assert unused_var['source'] == 'flake8'
    assert unused_var['code'] == 'F841'
    assert unused_var['range']['start'] == {'line': 5, 'character': 1}
    assert unused_var['range']['end'] == {'line': 5, 'character': 11}
    assert unused_var['severity'] == lsp.DiagnosticSeverity.Warning


def test_flake8_lint(workspace):
    try:
        name, doc = temp_document(DOC, workspace)
        diags = flake8_lint.pyls_lint(workspace, doc)
        msg = 'F841 local variable \'a\' is assigned to but never used'
        unused_var = [d for d in diags if d['message'] == msg][0]

        assert unused_var['source'] == 'flake8'
        assert unused_var['code'] == 'F841'
        assert unused_var['range']['start'] == {'line': 5, 'character': 1}
        assert unused_var['range']['end'] == {'line': 5, 'character': 11}
        assert unused_var['severity'] == lsp.DiagnosticSeverity.Warning

    finally:
        os.remove(name)


def test_flake8_config_param(workspace):
    with patch('pyls.plugins.flake8_lint.Popen') as popen_mock:
        mock_instance = popen_mock.return_value
        mock_instance.communicate.return_value = [bytes(), bytes()]
        flake8_conf = '/tmp/some.cfg'
        workspace._config.update({'plugins': {'flake8': {'config': flake8_conf}}})
        _name, doc = temp_document(DOC, workspace)
        flake8_lint.pyls_lint(workspace, doc)
        call_args = popen_mock.call_args.args[0]
        assert 'flake8' in call_args
        assert '--config={}'.format(flake8_conf) in call_args


def test_flake8_executable_param(workspace):
    with patch('pyls.plugins.flake8_lint.Popen') as popen_mock:
        mock_instance = popen_mock.return_value
        mock_instance.communicate.return_value = [bytes(), bytes()]

        flake8_executable = '/tmp/flake8'
        workspace._config.update({'plugins': {'flake8': {'executable': flake8_executable}}})

        _name, doc = temp_document(DOC, workspace)
        flake8_lint.pyls_lint(workspace, doc)

        call_args = popen_mock.call_args.args[0]
        assert flake8_executable in call_args


def test_flake8_passes_stdin_display_name(workspace):
    """flake8 reads the document from stdin, so it has to be told the real filename.

    Without it flake8 sees the file as "stdin" and any setting resolved per filename,
    such as per-file-ignores or exclude, silently cannot match.
    """
    with patch('pyls.plugins.flake8_lint.Popen') as popen_mock:
        mock_instance = popen_mock.return_value
        mock_instance.communicate.return_value = [bytes(), bytes()]

        name, doc = temp_document(DOC, workspace)
        try:
            flake8_lint.pyls_lint(workspace, doc)
            call_args = popen_mock.call_args.args[0]
            assert '--stdin-display-name={}'.format(doc.path) in call_args
        finally:
            os.remove(name)


def test_flake8_omits_stdin_display_name_without_a_path(workspace):
    """An unsaved document has no path, so there is no name to report."""
    with patch('pyls.plugins.flake8_lint.Popen') as popen_mock:
        mock_instance = popen_mock.return_value
        mock_instance.communicate.return_value = [bytes(), bytes()]

        doc = Document('', workspace, DOC)
        flake8_lint.pyls_lint(workspace, doc)

        call_args = popen_mock.call_args.args[0]
        assert not [arg for arg in call_args if arg.startswith('--stdin-display-name')]


def test_flake8_falls_back_to_the_running_interpreter(workspace):
    """The fallback must not be a bare "python", which Python 3 only systems lack."""
    with patch('pyls.plugins.flake8_lint.Popen') as popen_mock:
        def fail_for_executable(cmd, **_kwargs):
            if cmd[0] == 'flake8':
                raise IOError('not found')
            mock_instance = patch('pyls.plugins.flake8_lint.Popen').start()
            mock_instance.communicate.return_value = [bytes(), bytes()]
            return mock_instance

        popen_mock.side_effect = fail_for_executable
        _name, doc = temp_document(DOC, workspace)
        flake8_lint.pyls_lint(workspace, doc)

        fallback_cmd = popen_mock.call_args.args[0]
        assert fallback_cmd[:3] == [sys.executable, '-m', 'flake8']
        assert fallback_cmd[0] != 'python'


def test_flake8_reports_when_it_cannot_run_at_all(workspace, caplog):
    """Both attempts failing should log something actionable, not raise."""
    with patch('pyls.plugins.flake8_lint.Popen', side_effect=IOError('not found')):
        _name, doc = temp_document(DOC, workspace)
        with caplog.at_level(logging.ERROR):
            diags = flake8_lint.pyls_lint(workspace, doc)

    assert not diags
    errors = [r.getMessage() for r in caplog.records if r.levelno >= logging.ERROR]
    assert len(errors) == 1
    assert 'flake8.executable' in errors[0]


def test_per_file_ignores_are_respected(workspace, tmpdir):
    """End to end: the setting that this fix exists for.

    Runs the real flake8 against a project whose config ignores a code for this file.
    """
    project = tmpdir.mkdir('proj')
    project.join('setup.cfg').write(
        '[flake8]\nper-file-ignores =\n    legacy.py: F841\n'
    )
    source_file = project.join('legacy.py')
    source_file.write(DOC)

    doc = Document(uris.from_fs_path(str(source_file)), workspace, DOC)
    workspace._config.update({'plugins': {'flake8': {'config': str(project.join('setup.cfg'))}}})
    diags = flake8_lint.pyls_lint(workspace, doc)

    assert not [d for d in diags if d['code'] == 'F841'], \
        'per-file-ignores should have suppressed F841 for legacy.py'
