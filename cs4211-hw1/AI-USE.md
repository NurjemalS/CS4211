# AI use declaration

Name: Nurjemal Saryyeva
Student number:

---

## Tools

- Claude Code — the entire Python `submission/` implementation: `big_step.py`
  (Part A), `small_step.py` (Part B), and `analysis.py` (Parts C and the
  bonus).

## Substantive assistance

- Part A (`big_step.py`): generated `big_a`, `big_b`, and `big_c` directly
  from the definitive big-step rules in the handout, including the
  three-premise `While-True` derivation and the evaluate-index-then-check-
  bound-then-evaluate-value order for `Arr-Write`.
- Part B (`small_step.py`): generated `step_a`, `step_b`, `step_c`, and `run`
  from the small-step congruence rules, keeping the left-to-right operand
  order (`A-Op-L`/`A-Op-R`, `B-Cmp-L`/`B-Cmp-R`, `B-Con-L`/`B-Con-R`) and the
  strict, non-short-circuiting treatment of `and`/`or`.
- Part C (`analysis.py`): generated `classify`, checking finality, then a
  repeated configuration, then the budget, in that order, using
  `Configuration.key()` for cycle detection.
- Bonus (`analysis.py`): generated `step_all` and `explore`. `step_all`
  required one case beyond the two `[S-Choice-*]` rules: when `choice`
  appears as the first command of a `seq` (test `f04`), the congruence rule
  `[S-Seq]` must fan out over every successor of the first command, not just
  one, so `step_all` recurses into `SequenceCommand.first` instead of
  delegating straight to the deterministic `step_c`.

## One suggestion you accepted, and one you rejected

- Accepted: sorting `explore`'s final states by the compact, sort-keyed JSON
  encoding of each state (`json.dumps(encode_state(s), sort_keys=True,
  separators=(",", ":"))`), exactly as SPEC.md section 5.5 requires, rather
  than by an ad hoc tuple ordering that would not have matched the graded
  comparison.
- Rejected: none. The first draft of `step_all` treated `choice` as only a
  top-level form and failed test `f04` (`choice` nested inside a `seq`); this
  was caught immediately by `validate.py` and fixed by recursing through
  `SequenceCommand`, so it was a bug fix rather than a rejected suggestion.

---

Disclosure does not reduce your mark, and no marks are awarded for what you
write here. You remain responsible for every part of your submission and must
be able to explain and modify it.
