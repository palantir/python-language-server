# Copyright 2018 Palantir Technologies, Inc.
import logging
from pyls import hookimpl, lsp

log = logging.getLogger(__name__)


@hookimpl
def pyls_completions(document, position):
    # Rope is a bit rubbish at completing module imports, so we'll return None
    word = document.word_at_position({
        # The -1 should really be trying to look at the previous word, but that might be quite expensive
        # So we only skip import completions when the cursor is one space after `import`
        'line': position['line'], 'character': max(position['character'] - 1, 0),
    })
    if word == 'import':
        return None


{
    "if": {
        "prefix": "if",
        "body": [
            "if ${1:expression}:",
            "\t${2:pass}"
        ],
        "description": "Code snippet for an if statement"
    },
    "if/else": {
        "prefix": "if/else",
        "body": [
            "if ${1:condition}:",
            "\t${2:pass}",
            "else:",
            "\t${3:pass}"
        ],
        "description": "Code snippet for an if statement with else"
    },
    "elif": {
        "prefix": "elif",
        "body": [
            "elif ${1:expression}:",
            "\t${2:pass}"
        ],
        "description": "Code snippet for an elif"
    },
    "else": {
        "prefix": "else",
        "body": [
            "else:",
            "\t${1:pass}"
        ],
        "description": "Code snippet for an else"
    },
    "while": {
        "prefix": "while",
        "body": [
            "while ${1:expression}:",
            "\t${2:pass}"
        ],
        "description": "Code snippet for a while loop"
    },
    "while/else": {
        "prefix": "while/else",
        "body": [
            "while ${1:expression}:",
            "\t${2:pass}",
            "else:",
            "\t${3:pass}"
        ],
        "description": "Code snippet for a while loop with else"
    },
    "for": {
        "prefix": "for",
        "body": [
            "for ${1:target_list} in ${2:expression_list}:",
            "\t${3:pass}"
        ],
        "description": "Code snippet for a for loop"
    },
    "for/else": {
        "prefix": "for/else",
        "body": [
            "for ${1:target_list} in ${2:expression_list}:",
            "\t${3:pass}",
            "else:",
            "\t${4:pass}"
        ],
        "description": "Code snippet for a for loop with else"
    },
    "try/except": {
        "prefix": "try/except",
        "body": [
            "try:",
            "\t${1:pass}",
            "except ${2:expression} as ${3:identifier}:",
            "\t${4:pass}"
        ],
        "description": "Code snippet for a try/except statement"
    },
    "try/finally": {
        "prefix": "try/finally",
        "body": [
            "try:",
            "\t${1:pass}",
            "finally:",
            "\t${2:pass}"
        ],
        "description": "Code snippet for a try/finally statement"
    },
    "try/except/else": {
        "prefix": "try/except/else",
        "body": [
            "try:",
            "\t${1:pass}",
            "except ${2:expression} as ${3:identifier}:",
            "\t${4:pass}",
            "else:",
            "\t${5:pass}"
        ],
        "description": "Code snippet for a try/except/else statement"
    },
    "try/except/finally": {
        "prefix": "try/except/finally",
        "body": [
            "try:",
            "\t${1:pass}",
            "except ${2:expression} as ${3:identifier}:",
            "\t${4:pass}",
            "finally:",
            "\t${5:pass}"
        ],
        "description": "Code snippet for a try/except/finally statement"
    },
    "try/except/else/finally": {
        "prefix": "try/except/else/finally",
        "body": [
            "try:",
            "\t${1:pass}",
            "except ${2:expression} as ${3:identifier}:",
            "\t${4:pass}",
            "else:",
            "\t${5:pass}",
            "finally:",
            "\t${6:pass}"
        ],
        "description": "Code snippet for a try/except/else/finally statement"
    },
    "with": {
        "prefix": "with",
        "body": [
            "with ${1:expression} as ${2:target}:",
            "\t${3:pass}"
        ],
        "description": "Code snippet for a with statement"
    },
    "def": {
        "prefix": "def",
        "body": [
            "def ${1:funcname}(${2:parameter_list}):",
            "\t${3:pass}"
        ],
        "description": "Code snippet for a function definition"
    },
    "def(class method)": {
        "prefix": "def(class method)",
        "body": [
            "def ${1:funcname}(self, ${2:parameter_list}):",
            "\t${3:pass}"
        ],
        "description": "Code snippet for a class method"
    },
    "def(static class method)": {
        "prefix": "def(static class method)",
        "body": [
            "@staticmethod",
            "def ${1:funcname}(${2:parameter_list}):",
            "\t${3:pass}"
        ],
        "description": "Code snippet for a static class method"
    },
    "def(abstract class method)": {
        "prefix": "def(abstract class method)",
        "body": [
            "def ${1:funcname}(self, ${2:parameter_list}):",
            "\traise NotImplementedError"
        ],
        "description": "Code snippet for an abstract class method"
    },
    "class": {
        "prefix": "class",
        "body": [
            "class ${1:classname}(${2:object}):",
            "\t${3:pass}"
        ],
        "description": "Code snippet for a class definition"
    },
    "lambda": {
        "prefix": "lambda",
        "body": [
            "lambda ${1:parameter_list}: ${2:expression}"
        ],
        "description": "Code snippet for a lambda statement"
    },
    "if(main)": {
        "prefix": "if(main)",
        "body": [
            "def main():",
            "\t${1:pass}",
            "",
            "if __name__ == '__main__':",
            "\tmain()"
        ],
        "description": "Code snippet for a main function"
    },
    "async/def": {
        "prefix": "async/def",
        "body": [
            "async def ${1:funcname}(${2:parameter_list}):",
            "\t${3:pass}"
        ],
        "description": "Code snippet for an async statement"
    },
    "async/for": {
        "prefix": "async/for",
        "body": [
            "async for ${1:target} in ${2:iter}:",
            "\t${3:block}"
        ],
        "description": "Code snippet for an async for statement"
    },
    "async/for/else": {
        "prefix": "async/for/else",
        "body": [
            "async for ${1:target} in ${2:iter}:",
            "\t${3:block}",
            "else:",
            "\t${4:block}"
        ],
        "description": "Code snippet for an async for statement with else"
    },
    "async/with": {
        "prefix": "async/with",
        "body": [
            "async with ${1:expr} as ${2:var}:",
            "\t${3:block}"
        ],
        "description": "Code snippet for an async with statement"
    },
    "ipdb": {
        "prefix": "ipdb",
        "body": "import ipdb; ipdb.set_trace()",
        "description": "Code snippet for ipdb debug"
    },
    "pdb": {
        "prefix": "pdb",
        "body": "import pdb; pdb.set_trace()",
        "description": "Code snippet for pdb debug"
    },
    "pudb": {
        "prefix": "pudb",
        "body": "import pudb; pudb.set_trace()",
        "description": "Code snippet for pudb debug"
    },
}
