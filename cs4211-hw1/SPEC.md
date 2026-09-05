# CS4211 HW1 — Exact Interface and Data Formats

You are being asked to implement the big-step and small-step semantics of IMP.
The supplied adapter handles the surrounding machinery: it reads a JSON
request, converts the program into typed abstract syntax tree (AST) objects,
calls your semantic functions, and converts your result back to JSON.

The handout explains how to work through the homework and contains the
definitive big-step and small-step rules. Use this file when you need the
exact shape of an AST node, request, or response. The validator and
autograder use the formats described here, so details such as step counts,
premise order, and state representation matter.

Your program must read one JSON object from standard input and write one JSON
object to standard output. Write nothing else to standard output. If you want
to print debugging information, write it to standard error.

## 1. How JSON becomes the typed AST

The tests send programs as JSON because the same tests must work with Python,
Java, and C++. You do not need to write a lexer, parser, or JSON converter.
The program has already been parsed into an AST before your semantic functions
receive it.

For example, the JSON object

```json
{"k":"assign", "x":"r", "e":{"k":"num", "n":7}}
```

represents the command `r := 7`. The field `k` is short for *kind*. The outer
node has kind `assign`; its `x` field names the variable, and its `e` field
contains the expression being assigned. The nested node has kind `num`, and
its `n` field contains the numeral 7.

The supplied codec converts this JSON tree into the typed objects you use in
your implementation:

| Language | Typed object |
|---|---|
| Python | `Assign("r", Num(7))` |
| Java | `new Model.Assign("r", new Model.Num(7))` |
| C++ | an `imp::Assign` containing an `imp::Num` |

In Python, `codec.py` performs this conversion. In Java, it is `Codec.java`;
in C++, it is `codec.cpp`. You should normally leave the codec unchanged.
Your semantic functions inspect typed classes or variants such as `Assign`,
`Num`, `BinaryAExp`, and `SequenceCommand`; they do not inspect the short JSON
keys directly.

The following lists give the JSON form of every AST node. Text in angle
brackets, such as `<AExp>`, is a placeholder for another JSON value; do not
include the angle brackets in an actual request.

### Arithmetic expressions (`AExp`)

```text
{"k":"num",  "n": <integer>}
{"k":"var",  "x": <name>}
{"k":"aop",  "op": "+" | "-" | "*" | "/", "l": <AExp>, "r": <AExp>}
{"k":"aget", "a": <name>, "i": <AExp>}
```

These become the typed constructors `Num`, `Var`, `BinaryAExp`, and
`ArrayRead`, respectively. In a binary expression, `l` and `r` mean the left
and right operands. In an array read, `a` is the array name and `i` is the
index expression.

### Boolean expressions (`BExp`)

```text
{"k":"bool", "v": true | false}
{"k":"cmp",  "op": "=" | "<=", "l": <AExp>, "r": <AExp>}
{"k":"not",  "e": <BExp>}
{"k":"bop",  "op": "and" | "or", "l": <BExp>, "r": <BExp>}
```

These become `Bool`, `Compare`, `Not`, and `BinaryBExp`. The field `v` holds a
Boolean value, while `e` holds the expression under `not`.

### Commands (`Command`)

```text
{"k":"skip"}
{"k":"assign", "x": <name>, "e": <AExp>}
{"k":"seq",    "l": <Command>, "r": <Command>}
{"k":"if",     "b": <BExp>, "t": <Command>, "f": <Command>}
{"k":"while",  "b": <BExp>, "c": <Command>}
{"k":"aset",   "a": <name>, "i": <AExp>, "e": <AExp>}
{"k":"choice", "l": <Command>, "r": <Command>}  // bonus only
```

These become `Skip`, `Assign`, `SequenceCommand`, `If`, `While`,
`ArrayWrite`, and `Choice`. For an `if`, `b` is the guard, `t` is the then
branch, and `f` is the else branch. For a `while`, `c` is the loop body. The
`choice` form is used only for the bonus.

