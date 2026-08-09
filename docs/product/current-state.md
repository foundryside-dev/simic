# Current State — Simic        Checkpoint: 2026-08-09 (session 9)

## The bet right now
Design hardening — the hld-review burn-down (38 → 0 by 2026-08-31,
pacing signal) — plus the ADR-0002 information-management regime
(simic-357c92664c), now four sessions unstarted. **The pacing warning has
fired**: two consecutive flat sessions (7 and 9 did wiki/site work, 8 was
checkpoint-only); ~1.7 closures per working day needed to make the date.
Public face live, hardened and now deploy-gated: https://simic.foundryside.dev
with the wiki at /design/ (PDR-0018, PR #2 merged 6df7e7a).

**Namespec 2.0 landed post-checkpoint, same day (ADR-0008, PDR-0020,
branch namespec-2.0):** eight domains renamed (Sarpadia→Urborg, Tamiyo→Ugin,
Narset→Aurelia, Tezzeret→Urabrask, Urabrask→Jin-Gitaxias, Augustin→Isperia,
Kasmina→Wrenn, Oona→Tamiyo), full cascade through the constitution, every
design chapter, appendices, root docs, model.dsl + diagrams (re-rendered),
site, wiki (strict build green) and the open tracker titles; mechanics and
all 45 invariants unchanged. Pre-2.0 records read through the ADR-0008
concordance — beware the two reused names (Urabrask, Tamiyo). Publishing
the renamed site/wiki needs the owner-gated merge + push of namespec-2.0.

## In flight
- Nothing claimed. Six wave:1 items remain; simic-d6ea02f9a9 (containment
  owner) stays the natural next. Critical path: simic-0bf2c40dec →
  simic-38a07fad39.
- simic-42e575b93c (NEW, blocked-on-owner): recover or reconstruct the 33
  missing simic-design design-system files — fork decided by whether the
  claude.ai project survives (PDR-0019, proposed).
- Commissioning: both packs still absent from the session roster; the
  training-state applied prompt still awaits owner relay upstream
  (carried since session 6).
- simic-357c92664c (implement ADR-0002) ready, unstarted; plainweave
  seeding needs owner presence at the gate.

## Open questions / blocked-on-owner
- PDR-0019: does the SimicDesignSystem_5a908e project survive anywhere in
  your claude.ai/design UI? (Decides re-export vs reconstruction.)
- Watch the first post-merge Pages deploy: it carries both the new deploy
  gates (PDR-0018) AND the dependabot pymdown-extensions 10.21→11.0.1
  bump (PR #1, merged after PR #2, untested together). Gate failures are
  loud, not silent; local wiki builds will fail the version-drift gate
  until `pip install -U -r tools/wiki/requirements.txt`.
- Pacing warning fired (metrics.md): next DECIDE resumes wave:1 closures
  or re-plans the 2026-08-31 date by PDR — silent drift is the one
  disallowed outcome.
- Tooling, for upstream relay: `filigree issue-list --status open` exited
  144 and ignored the status filter (CLI path; MCP unaffected). Wardline's
  taint gate is inert on this repo (0 declared trust boundaries — green
  means "nothing to check" until boundaries are annotated).

## Last checkpoint did
- PDR-0018 (accepted): recorded the owner-directed static-content review →
  implementation → merge (5 commits, 2 review gates, 2 Criticals caught
  pre-merge) and the durable deploy/build gates; public copy honesty fix.
- PDR-0019 (proposed): design-system recovery fork, owner-gated; tracker
  item simic-42e575b93c created.
- Metrics: burn-down read flat at 38 — second consecutive flat session,
  pacing warning FIRED.
- No bet changed horizon; roadmap untouched.

## Next session, start here
Answer the pacing warning first: claim simic-d6ea02f9a9 and resume wave:1
closures, or re-plan the burn-down date by PDR. Check the post-merge
deploy status before any wiki/site work. PDR-0019's owner question can be
answered in passing and unblocks simic-42e575b93c.
