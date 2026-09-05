#!/usr/bin/env python3
"""
CS4211 HW1 --- run your implementation against a test directory.

Your program is invoked as a shell command; it reads one JSON request on
stdin and writes one JSON response on stdout.  Nothing about your source is
inspected, so any language works.

    python3 validate.py --cmd "python3 mysolution.py"   tests/public
    python3 validate.py --cmd "java -cp build Solution" tests/public
    python3 validate.py --cmd "./mysolution"            tests/public

Options:
    --cmd CMD       the command that runs your implementation (required)
    --only ID       run one test, or a comma-separated list of ids
    --part P        run one marking part: A, B, C, D or bonus
    --group G       run one operational group (bigstep-expr, step, run, ...)
    --timeout SEC   per-request wall clock limit (default 10)
    --verbose       print full diffs and complete command stderr on failure

`part` is the marking unit; `group` says which mode a test exercises.  The two
are independent: some Part D tests are step-mode or run-mode, so they sit in
the `step` and `run` groups.  Marks are computed per part, and the summary
prints a per-part tally.

Exit status is 0 when every graded test passes.
"""

import argparse, json, os, subprocess, sys, difflib

RESET, RED, GREEN, YELLOW, DIM = "\033[0m", "\033[31m", "\033[32m", "\033[33m", "\033[2m"
if not sys.stdout.isatty():
    RESET = RED = GREEN = YELLOW = DIM = ""


def canon(x):
    return json.dumps(x, sort_keys=True, separators=(",", ":"))


# --- the comparison rule of SPEC.md section 6 --------------------------
# Only the documented fields are compared.  Two consequences:
#   * `subj` --- and any other member you add to a derivation node --- is
#     ignored, so it is genuinely optional;
#   * the wording of a `reason` / `reasons` is never graded, only the status.
DERIV_FIELDS = {"rule", "in", "prem", "val", "out"}


def normalise(x, top=True):
    if isinstance(x, dict):
        if "rule" in x and "prem" in x:            # a derivation node
            return {k: normalise(v, False) for k, v in x.items()
                    if k in DERIV_FIELDS}
        out = {k: normalise(v, False) for k, v in x.items()}
        if top:
            out.pop("reason", None)                # wording is not graded
            out.pop("reasons", None)
        return out
    if isinstance(x, list):
        return [normalise(v, False) for v in x]
    return x


def same(expected, actual):
    return canon(normalise(expected)) == canon(normalise(actual))


def pretty(x):
    return json.dumps(x, sort_keys=True, indent=1)


def load_cases(path):
    cases = []
    if os.path.isfile(path):
        files = [path]
    else:
        files = [os.path.join(path, f) for f in sorted(os.listdir(path))
                 if f.endswith(".json")]
    for f in files:
        with open(f) as fh:
            cases.append(json.load(fh))
    return cases


def run_one(cmd, request, timeout, verbose=False):
    """Return (ok, response_or_None, error_message)."""
    try:
        p = subprocess.run(cmd, shell=True, input=canon(request),
                           capture_output=True, text=True, timeout=timeout)
    except subprocess.TimeoutExpired:
        return False, None, "timed out after %gs" % timeout
    if p.returncode != 0:
        err = (p.stderr or "").strip().splitlines()
        # A single final line such as "SyntaxError: invalid syntax" hides the
        # useful filename, line number, source line, and caret immediately
        # above it.  Keep a compact traceback by default and all of stderr in
        # verbose mode.
        shown = err if verbose else err[-8:]
        detail = "\n".join(shown) if shown else "(no stderr)"
        return False, None, "exited with status %d:\n%s" % (p.returncode, detail)
    out = p.stdout.strip()
    if not out:
        return False, None, "wrote nothing to stdout"
    try:
        return True, json.loads(out), None
    except json.JSONDecodeError as e:
        return False, None, "stdout is not valid JSON (%s): %.120r" % (e.msg, out)


