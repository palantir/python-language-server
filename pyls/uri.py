from urllib.parse import urlparse, urlunparse
from urllib.request import url2pathname, pathname2url


def path_to_uri(doc_uri, path):
    """Replace the path in a uri. Little bit hacky!

    Due to https://github.com/PythonCharmers/python-future/issues/273 we have
    to cast all parts to the same type since jedi can return str and urlparse
    returns unicode objects.
    """
    parts = list(urlparse(doc_uri))
    parts[2] = pathname2url(path)
    return urlunparse([str(p) for p in parts])


def uri_to_path(uri: str) -> str:
    """Convert an uri to a OS specific local filename.

    Windows:
        file:///C:/dir/file.py  ->  C:\dir\file.py
    Linux:
        file:/dir/file.py       ->  /dir/file.py
    """
    return url2pathname(urlparse(uri).path)
