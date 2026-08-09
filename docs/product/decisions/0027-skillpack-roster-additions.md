# PDR-0027 — Add axiom-experiment-formalisation to the Simic plugin roster; confirm contract-engineering current

Date: 2026-08-09   Status: accepted   Author: Claude (product-owner session 12)
Owner sign-off: RECEIVED 2026-08-09 — owner-stated: "experiment
formalisation and contract engineering are both for simic."
Related: PDR-0011 (skill capability roster), PDR-0015 (plugin roster
localized), simic-357c92664c (ADR-0002 regime — the pack's Tier-1
record-annotation discipline becomes relevant once records exist)

## Context

The upstream skillpacks marketplace (tachyon-beep/skillpacks) shipped
axiom-experiment-formalisation (EXPO/SUMO experiment-record formalisation,
v0.2.1) on 2026-08-08 and post-ship review fixes for
axiom-contract-engineering on 2026-08-09. Neither was in the Simic project
roster; the session's marketplace fetch surfaced both and the owner
confirmed both are for Simic.

## The call

- Installed **axiom-experiment-formalisation v0.2.1 at project scope** for
  /home/john/simic (SHA ca22e854, marketplace head). Loads from the next
  session. `.claude/settings.json` gains the enabledPlugins line
  (committed this checkpoint).
- **axiom-contract-engineering needed no action**: the installed copy is
  already pinned to the same head SHA, which includes the post-ship fixes
  (1 high, 11 medium).

Also noted for the roster's division of labour: the new pack's own
boundary routes fleet-size/pre-registration statistics to
counterfactual-statistics (already installed) and record enforcement to
contract-engineering; its distinctive contribution — Tier-1 ontology
annotation over typed records — becomes actionable when Leyline records
exist (Phase A onward) and pairs with the ADR-0002 information-management
regime.

## Reversal trigger

If the pack goes two review cycles unused once Phase A records exist (its
formalisation-triage sheet's own "honest exit" — RDF cosplay with no named
consumer), remove it from the project roster and record the removal
against PDR-0011.