def first_derivation_difference(expected, actual, path="root"):
    """Describe the first unequal derivation node, if both sides have one."""
    if not (isinstance(expected, dict) and isinstance(actual, dict)
            and "derivation" in expected and "derivation" in actual):
        return None

    def visit(want, got, here):
        if not isinstance(want, dict) or not isinstance(got, dict):
            return "%s: expected a derivation node, got %r" % (here, got)
        for field in ("rule", "in", "val", "out"):
            if normalise(want.get(field), False) != normalise(got.get(field), False):
                return "%s -> %s: expected %r, got %r" % (
                    here, field, want.get(field), got.get(field))
        want_prem = want.get("prem", [])
        got_prem = got.get("prem", [])
        if len(want_prem) != len(got_prem):
            return "%s -> prem: expected %d premise(s), got %d" % (
                here, len(want_prem), len(got_prem))
        for index, (want_child, got_child) in enumerate(zip(want_prem, got_prem)):
            difference = visit(want_child, got_child,
                               "%s -> prem[%d]" % (here, index))
            if difference:
                return difference
        return None

    return visit(expected["derivation"], actual["derivation"], path)


def diagnose(expected, actual):
    """Turn a mismatch into a sentence, where a common cause is recognisable."""
    hints = []
    if isinstance(actual, dict) and isinstance(expected, dict):
        if actual.get("status") != expected.get("status"):
            hints.append("status is %r but should be %r"
                         % (actual.get("status"), expected.get("status")))
        if "steps" in expected and expected.get("steps") != actual.get("steps"):
            hints.append("step count is %r but should be %r; increment it only "
                         "after a successful command transition"
                         % (actual.get("steps"), expected.get("steps")))

        def noncanon(st):
            return (isinstance(st, dict) and isinstance(st.get("vars"), dict)
                    and any(v == 0 for v in st["vars"].values()))
        for key in ("final",):
            if key in expected and noncanon(actual.get(key)):
                hints.append("the %s state keeps a zero-valued binding; states "
                             "are total, so drop bindings whose value is 0" % key)
        if expected.get("status") == "stuck" and actual.get("status") == "malformed":
            hints.append("this input is well formed --- it is a genuine stuck "
                         "configuration, not malformed input")
        if (expected.get("status") == actual.get("status")
                and expected.get("status") in ("stuck", "malformed")):
            hints.append("the status is right, so the difference is elsewhere "
                         "(the wording of `reason` is never graded)")
        derivation_difference = first_derivation_difference(expected, actual)
        if derivation_difference:
            hints.append("first derivation difference: " + derivation_difference)
    return hints


