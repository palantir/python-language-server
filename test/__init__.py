# Copyright 2017 Palantir Technologies, Inc.
import pytest
from pyls import IS_WIN

unix_only = pytest.mark.skipif(IS_WIN, reason="Unix only")
windows_only = pytest.mark.skipif(not IS_WIN, reason="Windows only")
