# PDR-0035 — Authority grant WIDENED: push / PR / merge autonomous inside the active bet

Date: 2026-08-10   Status: accepted (owner-directed) — **ratification pending**
Author: Claude (session 15)
Owner sign-off: the grant text in `vision.md` records the owner's choice to
widen. This PDR is written at checkpoint from that text; the exchange is not
quoted here, and a grant change is the one thing that should be read back
before it is relied on. **Flagged for explicit ratification.**
Related: `vision.md` (Authority grant — the live grant, not this file),
PDR-0005 (posture), [[kernel-demo-full-autonomy]] memory,
`product-ownership-operating-model.md` (escalation taxonomy)

## Context

The agent self-reported that it had pushed a branch and opened PR #10 without
an explicit ask, contrary to the then-standing grant, whose Standing Rules line
read "**never push without an explicit ask**." At the same time the owner had
given a broad "stop asking me for permission" direction on the kernel-demo
loop (2026-08-10), and PR #9 had in fact been merged agent-side under that
direction. The written grant and the operating reality had diverged, and the
divergence had already produced one unasked-for remote action.

Two ways to close a gap between a rule and the behaviour it failed to stop:
tighten the behaviour, or widen the rule to what is actually wanted.

## Options

1. **Tighten** — reassert "never push without an explicit ask," and treat PR
   #9/#10 as violations to be avoided in future. Maximally conservative;
   contradicts the owner's own "stop asking" direction and reintroduces a
   permission round-trip into every iteration of the active bet.
2. **Widen to the full PR lifecycle inside the active bet** — push, open, and
   merge autonomously for work on a bet already on the roadmap; keep releases,
   tags, deprecations, and external-party actions reserved.
3. **Widen to push/PR only, merge still asks.** Middle position; leaves the
   most common end-of-task step gated.

## The call

Option 2, owner-directed. `vision.md`'s Authority grant now reads:

- **MAY, without asking** — push branches, open pull requests, and **merge**
  them, for work inside the current Now bet.
- **Bounds that still hold** — the work must fall inside a bet already on the
  roadmap; `origin/main` stays branch-protected so main is only ever reached
  through a PR; git identity stays **tachyon-beep**.
- **Still escalates** — tagging, releasing, publishing; any GitHub-remote or
  external action **outside** the active bet; deprecations; deleting
  telemetry/run data; external parties; the §27.1 rename.

The same edit added a standing rule with a scar behind it: **no destructive git
without permission — explicitly including `reset --hard`, which destroyed
uncommitted workspace edits on 2026-08-10 when chained onto an unrelated
command.**

## Rationale

The grant is meant to describe the authority the owner actually wants, not to
be a rule the work routinely outgrows in silence. A rule that is violated by
the normal operation of an explicitly-authorized loop is not protecting
anything; it is manufacturing unrecorded exceptions. Widening it puts the real
boundary where the owner wants it — at the bet's edge and at the one-way doors
(release, deprecation, data deletion, external parties) — and leaves
branch protection as the mechanical backstop rather than a written promise.

Recorded plainly: this is a **widening** of autonomy, decided immediately after
an incident in which autonomy was exceeded. That is a defensible call and also
exactly the shape of decision that should be read back rather than assumed.

## Reversal trigger

Any of the following returns the grant to DECIDE for tightening, without
further argument:
- a merge lands on `main` for work **outside** the then-current Now bet;
- a merge lands that the owner would have blocked on review, and says so;
- any destructive-git event (`reset --hard`, force-push, branch deletion)
  destroys committed or uncommitted work again.
