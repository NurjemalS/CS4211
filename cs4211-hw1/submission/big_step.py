"""PART A: big-step semantics.

This is the first file you should edit.  Each function below corresponds to
one big-step judgement in the handout's definitive rules.  The argument and
return types state the semantic
contract explicitly:

* ``big_a`` maps an arithmetic expression and an input state to an integer
  together with a derivation;
* ``big_b`` does the same for a Boolean expression; and
* ``big_c`` maps a command and an input state to a final state together with
  a derivation.

JSON conversion, state canonicalisation, and arithmetic wrapping are supplied
elsewhere.  Do not manipulate JSON dictionaries in this file.
"""

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
    Choice,
    Command,
    Compare,
    Derivation,
    EvalResult,
    If,
    Not,
    Num,
    SequenceCommand,
    Skip,
    State,
    Var,
    While,
)
from arithmetic import apply_arithmetic_operator


def big_a(
    expression: AExp,
    state: State,
    arithmetic: ArithmeticMode,
) -> EvalResult[int]:
    """Evaluate one arithmetic expression using the handout's big-step rules.

    The result contains both the integer value and the derivation tree that
    establishes that value.  Implement the cases by inspecting the concrete
    AST class with ``isinstance``.

    A useful implementation order is:

    1. ``Num``: use ``expression.value`` and make a leaf derivation named
       ``"Num"``.
    2. ``Var``: call ``state.read_variable(expression.name)`` and make a
       ``"Var"`` leaf.  This helper implements the total-state convention.
    3. ``BinaryAExp``: recursively evaluate ``left`` and ``right`` in the
       same input state; apply the operator with
       ``apply_arithmetic_operator``; then make a derivation whose
       two premises are the left and right derivations, in that order.  The
       required rule names are ``Add``, ``Sub``, ``Mul``, and ``Div``.
    4. ``ArrayRead``: recursively evaluate the index, then call
       ``state.read_array``.  Its one premise is the index derivation and its
       rule name is ``Arr-Read``.

    In every case return ``EvalResult(value, derivation)``.  Use
    ``Derivation.expression(...)`` to build an expression node.  Do not
    update ``state``: expressions in IMP have no side effects.

    The handout translates the ``BinaryAExp`` rule into the corresponding
    recursive calls, arithmetic operation, premise order, and result object.
    """

    if isinstance(expression, Num):
        value = expression.value
        derivation = Derivation.expression("Num", state, value)
        return EvalResult(value, derivation)

    if isinstance(expression, Var):
        value = state.read_variable(expression.name)
        derivation = Derivation.expression("Var", state, value)
        return EvalResult(value, derivation)

    if isinstance(expression, BinaryAExp):
        left_result = big_a(expression.left, state, arithmetic)
        right_result = big_a(expression.right, state, arithmetic)
        value = apply_arithmetic_operator(
            expression.operator, left_result.value, right_result.value, arithmetic
        )
        rule = {
            "+": "Add",
            "-": "Sub",
            "*": "Mul",
            "/": "Div",
        }[expression.operator.value]
        derivation = Derivation.expression(
            rule, state, value, [left_result.derivation, right_result.derivation]
        )
        return EvalResult(value, derivation)

    if isinstance(expression, ArrayRead):
        index_result = big_a(expression.index, state, arithmetic)
        value = state.read_array(expression.array, index_result.value)
        derivation = Derivation.expression(
            "Arr-Read", state, value, [index_result.derivation]
        )
        return EvalResult(value, derivation)

    raise TypeError("unknown arithmetic expression %r" % expression)


