# Current State — Simic        Checkpoint: 2026-08-08 (session 4 close)

## The bet right now
Design hardening, now fully unblocked: the decision gate is adjudicated
(PDR-0007), the HLD is decomposed into docs/design/ chapters (PDR-0009,
ADR-0001), and the burn-down runs as six region-based waves (PDR-0008) —
moves the design-debt burn-down (41 open `hld-review` items → 0 by
2026-08-31, pacing signal).

## In flight
- Critical path: simic-ae3caf44f1 (lexicographic admission, wave:1) →
  simic-ed2698fafd (Schmitt-trigger hysteresis). The metrics.md harm-ceiling
  guardrail binds to ae3caf44f1's implementation.
- wave:0 remnants: simic-aff80b1843 + simic-e84fe6737c (in progress, claims
  held by claude-fable; both accumulated review findings as comments —
  heading levels, Sanctum/Overwatch, LaTeX rendering, chapter-citation rule),
  simic-a708c5b1b7 (§27.1 ADR, now ready).
- Waves 1–5 stamped as filigree labels (`wave:1-augustin` … `wave:5-scoreboard`);
  pick up with `filigree list --label=wave:N-…`. CI-skeleton design
  (simic-4da299ff46) is a parallel track and carries the doc-lint lane
  requirements as comment #9.
- Backlog: 41 open `hld-review` = 2 in progress + 34 ready + 5 blocked (all
  five behind real dependencies, none behind a decision).

## Open questions / blocked-on-owner
- Nothing escalated this session. Standing gates unchanged: publication and
  any push/tag/external action remain owner-gated; §27.1 formal ADR closure
  is filed as work (simic-a708c5b1b7), the ruling itself is settled (PDR-0006).
- No metric reversal trigger fired (burn-down 43→41 with 23 days to the
  2026-08-31 pacing date; K/N still owed by simic-642c2c1823 before Phase A).

## Last checkpoint did
- Adjudicated all 25 gate items with the owner: 23 accepted (keystone:
  lexicographic admission), Tamiyo rename wontfixed (deliberate promotion —
  owner-stated), fast-landing folded into the §27.3 open decision (PDR-0007).
- Laid out and stamped the six-wave programme (PDR-0008).
- Decomposed the 4,720-line HLD into 34 verified chapters with a four-agent
  tech-writer review — zero blockers (PDR-0009, ADR-0001, commits 0e0f1ea +
  ca25d92); AGENTS.md now points at docs/design/00-INDEX.md; citation
  convention is INV-nn / contract names / path#anchor.
- Name shelf: "weatherlight" available for a future proper noun (recorded on
  simic-a708c5b1b7).

## Next session, start here
Start wave:1: claim simic-ae3caf44f1 (lexicographic admission) — it lands as
an ADR (docs/adr/TEMPLATE.md, name the displaced constraints) editing
docs/design/domains/augustin.md + 07-counterfactual-engine.md. Finishing the
two in-progress wave:0 tasks first is the tidy alternative; their claims
expire 2026-08-09 16:33 UTC — reclaim if stale.
