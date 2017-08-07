# Copyright 2017 Palantir Technologies, Inc.
from . import (
    completion, definition, format,
    hover, pyflakes_lint, pycodestyle_lint,
    references, signature, symbols
)


CORE_PLUGINS = [
    completion, definition, format, hover, pyflakes_lint, pycodestyle_lint,
    references, signature, symbols
]
