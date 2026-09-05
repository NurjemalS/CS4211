"""PART C and BONUS: execution classification and nondeterministic search."""

from typing import List

from model import (
    ArithmeticMode,
    ClassifyResult,
    Choice,
    Command,
    Configuration,
    ExploreResult,
    If,
    SequenceCommand,
    Skip,
    State,
    Stuck,
)
from small_step import step_c


def classify(
    command: Command,
    state: State,
    arithmetic: ArithmeticMode,
    budget: int,
) -> ClassifyResult:
    """Run the deterministic semantics and detect repeated configurations.

    Use ``Configuration.key()`` as the dictionary key.  It compares the
    command and the extensional, canonical state by value.  At each iteration
    check, in order: ``Skip``; a repeated configuration; the budget; and then
    call ``step_c``.  Catch ``Stuck`` from arithmetic or array helpers and
    return a ``"stuck"`` result with the current step count.  A ``None``
    successor is likewise stuck.  A failed step attempt does not increment
    the count.
    """

    raise NotImplementedError("TODO Part C: classify")


def step_all(
    command: Command,
    state: State,
    arithmetic: ArithmeticMode,
) -> List[Configuration]:
    """BONUS: return every one-step successor under nondeterministic choice."""

    raise NotImplementedError("TODO bonus: step_all")


def explore(
    command: Command,
    state: State,
    arithmetic: ArithmeticMode,
    budget: int,
) -> ExploreResult:
    """BONUS: bounded breadth-first exploration using ``step_all``."""

    raise NotImplementedError("TODO bonus: explore")
