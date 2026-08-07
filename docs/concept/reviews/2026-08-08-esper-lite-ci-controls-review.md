# Esper-lite CI & Controls Review — inspiration and cautionary tales for Simic

Date: 2026-08-08 · Reviewer: Claude (product-owner session) · Requested by: john
Scope: `~/esper-lite` — `.github/workflows/test-suite.yml`, `pytest.ini`,
`pyproject.toml`, the three boundary linters and their YAML whitelists,
`tests/conftest.py`, `tests/meta/`, `scripts/proof_packet.py`, and the product
workspace's defect register. **Nothing here is to be copied directly**; each item
is a principle to re-derive inside Simic's constitution, cited as INV-nn where it
maps to an HLD §18 invariant.

## What esper-lite actually runs

One workflow, six jobs: a 5-minute lint job (three custom AST linters + ruff);
mypy (strict-ish, per-module strictness gradient, honest test-code relaxations);
Hypothesis property tests as their own lane; unit+integration with a 75% coverage
threshold whose comment honestly explains why it isn't 80%; a web-dashboard job;
and a nightly full suite (thorough Hypothesis profile, slow, stress). Plus a
non-gating `weft-shadow` job capturing wardline/loomweave/legis/warpline reports
as artifacts. Test lanes are marker-driven with `--strict-markers`; the default
lane excludes integration/stress/property/slow. An autouse conftest fixture
reseeds random/numpy/torch per test and captures/restores a known process-global
(`MaskedCategorical.validate`) so training tests cannot leak state. Mutation
testing (mutmut) is scoped to the three highest-stakes surfaces, not the repo.

## Inspiration — principles worth re-deriving

1. **Constitutional linters with whitelists that carry owner + reason.**
   `lint_leyline_types.py` (all shared types live in leyline/ unless allowed) is
   the direct ancestor of INV-2 enforcement; `lint_defensive_patterns.py`
   (getattr/hasattr/silent-except forbidden unless justified) mechanises INV-38's
   fail-loudly culture; `lint_gpu_sync.py` compensates statically for CI having
   no GPU. All three run in the 5-minute lint job on every PR — authority
   enforcement as cheap AST checks, not slow integration tests. Simic's
   forbidden-import and namespec checks should live in exactly this position.
2. **Lane discipline.** Fast default lane; explicit opt-in lanes; nightly
   thorough/stress; thresholds that match what the job actually runs, with the
   discrepancy documented in a comment rather than hidden. Maps cleanly onto the
   §20 test tree — with `authority/`, `blinding/`, `namespec/` in the fast
   default lane since they are cheap by construction.
3. **Meta-tests** (`tests/meta/`): tests that check contracts-vs-docs agreement
   (obs shape docs, defensive-pattern contract). Precedent for PDR-0002's
   citation lint — INV-nn references resolving against the HLD is a meta-test.
4. **Proof packets: pre-run instrument verification.** `proof_packet.py` checks
   live configuration against pre-registered baselines pinned by content hash in
   leyline (`FIXED_SCHEDULE_*_HASH`). This is INV-20's semantic-identity habit
   applied to experiment setup, and the ancestor of Urabrask's pre-flight role:
   an experiment may not start unless the instrument proves it is the instrument
   the pre-registration named.
5. **Import-isolation tests in fresh subprocesses** plus an import-cycle script —
   structural properties tested at the process level, not assumed from lint.
6. **Scoped mutation testing.** Mutmut aimed at the decision surfaces (policy,
   slot state machine, reward). Simic analogue: mutate the warrant checks, the
   blinding constructors, the deterministic resolver — the code whose silent
   failure is constitutional failure — not the whole tree.
7. **Shadow-then-gate adoption.** The `weft-shadow` job runs the whole weft suite
   `continue-on-error`, uploading artifacts. New gates arrive observable-first,
   then get promoted. Right pattern for wardline/legis in Simic too.
8. **The defect register as a WHEN-ledger.** Defects classified by the gate they
   must land before (pre-next-run / scheduled schema batch / deferred-priced /
   experiment-addressed), with the standing rule "nothing is fixed silently
   mid-arc — every fix routes through its stated gate." In an experiment-bearing
   codebase, an opportunistic hot-fix invalidates the instrument. Simic will need
   this discipline verbatim in spirit: defect scheduling is part of matched-
   control integrity, kin to INV-33.

## Cautionary tales — what it cost, and the Simic counter-design

1. **The silent-default class (the big one).** Three independent instances of
   "unmeasured means zero" (reward None→0, obs None→0, leyline omitted-field→0)
   taught the policy that permanence was worthless — *because the pipeline said
   so*. The retrofit cost an entire gate family (dead-dim sweeps, per-dim
   liveness/sentinel/clip stats, a reward–obs coverage report classifying every
   input as observed / inferable / intentionally-hidden / accidentally-
   unplumbed). Counter-design: INV-38 is the principle, but it needs mechanics
   from day one — Leyline schemas carry value/observed/age triples for
   low-cadence signals, never bare defaults; per-dim liveness is a standing QA
   check, not a forensic tool.
2. **Hand-offset schema drift.** The A1/A2 defect class: a flat feature vector
   with hand-maintained offsets, where adding a dim without bumping
   `OBS_V4_SLOT_FEATURE_SIZE` makes slot-1 silently alias slot-0's new dim; a
   field added to a dataclass but not to `to_leyline()` transports as its
   default forever. Their own converged fix — generated layouts (named blocks,
   layout hash, no hand offsets) plus exhaustive transport-completeness tests
   (a non-default value survives every hop) — arrived only after the damage.
   Simic: TelemetryEnvelope and every serialised contract get generated layouts
   and transport tests in Phase A, before a single consumer exists.
3. **Whitelist rot.** `leyline_boundaries.yaml` already carries "TODO:
   Cross-domain enum, migrate to leyline" — an exception that became load-
   bearing. Counter-design: authority-boundary violations get *no* allow-list
   (constitutional, fail closed); softer whitelists (sync points, defensive
   patterns) carry owner + reason + **expiry**, wardline-style.
4. **Determinism was per-test, not systemic.** Seeding fixtures and a process-
   global leak guard exist, but there is no bitwise replay gate in CI — nothing
   like INV-5. Esper-lite could not have caught a divergence the way Simic must.
   Counter-design: the Academy determinism gate is a CI lane (CPU-exact profile)
   from the phase that creates replay, not a local script.
5. **Run-artifact litter.** Telemetry logs, profiler output, coverage HTML at
   repo root; a `mutants/` workspace needing mypy excludes and careful copy
   rules. Trivial individually; collectively it blurs what is instrument and
   what is residue. Simic: runs write outside the tree from the first commit —
   history is Sarpadia's job, not the repo root's.
6. **`-x` in CI.** Stop-at-first-failure gives fast signal but reports one
   defect per run on a broken branch. Fine for PR lanes; the nightly should
   report breadth.

## Disposition

Feeds the CI-skeleton design task (Phase A/B). The register's deepest lessons —
silent defaults, hand-offset drift, fix-scheduling discipline — are candidate
inputs to the decision gate simic-0dd5362f05's adjudication session where they
touch contract shapes (value/observed/age triples in §9 schemas).