A name must match `[A-Za-z_][A-Za-z0-9_]*`.

## 2. States

A state has one map for scalar variables and one map for arrays:

```text
{"vars": {<name>: <integer>, ...}, "arrays": {<name>: [<integer>, ...], ...}}
```

The variable map represents the total map σ : Var → ℤ. If `vars` does not
contain a name, that variable has value 0. Reading an undeclared variable is
therefore never stuck.

Because the map is total, `{}` and `{"x":0}` represent the same variable
state. You must emit states in *canonical form*: omit every variable binding
whose value is 0. Use the supplied state read and write helpers; they already
apply this convention. The validator compares canonical states, so retaining
an `x:0` binding counts as a mismatch.

Arrays work differently. The `arrays` map is not total. The initial state
fixes every available array name, length, and value. Arrays never resize. A
program that names an array absent from the initial state is malformed input,
as explained in Section 7. An array that exists but is accessed outside its
bounds produces a stuck configuration.

## 3. Requests and arithmetic modes

Every input to your program has this form:

```json
{
  "mode":    "bigstep" | "step" | "run" | "classify" | "explore",
  "arith":   "int" | "int32",
  "program": <Command>,
  "state":   <State>,
  "budget":  <non-negative integer>
}
```

The `program` and `state` fields give the initial configuration. The `mode`
field says which semantic operation to perform. The five modes are explained
in Section 5, in the same order in which you implement them.

The `budget` field is present for `run`, `classify`, and `explore`, and absent
for `bigstep` and `step`. A budget may be 0; the public corpus includes this
case.

The `arith` field chooses how arithmetic operations behave:

- `"int"` means the mathematical integers ℤ. There is no fixed-width
  overflow. Python uses its arbitrary-precision `int`, Java uses
  `BigInteger`, and C++ uses the supplied arbitrary-precision `BigInteger`
  class in `adapters/cpp/integer.hpp`.
- `"int32"` means signed 32-bit arithmetic. After each `+`, `-`, `*`, or `/`
  operation, wrap the result into [−2³¹, 2³¹−1]. A numeral denotes itself; do
  not wrap it when you read the AST. An out-of-range numeral or initial state
  value is malformed input.

Use the arithmetic helper supplied with your adapter in both the big-step and
small-step implementations. In particular, division truncates toward zero:
`7/2 = 3` and `-7/2 = -3`. Division by zero is stuck.

The IMP operators `and` and `or` are strict. First evaluate the left operand,
next evaluate the right operand, and only then apply the connective. Do not
short-circuit the right operand.

## 4. Stuck configurations and array-write order

A configuration is stuck when its command is not final and no semantic rule
applies. There are exactly two ways for a well-formed program in this homework
to become stuck:

1. it tries to divide by zero; or
2. it reads or writes an array outside its bounds, where a valid index `z`
   must satisfy `0 ≤ z < |σ(a)|`.

Remember that reading an unmentioned scalar variable gives 0 and is not
stuck.

For an array write `a[i] := e`, the order is important. First evaluate the
index `i`. Next check whether the resulting index is in bounds. Only then
evaluate the value expression `e`. Thus, if `a` has length 3, the command
`a[5] := 1/0` is stuck because index 5 is out of bounds; the division is
never evaluated. Use this order in both big-step and small-step semantics.

## 5. Responses for each mode

The adapter turns the typed results returned by your functions into the JSON
responses below.

### 5.1 `bigstep`: execute and return a derivation

For `bigstep`, evaluate `⟨program, state⟩ ⇓ σ′`. Return both the final state
and the derivation that establishes it:

```json
{"status":"ok", "final": <State>, "derivation": <DerivationNode>}
{"status":"stuck", "reason": <string>}
```

