from ._version import get_versions
import sys

if sys.version_info[0] < 3:
    from future.standard_library import install_aliases
    install_aliases()

__version__ = get_versions()['version']
del get_versions
