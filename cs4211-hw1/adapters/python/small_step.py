"""PART B: small-step semantics and complete executions."""

from typing import Optional

from model import (
    AExp,
    ArithmeticMode,
    ArrayRead,
    ArrayWrite,
    Assign,
    BExp,
    BinaryAExp,
    BinaryBExp,
    Bool,
    BooleanOperator,
    Command,
    Compare,
    ComparisonOperator,
    Configuration,
    If,
    Not,
    Num,
    RunResult,
    SequenceCommand,
    Skip,
    State,
    Stuck,
    Var,
    While,
)


def step_a(
    expression: AExp,
    state: State,
    arithmetic: ArithmeticMode,
) -> Optional[AExp]:
    """Take one arithmetic-expression step.

    The result is another AST object, not a Python integer.  For example,
    stepping ``Var("x")`` produces ``Num(state.read_variable("x"))``.
    Constructing ``Num(value)`` and ``Num(value=value)`` are equivalent.

    Return ``None`` when ``expression`` is already ``Num`` because a numeral
    is an arithmetic value.  Otherwise perform exactly one arithmetic step
    from the handout's definitive rules.
    Follow the left-to-right congruence rules and rebuild the surrounding AST;
    do not evaluate the whole expression recursively.  Recursive arithmetic
    premises call ``step_a`` again, with all three arguments.
    """

    raise NotImplementedError("TODO Part B: step_a")


def step_b(
    expression: BExp,
    state: State,
    arithmetic: ArithmeticMode,
) -> Optional[BExp]:
    """Take exactly one Boolean-expression step.

    Return a residual ``BExp`` AST object, or ``None`` when ``expression`` is
    already ``Bool``.  Comparisons step their arithmetic operands with
    ``step_a``; Boolean connectives and ``Not`` step Boolean operands with
    ``step_b``.  A completed comparison therefore constructs ``Bool(value)``,
    not ``Num(value)``.
    """

    raise NotImplementedError("TODO Part B: step_b")


def step_c(
    command: Command,
    state: State,
    arithmetic: ArithmeticMode,
) -> Optional[Configuration]:
    """Take one step from a non-final command configuration.

    The top-level ``step`` driver checks for an outermost ``Skip`` before it
    calls this function.  Thus, an outermost ``Skip`` is final and never
    arrives here.  A command such as ``SequenceCommand(Skip(), second)`` is
    not itself ``Skip`` and must still take the ``S-Seq-Done`` step.

    Return the successor as ``Configuration(command=..., state=...)``.
    The positional form ``Configuration(command, state)`` is equivalent.
    When an outer rule takes a premise step, call the matching helper with
    every argument and rebuild the outer command from the returned fields;
    for example, a recursive ``step_c`` result has ``.command`` and ``.state``.

    Return ``None`` only when the input command is not final but no rule
    applies.  This means stuck, not final.  Division by zero and out-of-bounds
    array access instead raise ``Stuck`` from the supplied helpers.
    """

    raise NotImplementedError("TODO Part B: step_c")


def run(
    command: Command,
    state: State,
    arithmetic: ArithmeticMode,
    budget: int,
) -> RunResult:
    """Repeatedly call ``step_c`` and record every configuration.

    Start with ``Configuration(command, state)``.  At each iteration:

    1. If the current command is ``Skip``, return ``"terminated"``.
    2. If ``steps >= budget``, return ``"budget"``.
    3. Call ``step_c``.  Catch ``Stuck`` and return status ``"stuck"``;
       likewise, a ``None`` successor means ``"stuck"``.
    4. Append a real successor and increment ``steps``.

    Finality precedes the budget test, so a program that takes exactly
    ``budget`` steps terminates.  The configuration sequence includes the
    input configuration and therefore always has length ``steps + 1``.
    Store it as ``tuple(configurations)`` in ``RunResult``.
    """

    raise NotImplementedError("TODO Part B: run")
