# Copyright 2017 Palantir Technologies, Inc.
from urllib.parse import splittype
from urllib.parse import urljoin
from urllib.request import pathname2url
from urllib.request import url2pathname


def path2uri(path):
    """Convert an OS specific local filename to an uri.

    Windows:
        C:\dir\file.py  -> file:///C:/dir/file.py
    Linux:
        /dir/file.py    -> file:/dir/file.py
    """
    return urljoin('file:', pathname2url(path or ""))


def uri2path(uri: str) -> str:
    """Convert an uri to a OS specific local filename.

    Windows:
        file:///C:/dir/file.py  ->  C:\dir\file.py
    Linux:
        file:/dir/file.py       ->  /dir/file.py
    """
    type, path = splittype(uri or "")
    return url2pathname(path)
