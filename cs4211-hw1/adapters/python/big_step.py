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

    raise NotImplementedError("TODO Part A: big_a")


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

    raise NotImplementedError("TODO Part A: big_b")


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

    raise NotImplementedError("TODO Part A: big_c")