def big_b(
    expression: BExp,
    state: State,
    arithmetic: ArithmeticMode,
) -> EvalResult[bool]:
    """Evaluate one Boolean expression and return its value and derivation.

    Implement ``Bool``, ``Compare``, ``Not``, and ``BinaryBExp``.  For a
    comparison, call ``big_a`` on its two arithmetic operands.  For ``and``
    and ``or``, evaluate both operands: the homework semantics is strict and
    does not short-circuit.

    Rule names: ``True``, ``False``, ``Eq``, ``Leq``, ``Not``, ``And``,
    and ``Or``.
    """

    if isinstance(expression, Bool):
        derivation = Derivation.expression(
            "True" if expression.value else "False", state, expression.value
        )
        return EvalResult(expression.value, derivation)

    if isinstance(expression, Compare):
        left_result = big_a(expression.left, state, arithmetic)
        right_result = big_a(expression.right, state, arithmetic)
        if expression.operator.value == "=":
            value = left_result.value == right_result.value
            rule = "Eq"
        else:
            value = left_result.value <= right_result.value
            rule = "Leq"
        derivation = Derivation.expression(
            rule, state, value, [left_result.derivation, right_result.derivation]
        )
        return EvalResult(value, derivation)

    if isinstance(expression, Not):
        inner_result = big_b(expression.expression, state, arithmetic)
        value = not inner_result.value
        derivation = Derivation.expression("Not", state, value, [inner_result.derivation])
        return EvalResult(value, derivation)

    if isinstance(expression, BinaryBExp):
        left_result = big_b(expression.left, state, arithmetic)
        right_result = big_b(expression.right, state, arithmetic)
        if expression.operator.value == "and":
            value = left_result.value and right_result.value
            rule = "And"
        else:
            value = left_result.value or right_result.value
            rule = "Or"
        derivation = Derivation.expression(
            rule, state, value, [left_result.derivation, right_result.derivation]
        )
        return EvalResult(value, derivation)

    raise TypeError("unknown Boolean expression %r" % expression)


def big_c(
    command: Command,
    state: State,
    arithmetic: ArithmeticMode,
) -> EvalResult[State]:
    """Execute one command and return its final state and derivation.

    Implement ``Skip``, ``Assign``, ``SequenceCommand``, ``If``, ``While``,
    and ``ArrayWrite``.  ``Choice`` is bonus syntax and has no deterministic
    big-step rule.

    Keep the state flow visible in your code.  For example, a sequence first
    evaluates ``command.first`` in ``state`` and then evaluates
    ``command.second`` in the first result's state.  For an array write,
    evaluate the index, check the bound with ``state.read_array`` (or an
    equivalent check), and only then evaluate the value expression.

    Rule names: ``Skip``, ``Asgn``, ``Seq``, ``If-True``, ``If-False``,
    ``While-True``, ``While-False``, and ``Arr-Write``.  ``While-True`` has
    three premises in this order: guard, body, remaining loop.
    """

    if isinstance(command, Skip):
        derivation = Derivation.command("Skip", state, state)
        return EvalResult(state, derivation)

    if isinstance(command, Assign):
        expression_result = big_a(command.expression, state, arithmetic)
        final_state = state.write_variable(command.variable, expression_result.value)
        derivation = Derivation.command(
            "Asgn", state, final_state, [expression_result.derivation]
        )
        return EvalResult(final_state, derivation)

    if isinstance(command, SequenceCommand):
        first_result = big_c(command.first, state, arithmetic)
        second_result = big_c(command.second, first_result.value, arithmetic)
        derivation = Derivation.command(
            "Seq", state, second_result.value,
            [first_result.derivation, second_result.derivation],
        )
        return EvalResult(second_result.value, derivation)

    if isinstance(command, If):
        guard_result = big_b(command.guard, state, arithmetic)
        if guard_result.value:
            branch_result = big_c(command.then_branch, state, arithmetic)
            rule = "If-True"
        else:
            branch_result = big_c(command.else_branch, state, arithmetic)
            rule = "If-False"
        derivation = Derivation.command(
            rule, state, branch_result.value,
            [guard_result.derivation, branch_result.derivation],
        )
        return EvalResult(branch_result.value, derivation)

    if isinstance(command, While):
        guard_result = big_b(command.guard, state, arithmetic)
        if not guard_result.value:
            derivation = Derivation.command(
                "While-False", state, state, [guard_result.derivation]
            )
            return EvalResult(state, derivation)
        body_result = big_c(command.body, state, arithmetic)
        rest_result = big_c(command, body_result.value, arithmetic)
        derivation = Derivation.command(
            "While-True", state, rest_result.value,
            [guard_result.derivation, body_result.derivation, rest_result.derivation],
        )
        return EvalResult(rest_result.value, derivation)

    if isinstance(command, ArrayWrite):
        index_result = big_a(command.index, state, arithmetic)
        state.read_array(command.array, index_result.value)  # bounds check
        expression_result = big_a(command.expression, state, arithmetic)
        final_state = state.write_array(
            command.array, index_result.value, expression_result.value
        )
        derivation = Derivation.command(
            "Arr-Write", state, final_state,
            [index_result.derivation, expression_result.derivation],
        )
        return EvalResult(final_state, derivation)

    raise TypeError("unknown command %r" % command)
