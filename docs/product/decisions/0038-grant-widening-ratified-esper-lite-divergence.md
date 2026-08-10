# PDR-0038 — Grant widening RATIFIED; the divergence from esper-lite's grant is deliberate

Date: 2026-08-10   Status: accepted   Author: Claude (session 15)
Owner sign-off: RECEIVED — the owner was shown the two grants side by side with
the contradiction stated, and chose "keep Simic's widening, leave esper-lite
alone. Divergence is deliberate and recorded."
Confirms (does not supersede): PDR-0035, whose status was
"accepted (owner-directed) — ratification pending"
Related: `vision.md` (the live grant), `~/esper-lite/docs/product/vision.md`

## Context

PDR-0035 widened Simic's authority grant so push / open-PR / **merge** inside
the active bet are autonomous, and flagged it for ratification because a grant
change should be read back rather than assumed.

The owner's answer directed a comparison against the parent grant. That
comparison found a **direct contradiction** on the single most consequential
clause, not a drift:

| Clause | esper-lite (`Last reviewed: 2026-07-10`) | Simic (widened 2026-08-10) |
|---|---|---|
| push a branch | **ESCALATE** — "never push without an explicit ask" | AUTO inside the active bet |
| open a PR | **ESCALATE** — "any GitHub-remote/external action" | AUTO inside the active bet |
| merge a PR | **ESCALATE** | AUTO inside the active bet |
| tag / release | ESCALATE | ESCALATE |
| outside the active bet | ESCALATE | ESCALATE |
| destructive git | permission required | permission required, **and `reset --hard` named explicitly** |

Everything else — the run authorization, the experiment-value principle, the
identity rule, the escalation taxonomy — is already carried over verbatim and
does not diverge.

"Simic should inherit that grant" therefore had two opposite readings: adopt the
parent verbatim and *revoke* the widening, or treat esper-lite as the base from
which Simic has deliberately diverged. Rather than pick, the choice was put to
the owner with the consequence of each spelled out.

## Options

1. **Inherit verbatim** — revoke the widening; all remote actions escalate again.
2. **Sync both** — carry the widening back into esper-lite so one grant governs
   both projects.
3. **Keep Simic's widening; leave esper-lite alone** — the grants differ on this
   clause on purpose.

## The call

Option 3, owner-selected. Simic's grant stands as widened. esper-lite's grant is
**not** edited — it governs a project in a different phase, and a vision change
there would need its own PDR in its own workspace anyway.

PDR-0035's ratification flag is hereby **cleared**. The `vision.md` status line
records the ratification and the deliberate divergence, so a future session
comparing the two files finds the difference explained rather than treating it
as drift to be "fixed" back.

## Rationale

The two projects are not in the same phase. esper-lite's grant was written for a
system with live GPU runs and published results, where a remote action can
expose a half-formed empirical claim. Simic is two days old, pre-Phase-A, and
its Now bet is a self-contained experiment behind a branch-protected main. The
mechanical backstop — main reachable only through a PR — carries the weight that
esper-lite's "never push" clause carried by policy.

Recorded plainly, because it will look odd later: Simic's agent has *more*
remote autonomy than esper-lite's, on a younger project. That is the owner's
call, made with the contradiction in front of him.

## Reversal trigger

Unchanged from PDR-0035, and still live:
- a merge lands on `main` for work **outside** the then-current Now bet;
- a merge lands that the owner would have blocked on review, and says so;
- any destructive-git event destroys committed or uncommitted work again.

Additionally: if esper-lite is ever revived as an active project under the same
agent, the two grants are reconciled at that point rather than left to diverge
silently.
