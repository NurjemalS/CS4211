"""GIVEN conversion between the JSON protocol and typed model objects.

Only this file knows that the wire format uses short keys such as ``k``,
``l``, and ``r``.  The semantic functions work with named fields instead.
"""

from __future__ import annotations

from typing import Any, Dict, List, Mapping, cast

from model import (
    AExp,
    ArithmeticMode,
    ArithmeticOperator,
    ArrayRead,
    ArrayWrite,
    Assign,
    BExp,
    BinaryAExp,
    BinaryBExp,
    Bool,
    BooleanOperator,
    Choice,
    ClassifyResult,
    Command,
    Compare,
    ComparisonOperator,
    Configuration,
    Derivation,
    ExploreResult,
    If,
    Not,
    Num,
    Request,
    RequestMode,
    RunResult,
    SequenceCommand,
    Skip,
    State,
    Var,
    While,
)

JsonObject = Dict[str, Any]


def decode_aexp(raw: Mapping[str, Any]) -> AExp:
    kind = raw["k"]
    if kind == "num":
        return Num(int(raw["n"]))
    if kind == "var":
        return Var(str(raw["x"]))
    if kind == "aop":
        return BinaryAExp(
            ArithmeticOperator(raw["op"]),
            decode_aexp(raw["l"]),
            decode_aexp(raw["r"]),
        )
    if kind == "aget":
        return ArrayRead(str(raw["a"]), decode_aexp(raw["i"]))
    raise ValueError("unknown arithmetic-expression kind %r" % kind)


def decode_bexp(raw: Mapping[str, Any]) -> BExp:
    kind = raw["k"]
    if kind == "bool":
        return Bool(bool(raw["v"]))
    if kind == "cmp":
        return Compare(
            ComparisonOperator(raw["op"]),
            decode_aexp(raw["l"]),
            decode_aexp(raw["r"]),
        )
    if kind == "not":
        return Not(decode_bexp(raw["e"]))
    if kind == "bop":
        return BinaryBExp(
            BooleanOperator(raw["op"]),
            decode_bexp(raw["l"]),
            decode_bexp(raw["r"]),
        )
    raise ValueError("unknown Boolean-expression kind %r" % kind)


def decode_command(raw: Mapping[str, Any]) -> Command:
    kind = raw["k"]
    if kind == "skip":
        return Skip()
    if kind == "assign":
        return Assign(str(raw["x"]), decode_aexp(raw["e"]))
    if kind == "seq":
        return SequenceCommand(decode_command(raw["l"]), decode_command(raw["r"]))
    if kind == "if":
        return If(
            decode_bexp(raw["b"]),
            decode_command(raw["t"]),
            decode_command(raw["f"]),
        )
    if kind == "while":
        return While(decode_bexp(raw["b"]), decode_command(raw["c"]))
    if kind == "aset":
        return ArrayWrite(
            str(raw["a"]), decode_aexp(raw["i"]), decode_aexp(raw["e"])
        )
    if kind == "choice":
        return Choice(decode_command(raw["l"]), decode_command(raw["r"]))
    raise ValueError("unknown command kind %r" % kind)


def decode_state(raw: Mapping[str, Any]) -> State:
    return State.create(raw.get("vars", {}), raw.get("arrays", {}))


def decode_request(raw: Mapping[str, Any]) -> Request:
    return Request(
        mode=cast(RequestMode, str(raw["mode"])),
        arithmetic=ArithmeticMode(raw.get("arith", "int")),
        program=decode_command(raw["program"]),
        state=decode_state(raw["state"]),
        budget=int(raw.get("budget", 10000)),
    )


