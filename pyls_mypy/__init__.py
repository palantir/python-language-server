from future.standard_library import install_aliases
from ._version import get_versions

install_aliases()
__version__ = get_versions()['version']
del get_versions
