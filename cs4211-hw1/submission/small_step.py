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
from arithmetic import apply_arithmetic_operator


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

    if isinstance(expression, Num):
        return None

    if isinstance(expression, Var):
        return Num(state.read_variable(expression.name))

    if isinstance(expression, BinaryAExp):
        if not isinstance(expression.left, Num):
            left_step = step_a(expression.left, state, arithmetic)
            return BinaryAExp(expression.operator, left_step, expression.right)
        if not isinstance(expression.right, Num):
            right_step = step_a(expression.right, state, arithmetic)
            return BinaryAExp(expression.operator, expression.left, right_step)
        value = apply_arithmetic_operator(
            expression.operator, expression.left.value, expression.right.value, arithmetic
        )
        return Num(value)

    if isinstance(expression, ArrayRead):
        if not isinstance(expression.index, Num):
            index_step = step_a(expression.index, state, arithmetic)
            return ArrayRead(expression.array, index_step)
        value = state.read_array(expression.array, expression.index.value)
        return Num(value)

    raise TypeError("unknown arithmetic expression %r" % expression)


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

    if isinstance(expression, Bool):
        return None

    if isinstance(expression, Compare):
        if not isinstance(expression.left, Num):
            left_step = step_a(expression.left, state, arithmetic)
            return Compare(expression.operator, left_step, expression.right)
        if not isinstance(expression.right, Num):
            right_step = step_a(expression.right, state, arithmetic)
            return Compare(expression.operator, expression.left, right_step)
        if expression.operator is ComparisonOperator.EQUAL:
            value = expression.left.value == expression.right.value
        else:
            value = expression.left.value <= expression.right.value
        return Bool(value)

    if isinstance(expression, Not):
        if not isinstance(expression.expression, Bool):
            inner_step = step_b(expression.expression, state, arithmetic)
            return Not(inner_step)
        return Bool(not expression.expression.value)

    if isinstance(expression, BinaryBExp):
        if not isinstance(expression.left, Bool):
            left_step = step_b(expression.left, state, arithmetic)
            return BinaryBExp(expression.operator, left_step, expression.right)
        if not isinstance(expression.right, Bool):
            right_step = step_b(expression.right, state, arithmetic)
            return BinaryBExp(expression.operator, expression.left, right_step)
        if expression.operator is BooleanOperator.AND:
            value = expression.left.value and expression.right.value
        else:
            value = expression.left.value or expression.right.value
        return Bool(value)

    raise TypeError("unknown Boolean expression %r" % expression)


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

    if isinstance(command, Assign):
        if not isinstance(command.expression, Num):
            expression_step = step_a(command.expression, state, arithmetic)
            return Configuration(Assign(command.variable, expression_step), state)
        next_state = state.write_variable(command.variable, command.expression.value)
        return Configuration(Skip(), next_state)

    if isinstance(command, SequenceCommand):
        if isinstance(command.first, Skip):
            return Configuration(command.second, state)
        inner = step_c(command.first, state, arithmetic)
        if inner is None:
            return None
        return Configuration(
            SequenceCommand(inner.command, command.second), inner.state
        )

    if isinstance(command, If):
        if not isinstance(command.guard, Bool):
            guard_step = step_b(command.guard, state, arithmetic)
            return Configuration(
                If(guard_step, command.then_branch, command.else_branch), state
            )
        if command.guard.value:
            return Configuration(command.then_branch, state)
        return Configuration(command.else_branch, state)

    if isinstance(command, While):
        unfolded = If(
            command.guard,
            SequenceCommand(command.body, command),
            Skip(),
        )
        return Configuration(unfolded, state)

    if isinstance(command, ArrayWrite):
        if not isinstance(command.index, Num):
            index_step = step_a(command.index, state, arithmetic)
            return Configuration(
                ArrayWrite(command.array, index_step, command.expression), state
            )
        state.read_array(command.array, command.index.value)  # bounds check
        if not isinstance(command.expression, Num):
            expression_step = step_a(command.expression, state, arithmetic)
            return Configuration(
                ArrayWrite(command.array, command.index, expression_step), state
            )
        next_state = state.write_array(
            command.array, command.index.value, command.expression.value
        )
        return Configuration(Skip(), next_state)

    return None


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

    configurations = [Configuration(command, state)]
    steps = 0
    current = configurations[0]

    while True:
        if isinstance(current.command, Skip):
            return RunResult(
                status="terminated",
                steps=steps,
                configurations=tuple(configurations),
                final_state=current.state,
            )

        if steps >= budget:
            return RunResult(
                status="budget", steps=steps, configurations=tuple(configurations)
            )

        try:
            successor = step_c(current.command, current.state, arithmetic)
        except Stuck as error:
            return RunResult(
                status="stuck",
                steps=steps,
                configurations=tuple(configurations),
                reason=str(error),
            )

        if successor is None:
            return RunResult(
                status="stuck",
                steps=steps,
                configurations=tuple(configurations),
                reason="no rule applies",
            )

        configurations.append(successor)
        steps += 1
        current = successor
