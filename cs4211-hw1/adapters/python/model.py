"""Typed objects used by the Python semantics implementation.

This file is GIVEN.  It contains the abstract syntax tree (AST), state, and
result classes.  The JSON protocol is decoded into these classes by codec.py,
so the semantic functions never need to inspect keys such as ``"k"`` or
``"e"``.

The classes are intentionally small data containers.  Do not add evaluation
methods to them: the homework asks you to implement the semantic rules in
big_step.py, small_step.py, and analysis.py.
"""

from __future__ import annotations

from dataclasses import dataclass, field
from enum import Enum
from typing import Dict, Generic, Literal, Mapping, Optional, Sequence, Tuple, TypeVar, Union


class Stuck(Exception):
    """No semantic rule applies (division by zero or an invalid array index)."""


class Malformed(Exception):
    """The request is not in the input language.  Malformed inputs are ungraded."""


class ArithmeticMode(Enum):
    INTEGER = "int"
    INT32 = "int32"


class ArithmeticOperator(Enum):
    ADD = "+"
    SUBTRACT = "-"
    MULTIPLY = "*"
    DIVIDE = "/"


class ComparisonOperator(Enum):
    EQUAL = "="
    LESS_OR_EQUAL = "<="


class BooleanOperator(Enum):
    AND = "and"
    OR = "or"


# ---------------------------------------------------------------------------
# Arithmetic expressions
# ---------------------------------------------------------------------------


class AExp:
    """Base class for arithmetic expressions."""


@dataclass(frozen=True)
class Num(AExp):
    """A numeral AST value; construct it as ``Num(7)`` or ``Num(value=7)``."""

    value: int


@dataclass(frozen=True)
class Var(AExp):
    name: str


@dataclass(frozen=True)
class BinaryAExp(AExp):
    operator: ArithmeticOperator
    left: AExp
    right: AExp


@dataclass(frozen=True)
class ArrayRead(AExp):
    array: str
    index: AExp


# ---------------------------------------------------------------------------
# Boolean expressions
# ---------------------------------------------------------------------------


class BExp:
    """Base class for Boolean expressions."""


@dataclass(frozen=True)
class Bool(BExp):
    value: bool


@dataclass(frozen=True)
class Compare(BExp):
    operator: ComparisonOperator
    left: AExp
    right: AExp


@dataclass(frozen=True)
class Not(BExp):
    expression: BExp


@dataclass(frozen=True)
class BinaryBExp(BExp):
    operator: BooleanOperator
    left: BExp
    right: BExp


# ---------------------------------------------------------------------------
# Commands
# ---------------------------------------------------------------------------


class Command:
    """Base class for IMP commands."""


@dataclass(frozen=True)
class Skip(Command):
    pass


@dataclass(frozen=True)
class Assign(Command):
    variable: str
    expression: AExp


@dataclass(frozen=True)
class SequenceCommand(Command):
    first: Command
    second: Command


@dataclass(frozen=True)
class If(Command):
    guard: BExp
    then_branch: Command
    else_branch: Command


@dataclass(frozen=True)
class While(Command):
    guard: BExp
    body: Command


@dataclass(frozen=True)
class ArrayWrite(Command):
    array: str
    index: AExp
    expression: AExp


@dataclass(frozen=True)
class Choice(Command):
    """Bonus syntax: nondeterministic choice between two commands."""

    left: Command
    right: Command


# ---------------------------------------------------------------------------
# States and semantic results
# ---------------------------------------------------------------------------


