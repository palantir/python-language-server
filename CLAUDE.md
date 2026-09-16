# CLAUDE.md

Guidance for [Claude Code](https://claude.com/claude-code) when working in this repository.

## What this repository is

`pyls` is an implementation of the Language Server Protocol for Python. An editor speaks JSON-RPC to it over stdio or TCP; the server parses each open document and answers completion, definition, hover, reference, symbol and formatting requests, mostly by delegating to Jedi and to linters loaded as pluggy plugins.

Two things shape almost every decision here:

- **It still targets Python 2.7.** `setup.py` carries `python_version<"3"` markers and CI runs a 2.7 job. That rules out f-strings, and it is why source literals in tests carry `u''` prefixes.
- **Jedi is pinned below 0.18** (`jedi>=0.17.2,<0.18.0`). The 0.18 release changed the `Script` API, so the pin is load-bearing, not incidental.

Development here has been quiet since December 2020 — the most recent commit is an automated config change — and the actively maintained community fork is `python-lsp-server`. Worth knowing before promising a change will ship, but this repository is not archived and still accepts issues and PRs.

## Setting up an environment that works

**A modern interpreter will not work.** CI runs 2.7, 3.6, 3.7 and 3.8, and the pinned Jedi does not install on recent Pythons. Use 3.8:

```
uv python install 3.8
uv venv --python 3.8 /tmp/pls
uv pip install --python /tmp/pls/bin/python -e ".[all,test]"
uv pip install --python /tmp/pls/bin/python "setuptools<70" "pylint<3"
```

The last line is not optional:

- `pyls/config/config.py` imports `pkg_resources`, which setuptools 70+ no longer ships.
- `test/plugins/test_pylint_lint.py` imports `pylint.epylint`, removed in pylint 3.

## Commands

These are the four steps CI runs, in order:

```
/tmp/pls/bin/python -m pytest test/ -q
/tmp/pls/bin/python -m pylint pyls test
/tmp/pls/bin/python -m pycodestyle pyls test
/tmp/pls/bin/python -m pyflakes pyls test
```

**A clean checkout does not produce a clean run.** Record a baseline before changing anything and compare against it, rather than assuming a failure is yours. On Python 3.8 with current dependency versions a clean checkout gives roughly **12 failed, 99 passed, 8 skipped**, concentrated in the flake8, pydocstyle, pylint and numpy-hover tests — these track linter versions that have moved on since 2020. `pylint pyls test` reports around 84 messages and `pyflakes` reports an undefined `unicode` in `pyls/_utils.py`, both pre-existing.

## URIs are not always files

A document is identified by a URI, and **not every URI has a file behind it**. Editors such as Monaco send `inmemory://dummy.py`, and VS Code sends `untitled:` and `vscode-notebook-cell:`; the contents of those documents only ever arrive over `textDocument/didOpen` and `didChange`.

- `uris.to_fs_path()` returns a path-shaped **identifier**. For a non-file URI it is not a location on disk and must not be opened, walked, or used to derive a directory.
- `uris.is_file_uri()` is the check to use before doing anything filesystem-flavoured with `Document.path`, and `Document.is_file_backed` caches it.
- Note that `inmemory://dummy.py` puts `dummy.py` in the URI *authority*, not the path, so `urlparse` yields an empty path for it. That is a normal shape, not a malformed URI.

Anything that computes `os.path.dirname(document.path)` and feeds it to Jedi, rope or a linter needs to be guarded by `is_file_backed`. An unguarded `dirname` of a non-file document used to normalize to `'.'`, which silently put the server's working directory on the module search path.

## Conventions

- **Every source file starts with `# Copyright 2017 Palantir Technologies, Inc.`** Copy it from a neighbouring file.
- **Write Python 2/3 compatible code.** No f-strings; use `.format()`. `pylint` will suggest `consider-using-f-string` anyway — that suggestion does not apply here.
- **Plugins are pluggy hooks** registered as entry points in `setup.py`. Adding a plugin means adding both the module and its `pyls` entry point.
- **Tests use plain pytest with fixtures in `test/fixtures.py`** (`workspace`, `doc`, `config`, `pyls`), re-exported through `test/conftest.py`. `from test.fixtures import ...` is deliberately the first import in a test module: `test` shadows a stdlib name, so pylint sorts it as a standard import and reports `wrong-import-order` if anything precedes it.

## Things to be careful about

- **Do not "modernize" the codebase.** Removing `u''` prefixes, `object` base classes or `.format()` calls breaks the Python 2.7 job.
- **Do not bump Jedi past 0.18** without reworking `Document.jedi_script`; the `Script` constructor signature changed.
- **`pyls/uris.py` mirrors VS Code's `vscode-uri`** and says so. If you diverge from it, say why in a comment, because the next reader will check the two against each other.
- **Changing `to_fs_path` affects everything.** It feeds `Document.path`, the workspace root, config discovery and most plugins. Verify plugin behaviour, not just the URI unit tests.
