# PDR-0033 — Kernel demo implementation accepted and merged to main (PR #9)

Date: 2026-08-10   Status: accepted   Author: Claude (session 14)
Owner sign-off: RECEIVED in-session ("When you're ready to merge, please
do it via a PR to main" + "ok, lets do it now and then do the PR merge").
Related: PDR-0031 (moved to Now), PDR-0032 (rev 6.1 amendment), PDR-0029
(proof-of-concept purpose — stands, incl. never-citable-as-§28-evidence)

## Context

PDR-0031 recorded the kernel demo as a Now bet with implementation
starting. Session 14 (with the owner's parallel direction) completed all
18 plan tasks as `experiments/kernel_demo.py` (~3,900 lines, 7 CLI modes)
plus plotting sidecar and 113 unit tests, then ran three acceptance-grade
review waves before merge: a 35-agent code-review workflow (10 confirmed
findings — crash-resume granularity theme), a fable generalist fix pass
(8 defects — headline: gate 3's noise floor was statistically
unpassable), and four SME role reviews (pytorch / determinism /
counterfactual-statistics / morphogenesis; ~26 findings). All mechanical
findings were fixed on-branch; the one spec-level finding became
PDR-0032.

## The call

**Accept the implementation against its criteria** (locked spec rev 6.1
conformance, review findings closed or owner-flagged, all gates green:
113 tests, mypy/ruff clean, CPU selftest via the real CLI) **and merge**:
PR #9, merge commit 2b48431, owner-directed. Branch, worktree, and the
SDD workspace cleaned up; tracker simic-4a44ed57c9 closed. The merge
also published the previously-queued 22 local-main commits (the branch
folded local main pre-PR at the owner's direction) — the publish-queue
open question from session 13 is resolved as a side effect.

## Rationale

The bet's implementation phase is done and verified to the standard the
plan set (per-task gates + whole-branch review + SME wave). Holding it
unmerged had no remaining function once the owner directed the merge; the
PR body preserves the acceptance evidence and the residual low-severity
flags.

## Residual (recorded, not blocking)

Low-severity review flags live in PR #9's body and the commit trail:
gate-8 contingency dead code (plan-internal contradiction Task 14 vs 17),
load_for_training seed_namespace filter gap, wardline taint gate inert
repo-wide, CPU freeze fail-open. None blocks Phases A–F; each is a small
owner-optioned hardening.

## Reversal trigger

The bet is NOT done — implementation is. If Operational Phases A–F stall
for more than ~3 weeks (pacing signal, not pressure: no Phase-A GPU
certify by 2026-08-31), the demo's Now slot returns to DECIDE against the
burn-down (which has its own fired signal, see metrics 2026-08-10).
PDR-0029's standing constraint holds: the demo is never citable as §28
evidence; its verdict booleans are the only claim surface.
