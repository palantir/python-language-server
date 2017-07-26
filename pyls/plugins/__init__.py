# Copyright 2017 Palantir Technologies, Inc.
from . import (
    completion, definition, format,
    hover, pyflakes_lint, pycodestyle_lint,
    references, symbols, signature
)


CORE_PLUGINS = [
    completion, definition, format, hover, pyflakes_lint, pycodestyle_lint,
    references, symbols, signature
]
