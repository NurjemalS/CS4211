# CS4211 Homework 1 — Implementing the Semantics of IMP

In this homework you are asked to implement the big-step and small-step
semantics of IMP in Python, Java, or C++. Begin with
[`handout/HW1.pdf`](handout/HW1.pdf). It gives the setup commands, explains
what each supplied file does, takes you through the implementation one part
at a time, and contains every definitive big-step and small-step rule used by
the assignment. You do not need the lecture notes to resolve the semantics.

`SPEC.md` is the exact input/output contract used by the validator and
autograder. The handout settles semantic behavior; the specification settles
precise questions about JSON fields, rule names, and result formats.

## What is in the archive

```text
README.md             this concise setup and submission guide
handout/HW1.pdf       the assignment handout
SPEC.md               exact JSON request and response formats
adapters/python/      typed Python starter code
adapters/java/        typed Java starter code
adapters/cpp/         typed C++ starter code
tests/public/         tests whose requests and expected answers you can inspect
tests/malformed/      ungraded examples rejected before your program runs
validate.py           sends tests to your program and compares its JSON answers
render.py             displays a derivation as a tree or a run as a table
AI-USE.md             disclosure template to submit with your work
```

The language adapters are divided by responsibility. The model files define
classes/structs for the AST, state, derivations, configurations, and results.
The codec files translate between those typed objects and the JSON interface.
You normally edit only the files named for the semantic part:

| Language | Files you normally edit | Given support files |
|---|---|---|
| Python | `big_step.py`, `small_step.py`, `analysis.py` | `model.py`, `codec.py`, `arithmetic.py`, `solution.py` |
| Java | `BigStep.java`, `SmallStep.java`, `Analysis.java` | `Model.java`, `Codec.java`, `Arithmetic.java`, `Json.java`, `Solution.java` |
| C++ | `big_step.cpp`, `small_step.cpp`, `analysis.cpp` | `model.*`, `codec.*`, `arithmetic.hpp`, `semantics.hpp`, `integer.hpp`, `json.hpp`, `solution.cpp` |

## Make your working copy

Choose one language and copy its entire adapter to a directory named
`submission`. Run exactly one of these commands from the top-level
`cs4211-hw1` directory:

```sh
cp -R adapters/python submission
# cp -R adapters/java submission
# cp -R adapters/cpp submission
```

The command copies all the files for the selected language. Do not copy only
the entry-point file: the model, codec, arithmetic, and semantic files work
together. Make all your changes under `submission/` and keep `adapters/`
unchanged as a reference copy. If you use Windows without `cp`, copy the
selected adapter directory in File Explorer and rename the copy `submission`.

The displayed commands use a POSIX shell. On Windows, use WSL or Git Bash, or
translate the copy/build commands and line continuations to PowerShell. The
Python tools `validate.py` and `render.py` are themselves cross-platform.

## First run

After making the copy, run the commands for your language from the top-level
`cs4211-hw1` directory.

### Python

```sh
python3 validate.py \
  --cmd "python3 submission/solution.py" \
  tests/public
```

`validate.py` is the supplied test driver. The text after `--cmd` tells it
how to start your program. `tests/public` tells it where to find the visible
tests and their expected responses.

### Java

```sh
mkdir -p build/java
javac submission/*.java -d build/java
python3 validate.py \
  --cmd "java -cp build/java Solution" \
  tests/public
```

The first command creates a directory for compiled classes. The second
compiles every Java source file in your `submission/` working copy into that
directory. The final command runs the same validator, using the compiled
`Solution` class as the program under test.

### C++

```sh
mkdir -p build
g++ -std=c++17 -O2 submission/*.cpp -o build/solution
python3 validate.py \
  --cmd "./build/solution" \
  tests/public
```

The compiler combines all C++ implementation files and writes the executable
as `build/solution`. The final command asks the validator to run that
executable on the visible tests.

On the untouched starter code, only `b01` should pass. It asks about a command
that is already `skip`, so the given process driver can answer without calling
a `TODO` function. This first pass confirms that your language setup and JSON
driver work.

For Python, you can locate syntax errors before running the validator:

```sh
python3 -m py_compile submission/*.py
```

On a process failure, the validator prints a compact traceback. Add
`--verbose` to show the complete error output.

## Work one part at a time

The command that starts your implementation is:

```text
Python:  python3 submission/solution.py
Java:    java -cp build/java Solution
C++:     ./build/solution
```

For example, a Python student runs all visible Part A tests with:

```sh
python3 validate.py \
  --cmd "python3 submission/solution.py" \
  --part A tests/public
```

The handout gives the complete commands for all three languages and explains
`--part`, `--group`, `--only`, and `--verbose`. Passing every public test is
necessary but not sufficient: marking also uses hidden tests that exercise the
same rules on different programs.

Test IDs are series names, not marking-part names. In particular, the `c`
series belongs to Part B:

| Marking part | Public test IDs |
|---|---|
| A | `a01`–`a15` |
| B | `b01`–`b14`, `c01`–`c07` |
| C | `d01`–`d06` |
| D | `e01`–`e18` |
| bonus | `f01`–`f04` |

Part D assumes that Parts A–C work: it reuses both evaluators, complete runs,
and the classifier.

## Read a result more easily

`render.py` displays derivations as proof trees and executions as tables. To
see the expected response stored in a public test, run:

```sh
python3 render.py --from-test tests/public/a01.json
```

To run your implementation on the same request and render your own response,
add its command:

```sh
python3 render.py --from-test tests/public/a01.json \
  --cmd "python3 submission/solution.py"
```

Replace the command for Java or C++. Add `--latex --standalone` if you want a
complete LaTeX document instead of the text view. `render.py` is only a
display tool; `validate.py` is what compares your result with the expected
one.

## Before submitting

Submit one archive containing:

1. `submission/`, containing the complete working copy of your chosen adapter;
2. a one-line `RUN` file containing the same command you used after `--cmd`;
3. `answers.pdf`, a legible scan of your handwritten Section 5 work unless
   you have an approved accommodation; and
4. the completed `AI-USE.md` template, including the required reflection on
   one accepted and one rejected suggestion (or a statement that none was
   rejected).

For Python, `RUN` contains `python3 submission/solution.py`. Java and C++
submissions also include a `Makefile` whose default target builds the files
needed by their `RUN` command.

The archive should unpack to:

```text
submission/             all files from your chosen adapter
RUN                     the command that starts your program
Makefile                Java and C++ only
answers.pdf             handwritten Section 5 answers, scanned legibly
AI-USE.md
```

Before uploading, unpack your archive into a fresh copy of the released
`cs4211-hw1` directory. Rebuild it and run `validate.py` against
`tests/public` once more. This checks that your archive includes every source
file needed by the command in `RUN`.
