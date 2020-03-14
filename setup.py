#!/usr/bin/env python
from setuptools import setup
import versioneer

if __name__ == "__main__":
    setup(version=versioneer.get_version(), cmdclass=versioneer.get_cmdclass())
