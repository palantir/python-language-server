Python Language Server
======================

.. image:: https://circleci.com/gh/palantir/python-language-server.svg?style=shield
    :target: https://circleci.com/gh/palantir/python-language-server

.. image:: https://ci.appveyor.com/api/projects/status/mdacv6fnif7wonl0?svg=true
    :target: https://ci.appveyor.com/project/gatesn/python-language-server

.. image:: https://img.shields.io/github/license/palantir/python-language-server.svg
     :target: https://github.com/palantir/python-language-server/blob/master/LICENSE

A Python 2.7 and 3.5+ implementation of the `Language Server Protocol`_.

Installation
------------

The base language server requires Jedi_ to provide Completions, Definitions, Hover, References, Signature Help, and
Symbols:

``pip install python-language-server``

If the respective dependencies are found, the following optional providers will be enabled:

* Rope_ for Completions and renaming
* Pyflakes_ linter to detect various errors
* McCabe_ linter for complexity checking
* pycodestyle_ linter for style checking
* pydocstyle_ linter for docstring style checking (disabled by default)
* autopep8_ for code formatting
* YAPF_ for code formatting (preferred over autopep8)

Optional providers can be installed using the `extras` syntax. To install YAPF_ formatting for example:

``pip install 'python-language-server[yapf]'``

All optional providers can be installed using:

``pip install 'python-language-server[all]'``

If you get an error similar to ``'install_requires' must be a string or list of strings`` then please upgrade setuptools before trying again. 

``pip install -U setuptools``

3rd Party Plugins
~~~~~~~~~~~~~~~~~
Installing these plugins will add extra functionality to the language server:

* pyls-mypy_ Mypy type checking for Python 3
* pyls-isort_ Isort import sort code formatting
* pyls-black_ for code formatting using Black_

Please see the above repositories for examples on how to write plugins for the Python Language Server. Please file an
issue if you require assistance writing a plugin.

Configuration
-------------

Location of Configuration File
~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~

There are three configuration levels below.

* user-level configuration (e.g. ~/.config/CONFIGFILE)
* lsp-level configuration (via LSP didChangeConfiguration method)
* project-level configuration

The latter level has priority over the former.

As project-level configuration, configurations are read in from files
in the root of the workspace, by default. What files are read in is
described after.

At evaluation of python source file ``foo/bar/baz/example.py`` for
example, if there is any configuration file in the ascendant directory
(i.e. ``foo``, ``foo/bar`` or ``foo/bar/baz``), it is read in before
evaluation. If multiple ascendant directories contain configuration
files, files only in the nearest ascendant directory are read in.

In some cases, automatically discovered files are exclusive with files
in the root of the workspace.

Syntax in Configuration File
~~~~~~~~~~~~~~~~~~~~~~~~~~~~

Configuration file should be written in "INI file" syntax.

Value specified in configuration file should be one of types below.

* bool
* int
* string
* list

"List" value is string entries joined with comma. Both leading and
trailing white spaces of each entries in a "list" value are trimmed.

Source Roots
~~~~~~~~~~~~

"Source roots" is determined in the order below.

1. if ``pyls.source_roots`` (described after) is specified, its value
   is used as "source roots"
2. if any of setup.py or pyproject.toml is found in the ascendant
   directory of python source file at evaluation, that directory is
   treated as "source roots"
3. otherwise, the root of the workspace is treated as "source roots"

"Source roots" is used as a part of sys path at evaluation of python
source files.

Python Language Server Specific Configuration
~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~

lsp-level and project-level configuration are supported for Python
Language Server specific configuration.

For project-level configuration, setup.cfg and tox.ini are read in.
Configuration files discovered automatically at evaluation of python
source file are **not** exclusive with configuration files in the root
of the workspace. Files in both locations are read in, and a
configuration in the former files has priority over one in the latter.

Python Language Server specific configurations are show below.

* ``pyls.source_roots`` (list) to specify source roots
* ``pyls.plugins.jedi.extra_paths`` (list) to specify extra sys paths

