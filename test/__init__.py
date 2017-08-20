# Copyright 2017 Palantir Technologies, Inc.
import pytest
from pyls import IS_WIN

windows_only = pytest.mark.skipif(not IS_WIN, reason="Windows only")
