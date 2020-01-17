# Copyright 2017 Palantir Technologies, Inc.
import os
import sys

import pytest

from pyls import uris
from pyls.python_ls import PythonLanguageServer

PY2 = sys.version_info.major == 2

if PY2:
    import pathlib2 as pathlib
    from StringIO import StringIO
else:
    import pathlib
    from io import StringIO


DOC_URI = uris.from_fs_path(__file__)


def path_as_uri(path):
    return pathlib.Path(os.path.abspath(path)).as_uri()


def test_local(pyls):
    """ Since the workspace points to the test directory """
    assert pyls.workspace.is_local()


def test_put_document(pyls):
    pyls.workspace.put_document(DOC_URI, 'content')
    assert DOC_URI in pyls.workspace._docs


def test_get_document(pyls):
    pyls.workspace.put_document(DOC_URI, 'TEXT')
    assert pyls.workspace.get_document(DOC_URI).source == 'TEXT'


def test_get_missing_document(tmpdir, pyls):
    source = 'TEXT'
    doc_path = tmpdir.join("test_document.py")
    doc_path.write(source)
    doc_uri = uris.from_fs_path(str(doc_path))
    assert pyls.workspace.get_document(doc_uri).source == 'TEXT'


def test_rm_document(pyls):
    pyls.workspace.put_document(DOC_URI, 'TEXT')
    assert pyls.workspace.get_document(DOC_URI).source == 'TEXT'
    pyls.workspace.rm_document(DOC_URI)
    assert pyls.workspace.get_document(DOC_URI)._source is None


@pytest.mark.parametrize('metafiles', [('setup.py',), ('pyproject.toml',), ('setup.py', 'pyproject.toml')])
def test_non_root_project(pyls, metafiles):
    repo_root = os.path.join(pyls.workspace.root_path, 'repo-root')
    os.mkdir(repo_root)
    project_root = os.path.join(repo_root, 'project-root')
    os.mkdir(project_root)

    for metafile in metafiles:
        with open(os.path.join(project_root, metafile), 'w+') as f:
            f.write('# ' + metafile)

    test_uri = uris.from_fs_path(os.path.join(project_root, 'hello/test.py'))
    pyls.workspace.put_document(test_uri, 'assert True')
    test_doc = pyls.workspace.get_document(test_uri)
    assert project_root in test_doc.sys_path()


def test_root_project_with_no_setup_py(pyls):
    """Default to workspace root."""
    workspace_root = pyls.workspace.root_path
    test_uri = uris.from_fs_path(os.path.join(workspace_root, 'hello/test.py'))
    pyls.workspace.put_document(test_uri, 'assert True')
    test_doc = pyls.workspace.get_document(test_uri)
    assert workspace_root in test_doc.sys_path()


def test_multiple_workspaces(tmpdir, pyls):
    workspace1_dir = tmpdir.mkdir('workspace1')
    workspace2_dir = tmpdir.mkdir('workspace2')
    file1 = workspace1_dir.join('file1.py')
    file2 = workspace2_dir.join('file1.py')
    file1.write('import os')
    file2.write('import sys')

    msg = {
        'uri': path_as_uri(str(file1)),
        'version': 1,
        'text': 'import os'
    }

    pyls.m_text_document__did_open(textDocument=msg)
    assert msg['uri'] in pyls.workspace._docs

    added_workspaces = [{'uri': path_as_uri(str(x))}
                        for x in (workspace1_dir, workspace2_dir)]
    pyls.m_workspace__did_change_workspace_folders(
        added=added_workspaces, removed=[])

    for workspace in added_workspaces:
        assert workspace['uri'] in pyls.workspaces

    workspace1_uri = added_workspaces[0]['uri']
    assert msg['uri'] not in pyls.workspace._docs
    assert msg['uri'] in pyls.workspaces[workspace1_uri]._docs

    msg = {
        'uri': path_as_uri(str(file2)),
        'version': 1,
        'text': 'import sys'
    }
    pyls.m_text_document__did_open(textDocument=msg)

    workspace2_uri = added_workspaces[1]['uri']
    assert msg['uri'] in pyls.workspaces[workspace2_uri]._docs

    pyls.m_workspace__did_change_workspace_folders(
        added=[], removed=[added_workspaces[0]])
    assert workspace1_uri not in pyls.workspaces


def _make_paths_dir_relative(paths, dirname):
    """Make paths relative to dirname

    This method assumes below for simplicity:

    - if a path in paths is relative, it is relative to "root"
    - dirname must be relative to "root"
    - empty dirname means "root" itself
    - neither "." nor ".." is allowed for dirname
    - dirname must use '/' as delimiter (because "metafile" uses it)
    """
    to_root = os.path.join(*(['..'] * len(dirname.split('/')))) if dirname else ''
    return list(p if os.path.isabs(p) else os.path.join(to_root, p) for p in paths)


