Python Language Server
======================

.. image:: https://circleci.com/gh/palantir/python-language-server.svg?style=shield
    :target: https://circleci.com/gh/palantir/python-language-server

.. image:: https://ci.appveyor.com/api/projects/status/mdacv6fnif7wonl0?svg=true
    :target: https://ci.appveyor.com/project/gatesn/python-language-server

.. image:: https://img.shields.io/github/license/palantir/python-language-server.svg
     :target: https://github.com/palantir/python-language-server/blob/master/LICENSE

A Python 2.7 and 3.4+ implementation of the `Language Server Protocol`_ making use of Jedi_, pycodestyle_, Pyflakes_ and YAPF_.

Plugins
-------

Installing these plugins will add extra functionality to the language server:

* Mypy type checking (requires Python 3) - https://github.com/tomv564/pyls-mypy

Features
--------

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

Installation
------------

``pip install python-language-server``

Development
-----------

To run the test suite:

``pip install .[test] && tox``

Develop against VS Code
=======================

The Python language server can be developed against a local instance of Visual Studio Code.

1. Install `VSCode for Mac <http://code.visualstudio.com/docs/?dv=osx>`_
2. From within VSCode View -> Command Palette, then type *shell* and run ``install 'code' command in PATH``

.. code-block:: bash

    # Setup a virtual env
    virtualenv env
    . env/bin/activate

    # Install pyls
    pip install .

    # Install the vscode-client extension
    cd vscode-client
    npm install .

    # Run VSCode which is configured to use pyls
    # See the bottom of vscode-client/src/extension.ts for info
    npm run vscode -- $PWD/../

Then to debug, click View -> Output and in the dropdown will be pyls.
To refresh VSCode, press `Cmd + r`

License
-------

This project is made available under the MIT License.

.. _Language Server Protocol: https://github.com/Microsoft/language-server-protocol
.. _Jedi: https://github.com/davidhalter/jedi
.. _pycodestyle: https://github.com/PyCQA/pycodestyle
.. _Pyflakes: https://github.com/PyCQA/pyflakes
.. _YAPF: https://github.com/google/yapf
