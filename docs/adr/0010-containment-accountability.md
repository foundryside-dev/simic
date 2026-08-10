# ADR-0010 — Name the owner of emergency containment: rollbacks are Isperia's accountability
<!-- adr-meta:begin — append-only; rules: README.md#metadata-and-immutability -->

Date: 2026-08-09 · Status: accepted
Deciders: John (wave:1 resume, product session 11) · Tracker: simic-d6ea02f9a9
Source: peer review §24
(`../concept/reviews/2026-08-08-esper-pivot-peer-review.md`)

Amends: —
Amended-by: —
Supersedes: —
Superseded-by: —
<!-- adr-meta:end — everything below is IMMUTABLE body (ADR-0017) -->

## Context

INV-28 records emergency containment as distinct from economic judgement but
gives it no owner: "logged and reviewed" with no named authority means in
practice nobody owns it — a real hole in a constitution built on named
authorities. A rollback is evidence that a warrant was issued wrongly, and
warrants are Isperia's sole output (INV-26, INV-27); nothing else in the
system could have prevented the admission. Aurelia answers only "is there a
problem"; Momir only "here, try this".

## Decision

Emergency containment gets a named owner and a route back to the decision.

1. **Detection and the rollback stay mechanical, in Tolaria.** Waiting for
   adjudication while the host produces NaNs would be absurd. On a declared
   safety-invariant breach Tolaria contains immediately, then reports.
   Detect-and-contain is mechanical; accountability is judicial. The report
   is an account of the breach, never an opinion about the candidate —
   Tolaria's neutrality (INV-03) is preserved, which matters because
   "Tolaria decides when to roll back on safety grounds" is a shorter step
   to "Tolaria has opinions about candidates" than it looks.
2. **Accountability is Isperia's.** Every containment event routes back to
   the decision, not just to the log. `AdmissionDecision` already carries
   `evidence_digest`, `selected_semantic_hash`,
   `adjudication_policy_version` and the per-candidate eligibility and veto
   results, so the containment record names the warrant that authorised the
   growth, the policy version in force, and the specific checks that passed
   and should not have. A containment is thereby a defect report against a
   policy — actionable in a way "candidate X was bad" is not.
3. **Blame attaches to the policy version, never to
   Isperia-the-component.** With the initial rule-driven adjudicator this is
   literally true: a rollback means the declared thresholds were wrong, and
   the fix is an ADR and a version bump. Retrospective re-adjudication can
   then ask directly: *under the revised policy, would this warrant have
   issued?* — a regression test for judgement (first-class capability
   tracked as simic-43f5e2264a).
4. **Cost and veto failure never share a code.** The §15.3 failure taxonomy
   (`../design/domains/urborg.md`) gains `CONTAINMENT_CATASTROPHE`,
   distinct from `INTEGRATION_SHOCK`: one is a cost, the other is a veto
   failure.

## Displaced constraints

INV-28 amended.

- Old: "**Containment distinction:** emergency safety reduction is recorded
  as containment, not disguised as economic judgement."
- New: "**Containment accountability:** emergency safety reduction is
  recorded as containment, never disguised as economic judgement; Tolaria
  detects and contains mechanically, and every containment is adjudicated by
  Isperia back to the admitting warrant and the `adjudication_policy_version`
  in force — a rollback is a defect report against that policy version.
  (ADR-0010)"

No other invariant changes. INV-03 (Tolaria neutrality), INV-26/27
(warrants), and INV-29 (authority separation) are load-bearing context and
unchanged.

## Options considered

- **No named owner (status quo).** Rejected: an unowned review is no
  review; the constitution names authorities everywhere else.
- **Tolaria owns accountability.** Rejected: collapses detection into
  judgement and erodes INV-03 — the substrate acquires opinions about
  candidates.
- **Aurelia owns it (it commissioned the growth).** Rejected: Aurelia's
  authority is pre-commit only (INV-29) and its question is "is there a
  problem", not "should this have been admitted"; the preventable act was
  the warrant.
- **Emrakul owns it (it removes structure).** Rejected: Emrakul executes
  maintenance verdicts post-commit; containment is precisely the case that
  bypasses ordinary maintenance adjudication, and the accountability
  question concerns the admission, not the removal.

## Consequences

Isperia's chapter carries the accountability subsection and invariant;
Tolaria's chapter pins the detect-and-contain boundary; the growth-model
transition rules and Wrenn's removal exception cite the split; the Urborg
taxonomy gains `CONTAINMENT_CATASTROPHE` with an explicit never-share-a-code
note. The `ContainmentEvent` record shape lands with the §9 Warrant record
definitions (simic-0bf2c40dec), binding warrant id, policy version and the
passed-check list. Rollbacks are rare by construction, so this channel alone
under-feeds the veto; near-miss recording is tracked separately (the
tail-veto training-signal wave:1 issue).

Reversal trigger: if the rule-driven adjudicator is replaced by a learned
one such that "the declared thresholds were wrong" stops being literally
true, revisit where policy-defect blame attaches — by ADR, never silently.
