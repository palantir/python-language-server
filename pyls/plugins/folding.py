# pylint: disable=len-as-condition,no-member

import sys
import ast

from pyls import hookimpl

OLD_AST = (sys.version_info.major, sys.version_info.minor) <= (3, 2)
if OLD_AST:
    Try = (ast.TryFinally, ast.TryExcept)
else:
    Try = ast.Try


def __update_if_try(ctx, tree_nodes, folding_starts, folding_ranges,
                    folding_ends, line, col):
    ctx_id = ctx[0]
    common_node = tree_nodes[ctx_id]
    if isinstance(common_node, (ast.If, Try)):
        if ctx_id in folding_starts:
            node_start = folding_starts[ctx_id]
            ctx_line, _ = node_start
            if ctx_line < line:
                folding_starts.pop(ctx_id)
                folding_ranges.append((node_start, (line, col)))
                folding_ends[ctx_id] = (line, col)
        else:
            folding_ends[ctx_id] = (line, col)


def __update_folding_ranges(ctx, stack, line, col, folding_starts,
                            folding_ends, tree_nodes, folding_ranges):
    _, next_ctx = stack[0]
    while ctx != next_ctx:
        this_ctx = ctx.pop(0)
        if this_ctx in folding_starts:
            ctx_start = folding_starts.pop(this_ctx)
            ctx_line, _ = ctx_start
            if ctx_line < line:
                folding_ranges.append((ctx_start, (line, col)))
        elif this_ctx in folding_ends:
            ctx_line, _ = folding_ends[this_ctx]
            folding_ranges.append(((ctx_line + 1, 0), (line, col)))
            node = tree_nodes[this_ctx]
            if isinstance(node, Try):
                continue
            else:
                break
    if ctx == next_ctx:
        __update_if_try(ctx, tree_nodes, folding_starts, folding_ranges,
                        folding_ends, line, col)
    return folding_ranges


def __reduce_folding_ranges(folding_ranges):
    actual_ranges = []
    i = 0
    while i < len(folding_ranges) - 1:
        ((left_line, _), left_end) = folding_ranges[i]
        ((right_line, _), right_end) = folding_ranges[i + 1]
        if left_line == right_line and left_end == right_end:
            actual_ranges.append(folding_ranges[i + 1])
            i += 2
        elif left_line == right_line:
            actual_ranges.append(folding_ranges[i])
            i += 2
        else:
            actual_ranges.append(folding_ranges[i])
            i += 1

    if i == len(folding_ranges) - 1:
        actual_ranges.append(folding_ranges[i])
    return actual_ranges


def __compute_folding_ranges(tree):
    folding_ranges = []
    folding_starts = {}
    folding_ends = {}
    tree_nodes = {}

    stack = [(tree, [])]
    while len(stack) > 0:
        node, ctx = stack.pop(0)
        node_id = id(node)
        tree_nodes[node_id] = node
        if hasattr(node, 'lineno'):
            line, col = node.lineno, node.col_offset
            folding_starts[node_id] = (line, col)
        nodes = []
        new_ctx = list([node_id] + ctx)
        for child in ast.iter_child_nodes(node):
            nodes.append((child, new_ctx))
        stack = nodes + stack

        if len(nodes) == 0:
            if len(stack) > 0:
                folding_ranges = __update_folding_ranges(
                    ctx, stack, line, col, folding_starts, folding_ends,
                    tree_nodes, folding_ranges)

    folding_ranges = sorted(folding_ranges)
    ranges = __reduce_folding_ranges(folding_ranges)
    return ranges


@hookimpl
def pyls_folding_range(document):
    program = str(document.source)
    # Add an additional "pass" to ensure that there's always a next node
    program = program + '\n\npass'
    tree = None
    lines = []
    reparsing = False
    while tree is None:
        try:
            tree = ast.parse(program)
        except SyntaxError as e:
            offending_line = e.lineno
            lines = program.splitlines(True)
            lines = lines[:offending_line - 1]
            program = ''.join(lines)
            reparsing = True

    # Parse again to add additional node
    if reparsing:
        program = program + '\n\npass'
        tree = ast.parse(program)

    ranges = __compute_folding_ranges(tree)

    results = []
    for ((start_line, _), (end_line, _)) in ranges:
        start_line -= 1
        end_line -= 1
        # If start/end character is not defined, then it defaults to the
        # corresponding line last character
        results.append({
            'startLine': start_line,
            'endLine': end_line,
        })
    return results