def encode_aexp(expression: AExp) -> JsonObject:
    if isinstance(expression, Num):
        return {"k": "num", "n": expression.value}
    if isinstance(expression, Var):
        return {"k": "var", "x": expression.name}
    if isinstance(expression, BinaryAExp):
        return {
            "k": "aop",
            "op": expression.operator.value,
            "l": encode_aexp(expression.left),
            "r": encode_aexp(expression.right),
        }
    if isinstance(expression, ArrayRead):
        return {"k": "aget", "a": expression.array, "i": encode_aexp(expression.index)}
    raise TypeError("cannot encode arithmetic expression %r" % expression)


def encode_bexp(expression: BExp) -> JsonObject:
    if isinstance(expression, Bool):
        return {"k": "bool", "v": expression.value}
    if isinstance(expression, Compare):
        return {
            "k": "cmp",
            "op": expression.operator.value,
            "l": encode_aexp(expression.left),
            "r": encode_aexp(expression.right),
        }
    if isinstance(expression, Not):
        return {"k": "not", "e": encode_bexp(expression.expression)}
    if isinstance(expression, BinaryBExp):
        return {
            "k": "bop",
            "op": expression.operator.value,
            "l": encode_bexp(expression.left),
            "r": encode_bexp(expression.right),
        }
    raise TypeError("cannot encode Boolean expression %r" % expression)


def encode_command(command: Command) -> JsonObject:
    if isinstance(command, Skip):
        return {"k": "skip"}
    if isinstance(command, Assign):
        return {"k": "assign", "x": command.variable, "e": encode_aexp(command.expression)}
    if isinstance(command, SequenceCommand):
        return {"k": "seq", "l": encode_command(command.first), "r": encode_command(command.second)}
    if isinstance(command, If):
        return {
            "k": "if",
            "b": encode_bexp(command.guard),
            "t": encode_command(command.then_branch),
            "f": encode_command(command.else_branch),
        }
    if isinstance(command, While):
        return {"k": "while", "b": encode_bexp(command.guard), "c": encode_command(command.body)}
    if isinstance(command, ArrayWrite):
        return {
            "k": "aset",
            "a": command.array,
            "i": encode_aexp(command.index),
            "e": encode_aexp(command.expression),
        }
    if isinstance(command, Choice):
        return {"k": "choice", "l": encode_command(command.left), "r": encode_command(command.right)}
    raise TypeError("cannot encode command %r" % command)


def encode_state(state: State) -> JsonObject:
    return {
        "vars": dict(state.variables),
        "arrays": {name: list(values) for name, values in state.arrays.items()},
    }


def encode_derivation(node: Derivation) -> JsonObject:
    result: JsonObject = {
        "rule": node.rule,
        "in": encode_state(node.input_state),
        "prem": [encode_derivation(premise) for premise in node.premises],
    }
    if node.value is not None:
        result["val"] = node.value
    if node.output_state is not None:
        result["out"] = encode_state(node.output_state)
    if node.subject is not None:
        result["subj"] = node.subject
    return result


def encode_configuration(configuration: Configuration) -> JsonObject:
    return {"c": encode_command(configuration.command), "s": encode_state(configuration.state)}


def encode_run_result(result: RunResult) -> JsonObject:
    output: JsonObject = {
        "status": result.status,
        "steps": result.steps,
        "configs": [encode_configuration(c) for c in result.configurations],
    }
    if result.final_state is not None:
        output["final"] = encode_state(result.final_state)
    if result.reason is not None:
        output["reason"] = result.reason
    return output


def encode_classify_result(result: ClassifyResult) -> JsonObject:
    output: JsonObject = {"status": result.status, "steps": result.steps}
    if result.final_state is not None:
        output["final"] = encode_state(result.final_state)
    if result.reason is not None:
        output["reason"] = result.reason
    if result.cycle_start is not None:
        output["cycle_start"] = result.cycle_start
    if result.cycle_length is not None:
        output["cycle_length"] = result.cycle_length
    return output


def encode_explore_result(result: ExploreResult) -> JsonObject:
    return {
        "status": "ok",
        "finals_found": [encode_state(state) for state in result.finals_found],
        "stuck_found": result.stuck_found,
        "truncated": result.truncated,
    }
