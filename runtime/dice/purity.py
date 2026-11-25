#!/usr/bin/env python3

"""Purity metadata and DSL purity analysis.

This module is the source of truth for operator purity. It also leaves a seam
for a future refactor: if we want deeper static analysis later, it may be worth
lowering operator AST nodes into builtin function calls where span-preserving
rewriting is practical.
"""

from __future__ import annotations

from dataclasses import dataclass

from .lexer import (
    ADV,
    ASSIGN,
    AVG,
    CARET,
    DIS,
    DIV,
    ELSE,
    EQUAL,
    FLOORDIV,
    GREATER,
    GREATER_OR_EQUAL,
    HIGH,
    IN,
    LESS,
    LESS_OR_EQUAL,
    LOW,
    MINUS,
    MUL,
    PLUS,
    PRINT,
    PROP,
    RES,
    ROLL,
    SEMI,
)


@dataclass(frozen=True)
class OperatorPurity:
    logical_name: str
    pure: bool


UNARY_OPERATOR_PURITY = {
    ROLL: OperatorPurity("rollsingle", True),
    ADV: OperatorPurity("rolladvantage", True),
    DIS: OperatorPurity("rolldisadvantage", True),
    AVG: OperatorPurity("mean", True),
    PROP: OperatorPurity("sample", False),
    MINUS: OperatorPurity("neg", True),
    PRINT: OperatorPurity("print", False),
}

BINARY_OPERATOR_PURITY = {
    PLUS: OperatorPurity("add", True),
    MINUS: OperatorPurity("sub", True),
    MUL: OperatorPurity("mul", True),
    CARET: OperatorPurity("repeat_sum", True),
    DIV: OperatorPurity("div", True),
    FLOORDIV: OperatorPurity("floordiv", True),
    ROLL: OperatorPurity("roll", True),
    GREATER_OR_EQUAL: OperatorPurity("greaterorequal", True),
    LESS_OR_EQUAL: OperatorPurity("lessorequal", True),
    GREATER: OperatorPurity("greater", True),
    LESS: OperatorPurity("less", True),
    EQUAL: OperatorPurity("equal", True),
    IN: OperatorPurity("member", True),
    RES: OperatorPurity("res", True),
    ASSIGN: OperatorPurity("assign", False),
}

TENARY_OPERATOR_PURITY = {
    (RES, ELSE): OperatorPurity("reselse", True),
    (ROLL, HIGH): OperatorPurity("rollhigh", True),
    (ROLL, LOW): OperatorPurity("rolllow", True),
}


