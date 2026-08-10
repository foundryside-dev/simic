# PDR-0036 — Kernel demo spec rev 6.2: record the per-arm trajectory, its cost and its horizon influence (pre-data amendment)

Date: 2026-08-10   Status: **accepted** 2026-08-11 (was: proposed)
Author: Claude (session 15; status resolved session 16)
Owner sign-off: **RECEIVED 2026-08-11.** Recorded precisely, because this
record exists to prevent an unearned approval claim: the amendment's "The call"
paragraph was read back to the owner verbatim in session 16, and the owner then
directed the merge of PR #13 ("ok, lets merge 13"). PR #13 merged 2026-08-11 as
a merge commit — not squashed, so b9ae1af's retraction of b5c10db's over-claim
survives in history.

This is sign-off *by directed merge after read-back*, which is what the Q1 gate
asked for. It is **not** a claim that the owner reviewed the full rev 6.2 diff
line by line, and the spec header should not be upgraded beyond what this
sentence supports. The PDR's stated failure mode — unconfirmed before Phase A ⇒
amendment dropped, campaign runs on rev 6.1 — did not fire; the campaign runs on
**rev 6.2**.

Prior status, retained for the record: PARTIAL — "I'll take your
recommendations on that, particularly about the per arm telemetry" was assent to
the substance but not to the wording, which is why the spec header said PROPOSED
and the PR was held unmerged.
Related: PDR-0029 (proof-of-concept purpose), PDR-0032 (the rev 6.1 pre-data
precedent this follows), PDR-0033 (implementation accepted),
spec `docs/superpowers/specs/2026-08-09-kernel-demo-design.md`,
analysis `docs/superpowers/reviews/2026-08-10-kernel-demo-enhancement-analysis.md`,
register `docs/superpowers/specs/2026-08-10-kernel-demo-exploratory-register.md`

## Context

A cold read of `experiments/` asked what the demo could record that would
derisk **Simic**, not just settle the demo's own claim. The finding that
mattered: `run_arm` builds a full 20-dimensional `TelemetryRecord` per epoch for
every arm and then discards it. The store would have kept `curve_val` — one
scalar per epoch — so nothing in the campaign would have described the host
**while a graft integrates**.

That is not a gap in the demo's claim; the frozen battery does not need it. It
is a gap in everything Simic asks next. Wrenn's continued tenancy, Emrakul's
decay/lysis, Nissa's post-embodiment observation, and any second-graft study
are all decisions **about an already-grafted host**, and Simic has no empirical
support for any of them today. Divergence would have been counted, not
diagnosable.

The window is the point. `config_hash` covers the whole semantic surface and
`--certify` pins HEAD, so a recording change is free before Phase A and
impossible after it. No store exists. This is the same free-now/unfixable-later
structure as PDR-0032, one rev later.

## Options

1. **Amend now, additively** — add the recording, change nothing the frozen
   battery reads, re-certify.
2. **Leave it** — run the campaign, accept that the post-commit half of Simic
   gets no data from it, and pay for a second campaign later to get it.
3. **Widen the experiment** (menu size, a second slot, host families) — would
   answer more, and breaks the spec's scope pins and five SME panels'
   sign-off. Treated separately: see PDR-0037.

## The call

Option 1, as spec **rev 6.2** — proposed, not yet locked. Recorded per arm:
`telemetry` (the post-decision trajectory), `wall_s` / `peak_mem_bytes` (the
denominator the demo's own "supervision economics" claim otherwise lacked), and
`g_at_horizon` / `rms_ratio_horizon` beside the single blend-entry sample.
Trained Δ-modules go to a `fan_id`-keyed sidecar, never the JSONL, so
`Store.merge()`'s decode/sort/duplicate path is untouched. `SCHEMA_VERSION` → 2.

**Additivity verified rather than asserted:** `frozen_block_hash` is
byte-identical to its pre-amendment value (`4a82c72cb491b285…`) while
`config_hash` moved — the exact signature of a change that needs a re-`--certify`
and nothing else. No gate arithmetic and no verdict boolean moves.

**The wall:** the learner never reads arm telemetry. Post-decision telemetry on
the training path would be a time-travel channel that silently invalidates the
headline. Enforced by a `--selftest` step that poisons arm telemetry and
requires the learner's input to be bit-identical — so the check lands in the
certified artifact — plus unit tests.

Also decided, as part of the same package: the Tier-2 offline studies are
**registered pre-data** (the register file above), so they are secondary
exploratory analysis rather than post-hoc fishing against a one-shot eval.

## Rationale

The demo's stated intellectual role is that its fan store is "the
counterfactual atlas and proven substrate early Momir needs." An atlas that
records only end-state scalars is an atlas of outcomes, not of process — it
cannot answer a single question about a host that already carries a graft, and
those questions are the whole post-commit half of the system. Buying the
answers costs ~70 MB, ~235 MB of Δ weights, and a re-certify, today. After
Phase A it costs a second campaign.

Held as **proposed** deliberately: the spec header records five SME reviews
across three rounds, and its rev 6.1 precedent says "owner-approved" because
the owner approved specific amendment text. Writing "owner-approved" before
anyone read the wording would be a false provenance claim about a human
decision. The status flips on confirmation, not before.

**Correction (2026-08-10, from the rev-6.2 specialist panel):** this PDR
originally justified that posture by saying the header is inherited by "every
future `frozen.json`." **That mechanism claim is false** — `kernel_demo.py`
never reads the spec markdown, and `freeze_manifest`'s `spec_rev` is a
hardcoded string carrying no approval status. The posture stands on the simpler
ground above and needs no mechanism; the false claim is retracted here rather
than left to be discovered. Recorded as a correction, not an edit to the call.

## Reversal trigger

- If `Store.merge()`'s measured resident cost (~277 MB at collect+eval scale)
  proves unworkable at Phase A/B, the pre-stated fallback fires: arm telemetry
  moves to the `fan_id` sidecar, JSONL becomes the index. Pre-stated so the
  choice stays out of post-hoc territory.
- If the owner does not confirm the rev 6.2 text before Phase A is otherwise
  ready to run, the amendment is **dropped, not defaulted in** — the campaign
  runs on rev 6.1 and this PDR is superseded by one recording the drop.