@pytest.mark.parametrize('metafile', [
    'setup.cfg',
    'tox.ini',
    'service/foo/setup.cfg',
    'service/foo/tox.ini',
    None,
])
def test_source_roots_config(tmpdir, metafile):
    """Examine that source_roots config is intentionaly read in.

    This test also examines below for entries in source_roots:

    * absolute path is ignored
    * relative path is:
      - ignored, if it does not refer inside of the workspace
      - otherwise, it is treated as relative to config file location, and
      - normalized into absolute one
    """
    root_path = str(tmpdir)

    invalid_roots = ['/invalid/root', '../baz']
    source_roots = ['service/foo', 'service/bar'] + invalid_roots
    doc_root = source_roots[0]

    if metafile:
        dirname = os.path.dirname(metafile)
        if dirname:
            os.makedirs(os.path.join(root_path, dirname))

        # configured by metafile at pyls startup
        with open(os.path.join(root_path, metafile), 'w+') as f:
            f.write('[pyls]\nsource_roots=\n    %s\n' %
                    ',\n    '.join(_make_paths_dir_relative(source_roots, dirname)))

    pyls = PythonLanguageServer(StringIO, StringIO)
    pyls.m_initialize(
        processId=1,
        rootUri=uris.from_fs_path(root_path),
        initializationOptions={}
    )

    if not metafile:
        # configured by client via LSP after pyls startup
        pyls.m_workspace__did_change_configuration({
            'pyls': {'source_roots': source_roots},
        })

    # put new document under ROOT/service/foo
    test_uri = uris.from_fs_path(os.path.join(root_path, doc_root, 'hello/test.py'))
    pyls.workspace.put_document(test_uri, 'assert true')
    test_doc = pyls.workspace.get_document(test_uri)

    # apply os.path.normcase() on paths below, because case-sensitive
    # comparison on Windows causes unintentional failure for case
    # instability around drive letter

    sys_path = [os.path.normcase(p) for p in test_doc.sys_path()]
    for raw_path in source_roots:
        full_path = os.path.normcase(os.path.join(root_path, raw_path))
        if raw_path in invalid_roots:
            assert os.path.normpath(full_path) not in sys_path
            assert full_path not in sys_path  # check for safety
        else:
            assert os.path.normpath(full_path) in sys_path


@pytest.mark.parametrize('metafile', ['setup.cfg', 'tox.ini'])
def test_pyls_config_readin(tmpdir, metafile):
    """Examine that pyls config in the workspace root is always read in.

    This test creates two config files. One is created in the
    workspace root, and another is created in ascendant of the target
    document. Only the former has source_roots config.

    Then, this test examines that the former is always read in,
    regardless of existence of the latter, by checking source_roots
    config.
    """
    root_path = str(tmpdir)

    source_roots = ['service/foo', 'service/bar']

    with open(os.path.join(root_path, metafile), 'w+') as f:
        f.write('[pyls]\nsource_roots=\n    %s\n' %
                ',\n    '.join(source_roots))

    doc_root = source_roots[0]

    os.makedirs(os.path.join(root_path, doc_root))
    with open(os.path.join(root_path, doc_root, metafile), 'w+') as f:
        f.write('\n')

    pyls = PythonLanguageServer(StringIO, StringIO)
    pyls.m_initialize(
        processId=1,
        rootUri=uris.from_fs_path(root_path),
        initializationOptions={}
    )

    # put new document under root/service/foo
    test_uri = uris.from_fs_path(os.path.join(root_path, doc_root, 'hello/test.py'))
    pyls.workspace.put_document(test_uri, 'assert True')
    test_doc = pyls.workspace.get_document(test_uri)

    # apply os.path.normcase() on paths below, because case-sensitive
    # comparison on Windows causes unintentional failure for case
    # instability around drive letter

    sys_path = [os.path.normcase(p) for p in test_doc.sys_path()]
    for raw_path in source_roots:
        full_path = os.path.normcase(os.path.join(root_path, raw_path))
        assert os.path.normpath(full_path) in sys_path


@pytest.mark.parametrize('metafile', [
    'setup.cfg',
    'tox.ini',
    'service/foo/setup.cfg',
    'service/foo/tox.ini',
    None,
])
def test_jedi_extra_paths_config(tmpdir, metafile):
    """Examine that plugins.jedi.extra_paths config is intentionaly read in.

    This test also examines below for entries in plugins.jedi.extra_paths:

    * relative path is:
      - treated as relative to config file location, and
      - normalized into absolute one
    """
    root_path = str(tmpdir)

    extra_paths = ['extra/foo', 'extra/bar', '/absolute/root', '../baz']
    doc_root = 'service/foo'

    if metafile:
        dirname = os.path.dirname(metafile)
        if dirname:
            os.makedirs(os.path.join(root_path, dirname))

        # configured by metafile at pyls startup
        with open(os.path.join(root_path, metafile), 'w+') as f:
            f.write('[pyls]\nplugins.jedi.extra_paths=\n    %s\n' %
                    ',\n    '.join(_make_paths_dir_relative(extra_paths, dirname)))

    pyls = PythonLanguageServer(StringIO, StringIO)
    pyls.m_initialize(
        processId=1,
        rootUri=uris.from_fs_path(root_path),
        initializationOptions={}
    )

    if not metafile:
        # configured by client via LSP after pyls startup
        pyls.m_workspace__did_change_configuration({
            'pyls': {'plugins': {'jedi': {'extra_paths': extra_paths}}},
        })

    # put new document under ROOT/service/foo
    test_uri = uris.from_fs_path(os.path.join(root_path, doc_root, 'hello/test.py'))
    pyls.workspace.put_document(test_uri, 'assert true')
    test_doc = pyls.workspace.get_document(test_uri)

    # apply os.path.normcase() on paths below, because case-sensitive
    # comparison on Windows causes unintentional failure for case
    # instability around drive letter

    sys_path = [os.path.normcase(p) for p in test_doc.sys_path()]
    for raw_path in extra_paths:
        full_path = os.path.normcase(os.path.join(root_path, raw_path))
        assert os.path.normpath(full_path) in sys_path
