# ADR-0019 — Reopen the bounded comparison: C1 is tested against uniform scale-up, targeted static becomes an oracle ceiling
<!-- adr-meta:begin — append-only; rules: README.md#metadata-and-immutability -->

Date: 2026-10-09 · Status: proposed
Deciders: John (owner signature pending, PDR-0057 D2) · Tracker: simic-f73351380d

Amends: ADR-0018
Amended-by: —
Supersedes: —
Superseded-by: —
<!-- adr-meta:end — everything below is IMMUTABLE body (ADR-0017) -->

## Context

ADR-0018 compared three arms on one bounded host: no added capacity, the same extra
capacity trained from the start ("static"), and a scheduled graft. Its consequence clause
reads: "Reopen the design if the static control wins at the declared cost, or if
measurement uncertainty prevents a credible comparison; do not respond merely by enlarging
the controller."

Static won. Rung 3 read partial capture on both seed types (PDR-0052). Rung 4 found that
earlier grafts are better and that the graft never beats static at 10 epochs, tying it on
the median seed at 20 (PDR-0055 outcome,
`docs/results/2026-10-09-rung4-timing-horizon.md`).

ADR-0018's static arm places the graft's own module at the known deficit site from step
zero. Building it requires the diagnosis in advance. The founding principle the owner stated
on 2026-10-09 ("start by training a small model and inject extra parameters where you have
issue", instead of "training a massive model") has a different alternative: a larger model
with no diagnosis. The first claim (`docs/design/01-claim.md#4-non-goals`) lists
"static over-provisioning" among its comparators without fixing which form.

## Decision

Reopen the comparison as ADR-0018 directs, without enlarging the controller:
- **The efficiency claim (C1)** is tested against **uniform scale-up**: the same host widened
  everywhere, trained from step zero on the same future, at several parameter multiples.
  The result is reported as the largest multiple the graft is non-inferior to.
- **Targeted static** stays in every fleet that can carry it, reported as an **oracle
  ceiling**: what knowing the right module and site in advance is worth.
- **Recorded results stand.** Static's wins in rungs 3 and 4 are not reinterpreted; they
  answer the question ADR-0018 asked.
- The sequence of studies is PDR-0057's gates G0–G5.

## Displaced constraints

None constitutional. No invariant, namespec entry or authority boundary changes. The
displaced text is ADR-0018's single-comparator framing ("Compare no added capacity, that
same extra capacity trained normally from the start, and a prescribed graft"), which for C1
now carries uniform scale-up as the comparator and targeted static as a ceiling.

## Options considered

- **Keep targeted static as the comparator.** It lost because it tests a stronger claim
  than the principle makes: a graft can only match it by matching foreknowledge.
- **Drop targeted static.** It lost because the ceiling is informative, and dropping a
  control after it won would look like rescuing the graft.
- **Stop the ladder.** Not chosen by Claude. ADR-0018 asks for a reopened design, and
  stopping is the owner's call.

## Consequences

- This is a comparator change made after seeing data. It is made in the direction that
  tests the owner's principle, not one that favours the graft: G1 can refute C1 at bounded
  scale on its most favourable host (PDR-0057 D4).
- Fleets that test C1 add width-scaled no-op hosts, with their realised parameter multiple
  recorded.
- The vision's standing line ("static over-provisioning … beats the hand-built scheduled
  graft") stays true and is not edited by this ADR. A scoped C1 clause is proposed in
  PDR-0057 for owner read-back.
