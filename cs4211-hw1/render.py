#!/usr/bin/env python3
"""
CS4211 HW1 --- turn your output into something you can read.

A derivation becomes a LaTeX proof tree (the shape you drew by hand in the
handout), or an indented text tree.  An execution becomes a numbered table of
configurations.

    python3 render.py --from-test tests/public/a11.json           # expected output
    python3 render.py --from-test tests/public/a11.json \
      --cmd "python3 submission/solution.py"                       # your output
    python3 render.py --from-test tests/public/c04.json --latex > run.tex

Options:
    --from-test FILE   render the *expected* output stored in a test file
    --latex            emit LaTeX instead of text
    --max-depth N      collapse derivation subtrees below depth N (default: all)

The LaTeX output needs only amsmath, or use --standalone for a complete
compilable document.
"""

import argparse, json, subprocess, sys

# ---------------------------------------------------------------- pretty-print
PREC = {"or": 1, "and": 2, "not": 3, "cmp": 4, "+": 5, "-": 5, "*": 6, "/": 6}


def a_str(a, tex=False):
    k = a["k"]
    if k == "num":
        return str(a["n"])
    if k == "var":
        return mono(a["x"], tex)
    if k == "aget":
        return "%s[%s]" % (mono(a["a"], tex), a_str(a["i"], tex))
    if k == "aop":
        l, r = a_str(a["l"], tex), a_str(a["r"], tex)
        if a["l"]["k"] == "aop" and PREC[a["l"]["op"]] < PREC[a["op"]]:
            l = "(%s)" % l
        if a["r"]["k"] == "aop" and PREC[a["r"]["op"]] <= PREC[a["op"]]:
            r = "(%s)" % r
        return "%s %s %s" % (l, a["op"], r)
    raise ValueError(a)


def b_str(b, tex=False):
    k = b["k"]
    if k == "bool":
        return "true" if b["v"] else "false"
    if k == "cmp":
        return "%s %s %s" % (a_str(b["l"], tex), b["op"], a_str(b["r"], tex))
    if k == "not":
        inner = b_str(b["e"], tex)
        if b["e"]["k"] in ("bop", "cmp"):
            inner = "(%s)" % inner
        return "not %s" % inner
    if k == "bop":
        l, r = b_str(b["l"], tex), b_str(b["r"], tex)
        if b["l"]["k"] == "bop":
            l = "(%s)" % l
        if b["r"]["k"] == "bop":
            r = "(%s)" % r
        return "%s %s %s" % (l, b["op"], r)
    raise ValueError(b)


def c_str(c, tex=False, top=True):
    k = c["k"]
    if k == "skip":
        return "skip"
    if k == "assign":
        return "%s := %s" % (mono(c["x"], tex), a_str(c["e"], tex))
    if k == "aset":
        return "%s[%s] := %s" % (mono(c["a"], tex), a_str(c["i"], tex),
                                 a_str(c["e"], tex))
    if k == "seq":
        s = "%s; %s" % (c_str(c["l"], tex, False), c_str(c["r"], tex, False))
        return s if top else s
    if k == "if":
        return "if %s then %s else %s" % (b_str(c["b"], tex),
                                          c_str(c["t"], tex, False),
                                          c_str(c["f"], tex, False))
    if k == "while":
        return "while %s do %s" % (b_str(c["b"], tex), c_str(c["c"], tex, False))
    if k == "choice":
        return "%s [] %s" % (c_str(c["l"], tex, False), c_str(c["r"], tex, False))
    raise ValueError(c)


def mono(name, tex):
    return "\\mathtt{%s}" % name.replace("_", "\\_") if tex else name


def st_str(s, tex=False):
    vs = s.get("vars", {})
    arrs = s.get("arrays", {})
    parts = ["%s %s %d" % (mono(k, tex), "\\mapsto" if tex else "|->", v)
             for k, v in sorted(vs.items())]
    parts += ["%s %s [%s]" % (mono(k, tex), "\\mapsto" if tex else "|->",
                              ", ".join(map(str, v)))
              for k, v in sorted(arrs.items())]
    return "[" + ", ".join(parts) + "]"


