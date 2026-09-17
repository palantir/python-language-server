# Contributing

## Contributor License Agreement

Before your pull request can be merged, you must sign Palantir's CLA at
https://cla.palantir.com/. The `palantirtech` bot will comment on your PR with
the link and will update the PR status once you've signed.

## Getting set up

    python -m venv env
    . env/bin/activate        # Windows: env\Scripts\activate
    pip install -e '.[all,test]'

## Running the tests

    pytest

Lint before you push — CI runs pylint with the repo's `.pylintrc`:

    pylint pyls test

Tests run on Linux, macOS and Windows via GitHub Actions. If your change is
platform-sensitive (paths, URIs, subprocesses), say so in the PR description.

## Branching

Base your work on `develop`, not `master`. Open the pull request against
`develop` as well.

## Making a change

- Keep commits focused; one logical change per PR.
- Add or update tests under `test/` for any behaviour change. Plugin tests live
  in `test/plugins/`.
- New functionality usually belongs in a plugin under `pyls/plugins/`. Register
  it in the `pyls` entry-point group in `setup.py`, and add its configuration
  schema to `vscode-client/package.json` so it's documented.
- Document any new configuration option in `README.rst`.

## Manual testing against VS Code

    cd vscode-client
    yarn install
    yarn run vscode -- $PWD/../

Server output appears under View -> Output -> pyls. `Cmd + r` reloads the window.

## Reporting bugs

Include your OS, Python version, `pyls` version, the editor/client you're using,
and the relevant `pyls` output log. A minimal file that reproduces the problem
helps a lot.

## Releases

Maintainers only — see `RELEASE.md`.