class PurityAnalyzer:
    STATE_CHECKING = "checking"
    STATE_PURE = "pure"
    STATE_IMPURE = "impure"

    def __init__(self, interpreter):
        self.interpreter = interpreter
        self._function_states = {}

    def invalidate(self):
        self._function_states.clear()

    def function_is_pure(self, entry):
        if getattr(entry, "kind", None) != "dsl":
            return getattr(entry, "pure", False)
        return self._dsl_function_is_pure(entry, ())

    def _dsl_function_is_pure(self, entry, stack):
        state = self._function_states.get(entry.name)
        if state == self.STATE_PURE:
            return True
        if state == self.STATE_IMPURE:
            return False
        if state == self.STATE_CHECKING:
            cycle_start = stack.index(entry.name) if entry.name in stack else 0
            cycle = stack[cycle_start:] + (entry.name,)
            self.interpreter.exception(
                "Recursion not supported: recursive purity dependency detected: {}".format(" -> ".join(cycle)),
                node=entry.node,
                hint="Recursive dice functions are not supported yet.",
            )

        self._function_states[entry.name] = self.STATE_CHECKING
        next_stack = stack + (entry.name,)
        try:
            pure = self._function_node_is_pure(entry.node, next_stack)
        except Exception:
            self._function_states.pop(entry.name, None)
            raise
        self._function_states[entry.name] = self.STATE_PURE if pure else self.STATE_IMPURE
        return pure

    def _function_node_is_pure(self, node, stack):
        for param in node.params:
            if param.default is not None and not self.node_is_pure(param.default, stack):
                return False
        return self.node_is_pure(node.body, stack)

    def node_is_pure(self, node, stack):
        if node is None:
            return True
        if isinstance(node, list) or isinstance(node, tuple):
            return all(self.node_is_pure(item, stack) for item in node)

        node_type = type(node).__name__
        if node_type == "Val":
            return True
        if node_type == "Named":
            return self.node_is_pure(node.value, stack)
        if node_type == "CallArg":
            return self.node_is_pure(node.value, stack)
        if node_type == "LocalAssign":
            return self.node_is_pure(node.value, stack)
        if node_type == "BlockBody":
            return all(self.node_is_pure(statement, stack) for statement in node.statements) and self.node_is_pure(
                node.result, stack
            )
        if node_type == "VarOp":
            if node.op.type != SEMI:
                self.interpreter.exception("{} not implemented".format(node), node=node)
            return all(self.node_is_pure(child, stack) for child in node.nodes if type(child).__name__ != "FunctionDef")
        if node_type == "UnOp":
            metadata = UNARY_OPERATOR_PURITY.get(node.op.type)
            if metadata is None:
                self.interpreter.exception("{} not implemented".format(node), node=node)
            return self.node_is_pure(node.value, stack) and metadata.pure
        if node_type == "BinOp":
            metadata = BINARY_OPERATOR_PURITY.get(node.op.type)
            if metadata is None:
                self.interpreter.exception("{} not implemented".format(node), node=node)
            return self.node_is_pure(node.left, stack) and self.node_is_pure(node.right, stack) and metadata.pure
        if node_type == "TenOp":
            metadata = TENARY_OPERATOR_PURITY.get((node.op1.type, node.op2.type))
            if metadata is None:
                self.interpreter.exception("{} not implemented".format(node), node=node)
            return (
                self.node_is_pure(node.left, stack)
                and self.node_is_pure(node.middle, stack)
                and self.node_is_pure(node.right, stack)
                and metadata.pure
            )
        if node_type == "Call":
            arguments_are_pure = all(self.node_is_pure(arg, stack) for arg in node.args)
            if not arguments_are_pure:
                return False
            function_name = node.name.value
            if function_name in self.interpreter.callable_scope:
                return self._dsl_function_is_pure(self.interpreter.callable_scope[function_name], stack)
            if function_name in self.interpreter.executor.functions:
                return getattr(self.interpreter.executor.functions[function_name], "pure", False)
            self.interpreter.exception(
                "Unknown function {}".format(function_name),
                node=node,
                hint=self.interpreter._identifier_hint(function_name, prefer_call=True),
            )
        if node_type == "Split":
            if not self.node_is_pure(node.value, stack):
                return False
            return all(self.node_is_pure(clause, stack) for clause in node.clauses)
        if node_type == "SplitClause":
            condition_is_pure = node.otherwise or self.node_is_pure(node.condition, stack)
            return condition_is_pure and self.node_is_pure(node.result, stack)
        if node_type == "RangeLiteral":
            return self.node_is_pure(node.start, stack) and self.node_is_pure(node.end, stack)
        if node_type == "MeasureEntry":
            return self.node_is_pure(node.value, stack) and self.node_is_pure(node.weight, stack)
        if node_type == "MeasureLiteral":
            return all(self.node_is_pure(entry, stack) for entry in node.entries)
        if node_type == "SweepLiteral":
            return self.node_is_pure(node.values, stack)
        if node_type == "TupleLiteral":
            return all(self.node_is_pure(item, stack) for item in node.items)
        if node_type == "RecordEntry":
            return self.node_is_pure(node.value, stack)
        if node_type == "RecordLiteral":
            return all(self.node_is_pure(entry, stack) for entry in node.entries)
        if node_type == "SweepIndexCoordinate" or node_type == "SweepIndexFilter":
            return self.node_is_pure(node.value, stack)
        if node_type == "SweepIndex":
            return self.node_is_pure(node.value, stack) and all(
                self.node_is_pure(clause, stack) for clause in node.clauses
            )
        if node_type == "FunctionDef":
            return self._function_node_is_pure(node, stack)
        if node_type == "Import":
            return False

        self.interpreter.exception("purity analysis does not support {}".format(node_type), node=node)
