"""Linter plugin for costly spark calls."""
import logging
import sys
import ast
import collections

from pylint.epylint import py_run
from pyls import hookimpl, lsp


class SparkCostAnalyzer(ast.NodeVisitor):
    
    antipattern_func_names = [
        "collect"
    ]
    
    stats = []

    def visit_Call(self, node):
        func = node.func
        if type(func) == ast.Attribute:
            func_name = func.attr
            args = node.args
            if len(args) == 0 and func_name in self.antipattern_func_names:
                self.stats.append({
                    "message": "Costly spark method call found",
                    "symbol": func_name,
                    "severity": lsp.DiagnosticSeverity.Information,
                    "line": node.lineno,
                    "column": node.col_offset,
                    "message-id": "costly-spark-method"
                })

try:
    import ujson as json
except Exception:  # pylint: disable=broad-except
    import json

log = logging.getLogger(__name__)


class SparkCostChecker(object):
    last_diags = collections.defaultdict(list)

    @classmethod
    def lint(cls, document, is_saved):
        """Plugin interface to Spark Cost Checker linter.

        Args:
            document: The document to be linted.
            is_saved: Whether or not the file has been saved to disk.

        Returns:
            A list of dicts with the following format:

                {
                    'source': 'spark_cost_checker',
                    'range': {
                        'start': {
                            'line': start_line,
                            'character': start_column,
                        },
                        'end': {
                            'line': end_line,
                            'character': end_column,
                        },
                    }
                    'message': msg,
                    'severity': lsp.DiagnosticSeverity.*,
                }
        """
        if not is_saved:
            # AST can only be run on files that have been saved to disk.
            # Rather than return nothing, return the previous list of
            # diagnostics. If we return an empty list, any diagnostics we'd
            # previously shown will be cleared until the next save. Instead,
            # continue showing (possibly stale) diagnostics until the next
            # save.
            return cls.last_diags[document.path]

        # py_run will call shlex.split on its arguments, and shlex.split does
        # not handle Windows paths (it will try to perform escaping). Turn
        # backslashes into forward slashes first to avoid this issue.
        path = document.path
        if sys.platform.startswith('win'):
            path = path.replace('\\', '/')
            
        with open(path, "r") as source:
          tree = ast.parse(source.read())

        analyzer = SparkCostAnalyzer()
        analyzer.visit(tree)
        found_issues = analyzer.stats

        # The CostChecker's found_issues will be empty if nothing problematic is found
        if len(found_issues) == 0:
            cls.last_diags[document.path] = []
            return []

        diagnostics = []
        for diag in found_issues:
            # pylint lines index from 1, pyls lines index from 0
            line = diag['line'] - 1

            err_range = {
                'start': {
                    'line': line,
                    # Index columns start from 0
                    'character': diag['column'],
                },
                'end': {
                    'line': line,
                    # It's possible that we're linting an empty file. Even an empty
                    # file might fail linting if it isn't named properly.
                    'character': len(document.lines[line]) if document.lines else 0,
                },
            }

            diagnostics.append({
                'source': 'spark_cost_checker',
                'range': err_range,
                'message': '[{}] {}'.format(diag['symbol'], diag['message']),
                'severity': diag['severity'],
                'code': diag['message-id']
            })
        cls.last_diags[document.path] = diagnostics
        return diagnostics


@hookimpl
def pyls_settings():
    # Default pylint to disabled because it requires a config
    # file to be useful.
    return {'plugins': {'spark_cost_checker': {'enabled': False, 'args': []}}}


@hookimpl
def pyls_lint(config, document, is_saved):
    settings = config.plugin_settings('spark_cost_checker')
    log.debug("Got Spark Cost Checker settings: %s", settings)
    return SparkCostChecker.lint(document, is_saved)
