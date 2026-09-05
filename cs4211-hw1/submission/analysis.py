"""PART C and BONUS: execution classification and nondeterministic search."""

import json
from typing import List

from codec import encode_state
from model import (
    ArithmeticMode,
    ClassifyResult,
    Choice,
    Command,
    Configuration,
    ExploreResult,
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

    current = Configuration(command, state)
    seen = {}
    steps = 0

    while True:
        if isinstance(current.command, Skip):
            return ClassifyResult(
                status="terminated", steps=steps, final_state=current.state
            )

        key = current.key()
        if key in seen:
            return ClassifyResult(
                status="diverges",
                steps=steps,
                cycle_start=seen[key],
                cycle_length=steps - seen[key],
            )

        if steps >= budget:
            return ClassifyResult(status="unknown", steps=steps)

        seen[key] = steps
        try:
            successor = step_c(current.command, current.state, arithmetic)
        except Stuck as error:
            return ClassifyResult(status="stuck", steps=steps, reason=str(error))

        if successor is None:
            return ClassifyResult(status="stuck", steps=steps, reason="no rule applies")

        steps += 1
        current = successor


def step_all(
    command: Command,
    state: State,
    arithmetic: ArithmeticMode,
) -> List[Configuration]:
    """BONUS: return every one-step successor under nondeterministic choice."""

    if isinstance(command, Choice):
        return [
            Configuration(command.left, state),
            Configuration(command.right, state),
        ]

    if isinstance(command, SequenceCommand):
        if isinstance(command.first, Skip):
            return [Configuration(command.second, state)]
        inner_successors = step_all(command.first, state, arithmetic)
        return [
            Configuration(SequenceCommand(inner.command, command.second), inner.state)
            for inner in inner_successors
        ]

    successor = step_c(command, state, arithmetic)
    if successor is None:
        return []
    return [successor]


def explore(
    command: Command,
    state: State,
    arithmetic: ArithmeticMode,
    budget: int,
) -> ExploreResult:
    """BONUS: bounded breadth-first exploration using ``step_all``."""

    initial = Configuration(command, state)
    frontier = [initial]
    visited = {initial.key()}
    final_states = []
    final_keys = set()
    stuck_found = False
    truncated = False
    explored = 0

    while frontier:
        if explored >= budget:
            truncated = True
            break
        current = frontier.pop(0)
        explored += 1

        if isinstance(current.command, Skip):
            key = current.state.key()
            if key not in final_keys:
                final_keys.add(key)
                final_states.append(current.state)
            continue

        try:
            successors = step_all(current.command, current.state, arithmetic)
        except Stuck:
            stuck_found = True
            continue

        if not successors:
            stuck_found = True
            continue

        for successor in successors:
            successor_key = successor.key()
            if successor_key not in visited:
                visited.add(successor_key)
                frontier.append(successor)

    if frontier:
        truncated = True

    final_states.sort(
        key=lambda s: json.dumps(encode_state(s), sort_keys=True, separators=(",", ":"))
    )
    return ExploreResult(tuple(final_states), stuck_found, truncated)