Relative path in these configurations is treated as relative to the
directory, in which configuration file exists. For configuration via
LSP didChangeConfiguration method, the root of the workspace is used
as base directory.

Path in ``pyls.source_roots`` is ignored, if it refers outside of the
workspace.

To make these configurations persisted into setup.cfg or tox.ini,
describe them under ``[pyls]`` section like below.

.. code-block:: ini

    [pyls]
    source_roots = services/foo, services/bar
    plugins.jedi.extra_paths = ../extra_libs


Configuration at Source Code Evaluation
~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~

Configuration is loaded from zero or more configuration sources. Currently implemented are:

* pycodestyle: discovered in ~/.config/pycodestyle, setup.cfg, tox.ini and pycodestyle.cfg.
* flake8: discovered in ~/.config/flake8, setup.cfg, tox.ini and flake8.cfg

The default configuration source is pycodestyle. Change the `pyls.configurationSources` setting to `['flake8']` in
order to respect flake8 configuration instead.

Overall configuration is computed first from user configuration (in home directory), overridden by configuration
passed in by the language client, and then overriden by configuration discovered in the workspace.

Configuration files discovered in the workspace automatically at
evaluation of python source file are exclusive with configuration
files in the root of the workspace.

To enable pydocstyle for linting docstrings add the following setting in your LSP configuration:
```
"pyls.plugins.pydocstyle.enabled": true
```

See `vscode-client/package.json`_ for the full set of supported configuration options.

.. _vscode-client/package.json: vscode-client/package.json

Language Server Features
------------------------

Auto Completion:

.. image:: https://raw.githubusercontent.com/palantir/python-language-server/develop/resources/auto-complete.gif

Code Linting with pycodestyle and pyflakes:

.. image:: https://raw.githubusercontent.com/palantir/python-language-server/develop/resources/linting.gif

Signature Help:

.. image:: https://raw.githubusercontent.com/palantir/python-language-server/develop/resources/signature-help.gif

Go to definition:

.. image:: https://raw.githubusercontent.com/palantir/python-language-server/develop/resources/goto-definition.gif

Hover:

.. image:: https://raw.githubusercontent.com/palantir/python-language-server/develop/resources/hover.gif

Find References:

.. image:: https://raw.githubusercontent.com/palantir/python-language-server/develop/resources/references.gif

Document Symbols:

.. image:: https://raw.githubusercontent.com/palantir/python-language-server/develop/resources/document-symbols.gif

Document Formatting:

.. image:: https://raw.githubusercontent.com/palantir/python-language-server/develop/resources/document-format.gif

Development
-----------

To run the test suite:

``pip install .[test] && pytest``

Develop against VS Code
=======================

The Python language server can be developed against a local instance of Visual Studio Code.

Install `VSCode <https://code.visualstudio.com/download>`_

.. code-block:: bash

    # Setup a virtual env
    virtualenv env
    . env/bin/activate

    # Install pyls
    pip install .

    # Install the vscode-client extension
    cd vscode-client
    yarn install

    # Run VSCode which is configured to use pyls
    # See the bottom of vscode-client/src/extension.ts for info
    yarn run vscode -- $PWD/../

Then to debug, click View -> Output and in the dropdown will be pyls.
To refresh VSCode, press `Cmd + r`

License
-------

This project is made available under the MIT License.

.. _Language Server Protocol: https://github.com/Microsoft/language-server-protocol
.. _Jedi: https://github.com/davidhalter/jedi
.. _Rope: https://github.com/python-rope/rope
.. _Pyflakes: https://github.com/PyCQA/pyflakes
.. _McCabe: https://github.com/PyCQA/mccabe
.. _pycodestyle: https://github.com/PyCQA/pycodestyle
.. _pydocstyle: https://github.com/PyCQA/pydocstyle
.. _YAPF: https://github.com/google/yapf
.. _autopep8: https://github.com/hhatto/autopep8
.. _pyls-mypy: https://github.com/tomv564/pyls-mypy
.. _pyls-isort: https://github.com/paradoxxxzero/pyls-isort
.. _pyls-black: https://github.com/rupert/pyls-black
.. _Black: https://github.com/ambv/black