# ---------------------------------------------------------------- derivations
def deriv_text(node, depth=0, max_depth=None, out=None):
    out = [] if out is None else out
    val = ("= %s" % json.dumps(node["val"])) if "val" in node else ""
    if "out" in node:
        val = "~> %s" % st_str(node["out"])
    subj = node.get("subj", "?")
    out.append("%s[%-11s] <%s, %s> %s" % ("  " * depth, node["rule"], subj,
                                          st_str(node.get("in", {})), val))
    if max_depth is not None and depth >= max_depth:
        if node.get("prem"):
            out.append("%s..." % ("  " * (depth + 1)))
        return out
    for p in node.get("prem", []):
        deriv_text(p, depth + 1, max_depth, out)
    return out


def deriv_latex(node, max_depth=None, depth=0):
    """A self-contained proof tree.

    Rendered with \\frac, the way the handout renders inference rules, so
    the output needs only amsmath --- no bussproofs, no ebproof, nothing to
    install.
    """
    prem = node.get("prem", [])
    if max_depth is not None and depth >= max_depth:
        prem = ["..."] if prem else []
    label = "\\;{\\scriptstyle[\\mathsf{%s}]}" % tex_name(node["rule"])
    concl = tex_conclusion(node)
    if not prem:
        return "%s%s" % (concl, label)
    parts = ["\\vphantom{X}" if p == "..." else deriv_latex(p, max_depth, depth + 1)
             for p in prem]
    return "\\dfrac{%s}{%s}%s" % ("\\qquad ".join(parts), concl, label)


def tex_name(rule):
    return rule.replace("_", "\\_").replace("-", "\\text{-}")


def tex_subj(node):
    """Program text goes inside \\text{\\texttt{...}}.

    Math mode discards spaces, so `while 1 <= x do ...` would come out as one
    run-together word; \\text preserves them.  Only amsmath is needed.
    """
    s = node.get("subj")
    if s is None:
        return "c" if "out" in node else "e"
    esc = (str(s).replace("\\", "").replace("_", "\\_").replace("{", "\\{")
           .replace("}", "\\}").replace("&", "\\&").replace("#", "\\#")
           .replace("%", "\\%").replace("$", "\\$"))
    return "\\text{\\texttt{%s}}" % esc


def tex_conclusion(node):
    sin = st_str(node.get("in", {}), tex=True)
    lhs = "\\langle %s,\\, %s \\rangle" % (tex_subj(node), sin)
    if "out" in node:
        return "%s \\Downarrow %s" % (lhs, st_str(node["out"], tex=True))
    v = node.get("val")
    vs = ("\\mathsf{%s}" % ("true" if v else "false")) if isinstance(v, bool) else str(v)
    return "%s \\Downarrow %s" % (lhs, vs)


# ---------------------------------------------------------------- executions
def run_text(resp):
    rows = []
    configs = resp.get("configs", [])
    for i, cfg in enumerate(configs):
        rows.append((str(i), c_str(cfg["c"]), st_str(cfg["s"])))
    w0 = max([len(r[0]) for r in rows] + [1])
    w1 = min(max([len(r[1]) for r in rows] + [7]), 60)
    out = ["%s  %s  %s" % ("#".ljust(w0), "command".ljust(w1), "state"),
           "%s  %s  %s" % ("-" * w0, "-" * w1, "-" * 20)]
    for a, b, c in rows:
        out.append("%s  %s  %s" % (a.ljust(w0), b[:w1].ljust(w1), c))
    out.append("")
    st = resp.get("status")
    out.append("status: %s after %s step(s)" % (st, resp.get("steps")))
    if st == "terminated":
        out.append("final:  %s" % st_str(resp["final"]))
    if st == "stuck":
        out.append("reason: %s" % resp.get("reason", ""))
    if st == "budget":
        out.append("note:   the budget ran out; this says only that execution")
        out.append("        continued for that many steps.")
    return "\n".join(out)


def run_latex(resp):
    out = ["\\begin{tabular}{r l l}", "\\hline",
           "\\# & command & state \\\\", "\\hline"]
    for i, cfg in enumerate(resp.get("configs", [])):
        out.append("%d & $%s$ & $%s$ \\\\" % (i, c_str(cfg["c"], True),
                                              st_str(cfg["s"], True)))
    out += ["\\hline", "\\end{tabular}"]
    return "\n".join(out)


