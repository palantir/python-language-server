# Copyright 2017 Palantir Technologies, Inc.
"""A collection of URI utilities with logic built on the VSCode URI library.

https://github.com/Microsoft/vscode-uri/blob/e59cab84f5df6265aed18ae5f43552d3eef13bb9/lib/index.ts
"""
import re
from urllib.parse import urlparse
from pyls import IS_WIN

RE_DRIVE_LETTER_PATH = re.compile(r'^\/[a-zA-z]:')
RE_SLASH = re.compile(r'\/')


def fs_path(uri):
    """Returns the filesystem path of the given URI.

    Will handle UNC paths and normalize windows drive letters to lower-case. Also
    uses the platform specific path separator. Will *not* validate the path for
    invalid characters and semantics. Will *not* look at the scheme of this URI.
    """
    # scheme://netloc/path;parameters?query#fragment
    scheme, netloc, path, _params, _query, _fragment = urlparse(uri)

    if netloc and path and scheme == 'file':
        # unc path: file://shares/c$/far/boo
        value = "//{netloc}{path}".format(netloc=netloc, path=path)

    elif RE_DRIVE_LETTER_PATH.match(path):
        # windows drive letter: file:///C:/far/boo
        value = path[1].lower() + path[2:]

    else:
        # Other path
        value = path

    if IS_WIN:
        value = RE_SLASH.sub('\\', value)

    return value
