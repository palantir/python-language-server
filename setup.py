#!/usr/bin/env python
from setuptools import find_packages, setup
import versioneer

README = open('README.rst', 'r').read()


setup(
    name='python-language-server',

    # Versions should comply with PEP440.  For a discussion on single-sourcing
    # the version across setup.py and the project code, see
    # https://packaging.python.org/en/latest/single_source_version.html
    version=versioneer.get_version(),
    cmdclass=versioneer.get_cmdclass(),

    description='Python Language Server for the Language Server Protocol',

    long_description=README,

    # The project's main homepage.
    url='https://github.com/palantir/python-language-server',

    author='Palantir Technologies, Inc.',

    # You can just specify the packages manually here if your project is
    # simple. Or you can use find_packages().
    packages=find_packages(exclude=['contrib', 'docs', 'test']),

    # List run-time dependencies here.  These will be installed by pip when
    # your project is installed. For an analysis of "install_requires" vs pip's
    # requirements files see:
    # https://packaging.python.org/en/latest/requirements.html
    install_requires=[
        'configparser',
        'future',
        'jedi>=0.10',
        'json-rpc',
        'pycodestyle',
        'pyflakes',
        'yapf',
        'pluggy'
    ],

    # List additional groups of dependencies here (e.g. development
    # dependencies). You can install these using the following syntax,
    # for example:
    # $ pip install -e .[test]
    extras_require={
        'test': ['tox', 'versioneer', 'pytest', 'pytest-cov', 'coverage'],
    },

    # To provide executable scripts, use entry points in preference to the
    # "scripts" keyword. Entry points provide cross-platform support and allow
    # pip to create the appropriate form of executable for the target platform.
    entry_points={
        'console_scripts': [
            'pyls = pyls.__main__:main',
        ],
    },
)
