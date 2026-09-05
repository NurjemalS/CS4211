#!/usr/bin/env python3
"""GIVEN process driver for the Python starter code.

Run this file.  Implement the semantics in big_step.py, small_step.py, and
analysis.py.  The driver decodes JSON into typed model objects, calls the
appropriate semantic function, and converts the result back to JSON.
"""

import json
import sys
from typing import Any, Dict, Mapping

from analysis import classify, explore
from big_step import big_c
from codec import (
    decode_request,
    encode_classify_result,
    encode_command,
    encode_derivation,
    encode_explore_result,
    encode_run_result,
    encode_state,
)
from model import Malformed, Skip, Stuck
from small_step import run, step_c


# Big-step loop derivations and their JSON encodings are recursive trees.
# Python's default recursion limit is low enough to reject a few hundred
# textbook loop iterations, so give correct recursive implementations room.
sys.setrecursionlimit(max(sys.getrecursionlimit(), 10000))


def handle(raw_request: Mapping[str, Any]) -> Dict[str, Any]:
    """Decode and answer one request from validate.py."""

    request = decode_request(raw_request)
    try:
        if request.mode == "bigstep":
            result = big_c(request.program, request.state, request.arithmetic)
            return {
                "status": "ok",
                "final": encode_state(result.value),
                "derivation": encode_derivation(result.derivation),
            }

        if request.mode == "step":
            # Final and stuck configurations both lack a successor, but they
            # are different outcomes.  Check finality here so step_c receives
            # only a non-final command; only then can None mean "stuck".
            if isinstance(request.program, Skip):
                return {"status": "final"}
            next_configuration = step_c(
                request.program, request.state, request.arithmetic
            )
            if next_configuration is None:
                return {"status": "stuck", "reason": "no rule applies"}
            return {
                "status": "ok",
                "next": {
                    "c": encode_command(next_configuration.command),
                    "s": encode_state(next_configuration.state),
                },
            }

        if request.mode == "run":
            return encode_run_result(
                run(
                    request.program,
                    request.state,
                    request.arithmetic,
                    request.budget,
                )
            )

        if request.mode == "classify":
            return encode_classify_result(
                classify(
                    request.program,
                    request.state,
                    request.arithmetic,
                    request.budget,
                )
            )

        if request.mode == "explore":
            return encode_explore_result(
                explore(
                    request.program,
                    request.state,
                    request.arithmetic,
                    request.budget,
                )
            )

        return {"status": "error", "reason": "unknown mode %r" % request.mode}
    except Stuck as error:
        return {"status": "stuck", "reason": str(error)}
    except Malformed as error:
        return {"status": "malformed", "reasons": [str(error)]}


def main() -> None:
    request: Dict[str, Any] = json.load(sys.stdin)
    json.dump(handle(request), sys.stdout, separators=(",", ":"))
    sys.stdout.write("\n")


if __name__ == "__main__":
    main()