A `bigstep` request may legitimately answer `stuck`. This happens if
evaluation reaches division by zero or an out-of-bounds array access; there
is then no derivation and no final state. The graded corpus does not send a
nonterminating program in `bigstep` mode, so your recursive evaluator will
not be asked to return from such a call.

A derivation is a tree. Each JSON node represents one application of a rule:

```text
{"rule": <RuleName>, "in": <State>, "prem": [<DerivationNode>, ...],
 "val": <integer or boolean>}       // an expression judgement

{"rule": <RuleName>, "in": <State>, "prem": [<DerivationNode>, ...],
 "out": <State>}                    // a command judgement
```

Put premises in the same order as they appear in the inference rule. In
particular, `While-True` has three premises: first the guard, next the body,
and finally the remaining loop.

Use these fixed, case-sensitive names in big-step derivations:

| Judgement | Rule names |
|---|---|
| `AExp` | `Num`, `Var`, `Add`, `Sub`, `Mul`, `Div`, `Arr-Read` |
| `BExp` | `True`, `False`, `Eq`, `Leq`, `Not`, `And`, `Or` |
| `Command` | `Skip`, `Asgn`, `Seq`, `If-True`, `If-False`, `While-True`, `While-False`, `Arr-Write` |

The supplied `Derivation` type also has an optional subject string. If you set
it, the codec writes it as `subj`, and `render.py` uses it to label the proof
tree. You may omit it because it is not compared by the validator.

### 5.2 `step`: take one command step

For `step`, apply the command small-step relation once:

```json
{"status":"ok",    "next": {"c": <Command>, "s": <State>}}
{"status":"final"}
{"status":"stuck", "reason": <string>}
```

Here `c` is the residual command and `s` is its state. Return `final` only
when the input command is `skip`. Return `stuck` when the command is not
`skip` and has no successor.

The supplied entry point performs this distinction before calling the
command-step helper. Thus, the helper's precondition is that its outer command
is not `Skip`; under that precondition, a missing successor means stuck. This
does not remove `[S-Seq-Done]`: `SequenceCommand(Skip(), second)` is a sequence,
not an outermost `Skip`, and it steps to `second` in the same state.

The residual command is compared as an AST, not as printed IMP text.
Arithmetic numerals and Boolean literals are values, so `Num` and `Bool`
nodes do not take expression steps.

In Python, the residual returned by `step_a` is an `AExp` object. For example,
construct a numeral residual as `Num(value)`, not as the bare integer `value`.
The successor returned by `step_c` is a `Configuration` object; both
`Configuration(command, state)` and
`Configuration(command=command, state=state)` are valid constructor calls.
If a recursive command step returns `inner`, rebuild an outer sequence from
`inner.command` and carry `inner.state`. Call the helper matching the premise
category: `step_a` for an arithmetic premise, `step_b` for a Boolean premise,
and `step_c` for a command premise.

The small-step helpers and `render.py` use the following rule names. The
validator does not compare these names because a `step` response contains
only the successor configuration, but the names are useful when you trace a
rule application:

```text
A-Var, A-Op, A-Op-L, A-Op-R, A-Arr-Idx, A-Arr,
B-Cmp, B-Cmp-L, B-Cmp-R, B-Not-T, B-Not-F, B-Not-Step,
B-Con, B-Con-L, B-Con-R,
S-Asgn, S-Asgn-Step, S-Seq, S-Seq-Done,
S-If-Step, S-If-True, S-If-False, S-While,
S-Arr-Idx, S-Arr-Step, S-Arr,
S-Choice-L, S-Choice-R
```

The last two names are for the bonus.

### 5.3 `run`: record one deterministic execution

For `run`, begin with the initial configuration and repeatedly call the
command-step function, taking at most `budget` steps:

```json
{"status":"terminated", "steps": <n>, "final": <State>, "configs": [<Config>, ...]}
{"status":"stuck",      "steps": <n>, "configs": [<Config>, ...], "reason": <string>}
{"status":"budget",     "steps": <n>, "configs": [<Config>, ...]}
```

