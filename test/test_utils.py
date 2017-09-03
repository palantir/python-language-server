# Copyright 2017 Palantir Technologies, Inc.
import time
from pyls import _utils


def test_debounce():
    interval = 0.1

    @_utils.debounce(0.1)
    def call_m():
        call_m._count += 1

    call_m._count = 0

    call_m()
    call_m()
    call_m()
    assert call_m._count == 0

    time.sleep(interval * 2)
    call_m()
    assert call_m._count == 1

    time.sleep(interval * 2)
    call_m()
    assert call_m._count == 2