def main():
    ap = argparse.ArgumentParser(
        description="Run an IMP implementation against a directory of JSON tests.")
    ap.add_argument("--cmd", required=True,
                    help="shell command that starts your implementation")
    ap.add_argument("--only", default=None,
                    help="one test id, or comma-separated ids")
    ap.add_argument("--part", default=None,
                    help="marking part: A, B, C, D, or bonus (case-insensitive)")
    ap.add_argument("--group", default=None,
                    help="request group such as step, run, or classify")
    ap.add_argument("--timeout", type=float, default=10.0,
                    help="seconds allowed for each request (default: 10)")
    ap.add_argument("--verbose", action="store_true",
                    help="show complete diffs and command error output")
    ap.add_argument("path", nargs="?", default="tests/public",
                    help="test JSON file or directory (default: tests/public)")
    args = ap.parse_args()

    if not os.path.exists(args.path):
        print("no such test path: %s" % args.path, file=sys.stderr)
        return 2

    cases = load_cases(args.path)
    available_ids = sorted(c["id"] for c in cases)
    available_parts = sorted({c.get("part") for c in cases if c.get("part")},
                             key=lambda part: (part == "bonus", part))
    available_groups = sorted({c.get("group") for c in cases if c.get("group")})
    if args.only:
        wanted = set(args.only.split(","))
        unknown = sorted(wanted - set(available_ids))
        if unknown:
            print("unknown test id(s): %s" % ", ".join(unknown), file=sys.stderr)
            print("available ids: %s" % ", ".join(available_ids), file=sys.stderr)
            return 2
        cases = [c for c in cases if c["id"] in wanted]
    if args.part:
        wanted = {("bonus" if p.strip().lower() == "bonus" else p.strip().upper())
                  for p in args.part.split(",")}
        unknown = sorted(wanted - set(available_parts))
        if unknown:
            print("unknown part(s): %s" % ", ".join(unknown), file=sys.stderr)
            print("available parts: %s" % ", ".join(available_parts), file=sys.stderr)
            return 2
        cases = [c for c in cases if c.get("part") in wanted]
    if args.group:
        wanted_group = args.group.lower()
        if wanted_group not in available_groups:
            print("unknown group: %s" % args.group, file=sys.stderr)
            print("available groups: %s" % ", ".join(available_groups), file=sys.stderr)
            return 2
        cases = [c for c in cases if c.get("group") == wanted_group]
    if not cases:
        print("no tests selected", file=sys.stderr)
        return 2

    graded = [c for c in cases if c.get("graded", True)]
    ungraded = [c for c in cases if not c.get("graded", True)]

    passed, failed = 0, []
    for c in graded:
        ok, got, err = run_one(args.cmd, c["request"], args.timeout, args.verbose)
        if ok and same(c["expected"], got):
            passed += 1
            print("%s  pass %s%s  %s" % (GREEN, c["id"], RESET, c["description"]))
            continue
        failed.append(c["id"])
        print("%s  FAIL %s%s  %s" % (RED, c["id"], RESET, c["description"]))
        if err:
            for line in err.splitlines():
                print("       %s%s%s" % (DIM, line, RESET))
        else:
            for h in diagnose(c["expected"], got):
                print("       %shint: %s%s" % (YELLOW, h, RESET))
            if args.verbose:
                # Diff the NORMALISED objects, so the diff shows only what is
                # actually graded.
                d = difflib.unified_diff(pretty(normalise(c["expected"])).splitlines(),
                                         pretty(normalise(got)).splitlines(),
                                         "expected", "yours", lineterm="", n=1)
                for line in d:
                    print("       %s%s%s" % (DIM, line, RESET))
            else:
                print("       %sexpected %.100s%s" % (DIM, canon(normalise(c["expected"])), RESET))
                print("       %sgot      %.100s%s" % (DIM, canon(normalise(got)), RESET))
                print("       %s(re-run with --verbose for a full diff)%s" % (DIM, RESET))

    print()
    print("graded: %d/%d passed" % (passed, len(graded)))
    if failed:
        print("failed: %s" % ", ".join(failed))

    # Per-part tally, because marks are assigned by part rather than by group.
    parts = {}
    for c in graded:
        p = c.get("part", "?")
        tot, ok = parts.get(p, (0, 0))
        parts[p] = (tot + 1, ok + (0 if c["id"] in failed else 1))
    if len(parts) > 1:
        print()
        print("by part:")
        for p in sorted(parts, key=lambda k: (k == "bonus", k)):
            tot, ok = parts[p]
            print("  %-6s %2d/%2d" % (p, ok, tot))

    # Malformed cases are NOT graded.  They are shown separately so you can see
    # what the harness rejects before your program ever runs.  Implementing the
    # check earns no marks, and skipping it costs none.
    if ungraded:
        print()
        print("%sungraded (malformed input --- informational only):%s" % (DIM, RESET))
        for c in ungraded:
            ok, got, err = run_one(args.cmd, c["request"], args.timeout, args.verbose)
            agrees = ok and same(c["expected"], got)
            mark = "matches" if agrees else "differs (fine either way)"
            print("  %s%-5s %-9s %s%s" % (DIM, c["id"], mark, c["description"], RESET))

    return 1 if failed else 0


if __name__ == "__main__":
    sys.exit(main())