def classify_text(resp):
    st = resp["status"]
    lines = ["status: %s after %s step(s)" % (st, resp.get("steps"))]
    if st == "diverges":
        lines.append("the configuration at step %s equals the one at step %s"
                     % (resp.get("steps"), resp.get("cycle_start")))
        lines.append("cycle length %s --- on the deterministic fragment this "
                     "PROVES divergence" % resp.get("cycle_length"))
    if st == "unknown":
        lines.append("no configuration repeated within the budget.")
        lines.append("nothing is established: the program may or may not diverge.")
    if st == "terminated":
        lines.append("final:  %s" % st_str(resp["final"]))
    if st == "stuck":
        lines.append("reason: %s" % resp.get("reason", ""))
    return "\n".join(lines)


STANDALONE = """\\documentclass[border=10pt]{standalone}
\\usepackage{amsmath,amssymb}
\\begin{document}
%s
\\end{document}
"""


def main():
    ap = argparse.ArgumentParser(
        description="Render an IMP response as a proof tree or execution table.",
        epilog=("With --from-test alone, render the stored expected response. "
                "Add --cmd to run your implementation on that test and render "
                "its response. Without --from-test, read a JSON response from "
                "standard input."))
    ap.add_argument("--from-test", default=None, metavar="FILE",
                    help="render the expected response stored in a test file")
    ap.add_argument("--cmd", default=None, metavar="CMD",
                    help="with --from-test, run CMD on that test's request")
    ap.add_argument("--timeout", type=float, default=10.0, metavar="SEC",
                    help="seconds allowed for --cmd (default: 10)")
    ap.add_argument("--latex", action="store_true",
                    help="emit LaTeX instead of readable text")
    ap.add_argument("--standalone", action="store_true",
                    help="with --latex, emit a complete compilable document")
    ap.add_argument("--max-depth", type=int, default=None, metavar="N",
                    help="collapse derivation subtrees below depth N")
    args = ap.parse_args()

    if args.cmd and not args.from_test:
        ap.error("--cmd requires --from-test FILE")

    if args.from_test:
        with open(args.from_test) as fh:
            test = json.load(fh)
        if args.cmd:
            try:
                process = subprocess.run(
                    args.cmd, shell=True,
                    input=json.dumps(test["request"], separators=(",", ":")),
                    capture_output=True, text=True, timeout=args.timeout)
            except subprocess.TimeoutExpired:
                ap.error("--cmd timed out after %g seconds" % args.timeout)
            if process.returncode != 0:
                detail = process.stderr.strip() or "(no stderr)"
                ap.error("--cmd exited with status %d:\n%s"
                         % (process.returncode, detail))
            try:
                resp = json.loads(process.stdout)
            except json.JSONDecodeError as error:
                ap.error("--cmd output is not valid JSON: %s at line %d column %d"
                         % (error.msg, error.lineno, error.colno))
        else:
            resp = test["expected"]
    else:
        raw = sys.stdin.read()
        if not raw.strip():
            ap.error("provide --from-test FILE or pipe one JSON response to stdin")
        try:
            resp = json.loads(raw)
        except json.JSONDecodeError as error:
            ap.error("stdin is not valid JSON: %s at line %d column %d"
                     % (error.msg, error.lineno, error.colno))

    if resp.get("status") == "malformed":
        print("malformed input:")
        for r in resp.get("reasons", []):
            print("  - %s" % r)
        return

    if "derivation" in resp:
        if args.latex:
            expr = deriv_latex(resp["derivation"], args.max_depth)
            # The standalone class does not accept \\[ ... \\] at top level, so
            # the self-contained document uses inline math with \\displaystyle.
            print(STANDALONE % ("$\\displaystyle %s$" % expr) if args.standalone
                  else "\\[\n%s\n\\]" % expr)
        else:
            print("\n".join(deriv_text(resp["derivation"],
                                       max_depth=args.max_depth)))
            print("\nfinal: %s" % st_str(resp["final"]))
        return

    if "configs" in resp:
        if args.latex:
            body = run_latex(resp)
            print(STANDALONE % body if args.standalone else body)
        else:
            print(run_text(resp))
        return

    if "finals_found" in resp:
        print("final states found: %d%s"
              % (len(resp["finals_found"]),
                 "  (search truncated!)" if resp.get("truncated") else ""))
        for s in resp["finals_found"]:
            print("  %s" % st_str(s))
        if resp.get("stuck_found"):
            print("a stuck configuration was also reachable")
        return

    if "next" in resp:
        print("one step ->")
        print("  command: %s" % c_str(resp["next"]["c"]))
        print("  state:   %s" % st_str(resp["next"]["s"]))
        return

    print(classify_text(resp))


if __name__ == "__main__":
    main()
