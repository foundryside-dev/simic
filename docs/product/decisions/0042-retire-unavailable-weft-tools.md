# PDR-0042 — Retire the unavailable Weft integrations: Legis, Wardline, Warpline

Date: 2026-10-08   Status: accepted   Author: Claude (session 17)
Owner sign-off: "you can disregard wardline for now, it is being rebuilt";
"clean out the tools that aren't aailbile anymore including wardline and the
othe two" (2026-10-08).
Related: PDR-0010 and PDR-0030 (where these tools entered),
ADR-0015 (three-tier trust model, unchanged), `simic-8db0b87ed6`,
`simic-2035316005` (re-mark the bounded seams)

## Context

At session start, three configured MCP servers failed with `ENOENT`:
`~/.local/bin/legis`, `~/.local/bin/wardline` and
`~/.local/bin/warpline-mcp` no longer exist. Wardline is being rebuilt
upstream. Two SessionStart hooks also called the missing `warpline` and
`legis` binaries.

The bounded comparison had a harder dependency than configuration. It
imported the no-op `weft-markers` decorators from an absolute path inside
the Wardline checkout (`/home/john/wardline/packages/weft-markers`). It also
pinned that file's SHA256 and re-hashed it at **every training run**. So the
upstream rebuild would have stopped the experiment from running at all, for
reasons that have nothing to do with the science.

## The call

Remove every live integration with the three tools:

- the three MCP server entries in `.mcp.json`;
- the two SessionStart hooks;
- the `legis-workflow`, `wardline-gate` and `warpline-workflow` skills, under
  both `.claude/skills/` and `.agents/skills/`;
- `weft.toml`, which was Wardline-only;
- the Legis and Wardline lines in `.gitignore`;
- the three tool sections in `AGENTS.md`;
- the `weft-markers` dependency, its decorators and SHA256 pins in
  `experiments/bounded_comparison.py` and `experiments/bounded_data.py`, and
  `tests/unit/test_bounded_wardline.py`, which only tested scanner
  recognition.

**Every runtime validator stays.** The decorators were annotations for a
static scanner and did no work at runtime. The checks that actually reject
malformed input, missing evidence and source drift are unchanged, and the
contract tests still exercise them.

Not removed:

- Local ignored state under `.weft/` (`legis`, `wardline`, `warpline`) and
  `.wardline/`. Legis's directory may hold an append-only audit trail, and the
  grant reserves deleting such data to the owner.
- Historical ADRs, PDRs and reviews that mention the tools. They are records
  of their time.
- ADR-0015's three-tier trust model. It is doctrine, not tooling; only its
  mechanical enforcement is suspended, as it already was for the kernel demo.

## Consequences

- No static trust-boundary gate covers the bounded modules until Wardline
  returns. Runtime validation and contract tests are the only assurance, as
  they were for the kernel demo throughout.
- The 2026-10-08 pilot run can no longer be passed to `evaluate`, because the
  runner's source has changed. Evaluation was never authorized for it.
- `c40972d` remains the reference for how the seams were marked. Re-marking
  them is `simic-2035316005`.

## Reversal trigger

Wardline, Legis or Warpline is installed again with a working launcher. Each
returns through its own decision, not through a revert of this one. For
Wardline, `simic-2035316005` re-applies the markers against whatever
dependency form the rebuilt package ships, which should not be an absolute
path into a source checkout.

## Correction (2026-10-08, same session)

An independent review of `360b79c` found a factual error in "The call".
`tests/unit/test_bounded_wardline.py` was **not** scanner-only. Its first four
test functions (14 test cases) exercised runtime refusals in `validated_spec`,
`validated_data`, `evaluation_record` and `publish_evaluation`, and no other
test covered them. Deleting the file left those paths untested, so the claim
that "the contract tests still exercise them" was false between `360b79c` and
the fix. The fix restores those tests unchanged as
`tests/unit/test_bounded_contracts.py`. Only the marker-drift test and the
four scanner witnesses stay deleted.
