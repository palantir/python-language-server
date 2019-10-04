#!/usr/bin/env python
from setuptools import find_packages, setup
import versioneer

setup(
    version=versioneer.get_version(),
    cmdclass=versioneer.get_cmdclass(),
)