@dataclass(frozen=True)
class State:
    """An immutable IMP state in canonical form.

    Variables form a total map: ``read_variable("x")`` returns 0 when ``x``
    has no stored binding.  ``write_variable`` therefore removes a binding
    whose new value is 0.  Array names and lengths are fixed by the initial
    state.
    """

    variables: Mapping[str, int] = field(default_factory=dict)
    arrays: Mapping[str, Tuple[int, ...]] = field(default_factory=dict)

    @staticmethod
    def create(
        variables: Optional[Mapping[str, int]] = None,
        arrays: Optional[Mapping[str, Sequence[int]]] = None,
    ) -> State:
        canonical_variables = {
            name: value for name, value in (variables or {}).items() if value != 0
        }
        immutable_arrays = {
            name: tuple(values) for name, values in (arrays or {}).items()
        }
        return State(canonical_variables, immutable_arrays)

    def read_variable(self, name: str) -> int:
        return self.variables.get(name, 0)

    def write_variable(self, name: str, value: int) -> State:
        variables: Dict[str, int] = dict(self.variables)
        if value == 0:
            variables.pop(name, None)
        else:
            variables[name] = value
        return State.create(variables, self.arrays)

    def read_array(self, name: str, index: int) -> int:
        if name not in self.arrays:
            raise Malformed("array %s is not provided by the initial state" % name)
        values = self.arrays[name]
        if not 0 <= index < len(values):
            raise Stuck("index %d out of bounds for %s" % (index, name))
        return values[index]

    def write_array(self, name: str, index: int, value: int) -> State:
        if name not in self.arrays:
            raise Malformed("array %s is not provided by the initial state" % name)
        if not 0 <= index < len(self.arrays[name]):
            raise Stuck("index %d out of bounds for %s" % (index, name))
        arrays: Dict[str, Sequence[int]] = {
            array_name: tuple(values) for array_name, values in self.arrays.items()
        }
        row = list(arrays[name])
        row[index] = value
        arrays[name] = row
        return State.create(self.variables, arrays)

    def key(self) -> "StateKey":
        """A hashable representation for repeated-configuration detection."""

        return tuple(sorted(self.variables.items())), tuple(sorted(self.arrays.items()))


DerivationValue = Union[int, bool]
StateKey = Tuple[Tuple[Tuple[str, int], ...], Tuple[Tuple[str, Tuple[int, ...]], ...]]
RequestMode = Literal["bigstep", "step", "run", "classify", "explore"]
RunStatus = Literal["terminated", "stuck", "budget"]
ClassifyStatus = Literal["terminated", "stuck", "diverges", "unknown"]


@dataclass(frozen=True)
class Derivation:
    """One node of a big-step derivation tree."""

    rule: str
    input_state: State
    premises: Tuple[Derivation, ...] = ()
    value: Optional[DerivationValue] = None
    output_state: Optional[State] = None
    subject: Optional[str] = None

    @staticmethod
    def expression(
        rule: str,
        state: State,
        value: DerivationValue,
        premises: Sequence[Derivation] = (),
        subject: Optional[str] = None,
    ) -> Derivation:
        return Derivation(rule, state, tuple(premises), value=value, subject=subject)

    @staticmethod
    def command(
        rule: str,
        state: State,
        output: State,
        premises: Sequence[Derivation] = (),
        subject: Optional[str] = None,
    ) -> Derivation:
        return Derivation(
            rule, state, tuple(premises), output_state=output, subject=subject
        )


T = TypeVar("T")


@dataclass(frozen=True)
class EvalResult(Generic[T]):
    value: T
    derivation: Derivation


@dataclass(frozen=True)
class Configuration:
    """A residual command paired with its state.

    For example, ``Configuration(Skip(), state)`` represents
    ``<skip, state>``.  The fields are named ``command`` and ``state``.
    """

    command: Command
    state: State

    def key(self) -> Tuple[Command, StateKey]:
        return self.command, self.state.key()


@dataclass(frozen=True)
class RunResult:
    """The outcome and complete recorded prefix of one deterministic run."""

    status: RunStatus
    steps: int
    configurations: Tuple[Configuration, ...]
    final_state: Optional[State] = None
    reason: Optional[str] = None


@dataclass(frozen=True)
class ClassifyResult:
    status: ClassifyStatus
    steps: int
    final_state: Optional[State] = None
    reason: Optional[str] = None
    cycle_start: Optional[int] = None
    cycle_length: Optional[int] = None


@dataclass(frozen=True)
class ExploreResult:
    finals_found: Tuple[State, ...]
    stuck_found: bool
    truncated: bool


@dataclass(frozen=True)
class Request:
    mode: RequestMode
    arithmetic: ArithmeticMode
    program: Command
    state: State
    budget: int = 10000
