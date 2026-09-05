"""GIVEN arithmetic helpers shared by the semantic rules."""

from model import ArithmeticMode, ArithmeticOperator, Stuck


def wrap_result(value: int, arithmetic: ArithmeticMode) -> int:
    """Wrap an operation result in int32 mode; numerals themselves are not wrapped."""

    if arithmetic is ArithmeticMode.INT32:
        return ((value + 2 ** 31) % 2 ** 32) - 2 ** 31
    return value


def divide(left: int, right: int, arithmetic: ArithmeticMode) -> int:
    """Divide with truncation toward zero."""

    if right == 0:
        raise Stuck("division by zero")
    quotient = abs(left) // abs(right)
    if (left >= 0) != (right >= 0):
        quotient = -quotient
    return wrap_result(quotient, arithmetic)


def apply_arithmetic_operator(
    operator: ArithmeticOperator,
    left: int,
    right: int,
    arithmetic: ArithmeticMode,
) -> int:
    """Apply one arithmetic operator using the homework's arithmetic mode."""

    if operator is ArithmeticOperator.ADD:
        return wrap_result(left + right, arithmetic)
    if operator is ArithmeticOperator.SUBTRACT:
        return wrap_result(left - right, arithmetic)
    if operator is ArithmeticOperator.MULTIPLY:
        return wrap_result(left * right, arithmetic)
    if operator is ArithmeticOperator.DIVIDE:
        return divide(left, right, arithmetic)
    raise ValueError("unknown arithmetic operator %r" % operator)