A configuration has the form `{"c": <Command>, "s": <State>}`. Store the
initial configuration at `configs[0]`, followed by every successor. It follows
that `len(configs) == steps + 1` for every response.

At each iteration, first test whether the current command is `skip`. If it is,
return `terminated`, even when you have just taken the last permitted step.
Next test whether the budget has been exhausted. Only if another step is
permitted should you try to take it; if no rule applies, return `stuck`.

There are two implementation paths to a `stuck` run result. A non-final
command-step helper can return no successor, meaning simply that no rule
applies. Alternatively, a supplied arithmetic or state helper raises `Stuck`
when it detects division by zero or an out-of-bounds array access. Catch that
exception inside the execution loop so the returned result still records the
initial configuration and every successful successor before the failing
attempt. A failing attempt does not increment the step count.

This ordering means that `x := 1` with budget 1 terminates in one step. A
`budget` response means only that execution continued for the permitted
number of steps. It does not prove divergence.

### 5.4 `classify`: detect repeated configurations

For `classify`, follow the same deterministic execution as `run`, but do not
return the list of configurations. Instead, remember when each configuration
was first seen:

```json
{"status":"terminated", "steps": <n>, "final": <State>}
{"status":"stuck",      "steps": <n>, "reason": <string>}
{"status":"diverges",   "steps": <n>, "cycle_start": <i>, "cycle_length": <l>}
{"status":"unknown",    "steps": <n>}
```

At each iteration, first check whether the command is final. Next check
whether the current configuration has appeared before. Then check the budget.
If none of those conditions applies, record the configuration and try to take
one step. Return `stuck` if no rule applies, and also catch the supplied
`Stuck` exception raised by division by zero or an out-of-bounds array access.
A failed step attempt does not increment the step count.

Compare configurations by value, including the canonical form of the state,
not by object identity. When the configuration at step `n` equals the one
first seen at step `cycle_start`, return `diverges` with
`cycle_length = n - cycle_start`.

The required step relation is deterministic: every non-final, non-stuck
configuration has one successor. Once a configuration repeats, the same
sequence must repeat forever, so `diverges` is justified. By contrast,
`unknown` says only that the budget ended before termination, stuckness, or a
repeat was found. Check for a repeat before checking the budget so that a
cycle found on the last permitted step is still reported.

### 5.5 `explore`: bounded bonus search

The bonus adds `choice`, so a configuration can have more than one successor.
For `explore`, perform the bounded breadth-first search described in the
handout and return:

```json
{"status":"ok",
 "finals_found": [<State>, ...],
 "stuck_found":  true | false,
 "truncated":    true | false}
```

Return final states in canonical form, remove duplicates, and sort them by
the compact JSON serialization of each state with object keys sorted.
`stuck_found` says whether the search encountered a non-final configuration
with no successor. `truncated` is true when the search reaches its budget of
explored configurations.

A loop-free program can still be truncated when its budget is too small. For
example, `x := 1 [] x := 2` can do so. Every shipped bonus test is loop-free
and has a large enough budget for `truncated` to be false.

Do not try to compute all reachable final states for arbitrary programs with
both loops and choice. This mode is deliberately a bounded search.

## 6. How responses are compared

The validator parses your output as JSON before comparing it with the expected
response. JSON key order, whitespace, and indentation do not matter.

Two comparison rules let you choose explanatory text without losing marks:

1. In a derivation node, the validator compares only `rule`, `in`, `prem`,
   `val`, and `out`. Other members are ignored in both your response and the
   expected response. In particular, `subj` is optional.
2. For a `stuck` response, the text in `reason` is ignored. For a `malformed`
   response, the text entries in `reasons` are ignored. You may write these
   explanations in your own words; an empty string or list is acceptable.

Everything else is compared exactly. This includes every state, residual AST,
step count, status, and the shape and premise order of every derivation.
`validate.py` uses these same comparison rules locally.

## 7. Malformed input

Malformed input is rejected separately from semantic stuckness:

```json
{"status":"malformed", "reasons": [<string>, ...]}
```

An input is malformed when:

- it names an array that the initial state does not provide;
- under `"int32"`, it contains a numeral outside [−2³¹, 2³¹−1];
- under `"int32"`, its initial state contains a variable or array value
  outside that range; or
- it uses a command form not listed in Section 1.

You are not graded on malformed inputs. The files under `tests/malformed/`
show examples that the test system rejects before your implementation runs.
`validate.py` reports them in a separate ungraded section. You may implement
the check, but it earns no marks, and ignoring these cases costs no marks.

## 8. Running the validator

First copy one complete language adapter to `submission/`, as described in
the handout and README. Run the following commands from the top-level
`cs4211-hw1` directory.

For Python, no compilation is needed:

```sh
python3 validate.py --cmd "python3 submission/solution.py" tests/public
```

For Java, first compile every Java file in your working copy, then run the
compiled `Solution` class:

```sh
mkdir -p build/java
javac submission/*.java -d build/java
python3 validate.py --cmd "java -cp build/java Solution" tests/public
```

For C++, first compile every implementation file into `build/solution`, then
run that executable:

```sh
mkdir -p build
g++ -std=c++17 -O2 submission/*.cpp -o build/solution
python3 validate.py --cmd "./build/solution" tests/public
```

In each validator command, the quoted value after `--cmd` tells
`validate.py` how to start your program. The final argument,
`tests/public`, tells it to read the visible test requests and expected
responses from that directory. For each selected test, the validator starts
your command, sends the test's `request` object to standard input, reads your
JSON response from standard output, and compares it with `expected`.

On an untouched adapter, you should see only `b01` pass. That test asks about
`skip`, which the supplied entry point can answer without calling a function
marked `TODO`. Once you begin implementing a part, use an option such as
`--part A` or `--only a01` to select the relevant tests. Add `--verbose` to
see a complete mismatch or the complete error output from a failed process.

For Python, this command checks every submission file for syntax errors and
reports the precise filename and line number without running a semantic test:

```sh
python3 -m py_compile submission/*.py
```

Your command must exit with status 0 after writing its response. A non-zero
exit, crash, invalid JSON response, or extra text on standard output fails the
test. Each request has a wall-clock limit of 10 seconds.

## 9. Worked `run` example

This request asks for the complete small-step execution of `x := y + 2`,
starting from a state in which `y` is 5, with a budget of 50 steps:

```json
{"mode":"run","arith":"int","budget":50,
 "program":{"k":"assign","x":"x",
            "e":{"k":"aop","op":"+","l":{"k":"var","x":"y"},
                 "r":{"k":"num","n":2}}},
 "state":{"vars":{"y":5},"arrays":{}}}
```

The execution takes three steps, using `[A-Var]`, `[A-Op]`, and `[S-Asgn]`.
The response is:

```json
{"status":"terminated","steps":3,
 "final":{"vars":{"x":7,"y":5},"arrays":{}},
 "configs":[
  {"c":{"k":"assign","x":"x","e":{"k":"aop","op":"+","l":{"k":"var","x":"y"},"r":{"k":"num","n":2}}},
   "s":{"vars":{"y":5},"arrays":{}}},
  {"c":{"k":"assign","x":"x","e":{"k":"aop","op":"+","l":{"k":"num","n":5},"r":{"k":"num","n":2}}},
   "s":{"vars":{"y":5},"arrays":{}}},
  {"c":{"k":"assign","x":"x","e":{"k":"num","n":7}},
   "s":{"vars":{"y":5},"arrays":{}}},
  {"c":{"k":"skip"},
   "s":{"vars":{"x":7,"y":5},"arrays":{}}}]}
```

Notice that the state does not change while the expression is being reduced.
Only `[S-Asgn]` updates the variable map.
