# ADR-0003 — Close the project-name decision: Simic through publication, predecessors behind a clean seam

Date: 2026-08-08 · Status: accepted
Deciders: John (owner; in-session rulings 2026-08-08) · Tracker: simic-a708c5b1b7, simic-3a17fe545d, PDR-0006

> **Namespec note (ADR-0008):** this record predates Namespec 2.0 and uses
> Namespec 1.0 names; read it through the concordance in
> [`0008-namespec-2.0.md`](0008-namespec-2.0.md).

## Context

The HLD left the umbrella name open — remain `simic`, return to `esper`, or
adopt another name (`../design/programme/risks-and-open-decisions.md#271-project-level-name--decided`).
The working-name half had to settle before Phase A creates `src/simic/`;
the publication-identity half was headed for deferral to the publication
gate. PDR-0006 (`../product/decisions/0006-simic-through-publication-clean-seam.md`)
resolved both at product level and promised formal HLD closure as an ADR
under the PDR-0002 tiering. Phase A scaffolding has now landed, so the
working name must be contingency-free.

A separate hld-review gate ruling touching Namespec 1.0 (simic-3a17fe545d,
adjudicated 2026-08-08) is recorded here in the same Tier 1 record so the
reaffirmation has a citable home.

## Decision

**Simic is the repository, package, and presumptive publication name.** The
predecessors (ESPER, ESPER LITE) present as lineage history behind a clean
seam, not as identity: whatever succeeds is Simic. The canonical framing
formula for any retrospective reference is **"early versions of the simic
project (known as esper) found that…"** — continuity flows backward into the
Simic name, never forward out of the esper one. The clean seam is not
erasure: "here's where we got the idea" references are permitted where they
earn their place. Publication itself remains owner-gated under the authority
grant regardless of this naming decision.

**Namespec 1.0 reaffirmation:** the reviewer's proposal to rename Tamiyo
(simic-3a17fe545d) was REJECTED — Namespec 1.0 stands unamended. Owner
rationale: the v4.1 Tamiyo-as-strategist assignment was a deliberate
promotion (owner character preference), not an oversight; and under the
clean seam the pre-pivot tactical meaning of the name is history, not a
live constraint.

## Displaced constraints

None. The project-level name was an explicitly open decision, never a
constitutional constraint; Namespec 1.0 (subsystem names and authorities)
is reaffirmed unamended.

## Options considered

- **Return to `esper` (publish as ESPER v3)** — rejected: continuity naming
  contradicts the clean-cut reset rationale (PDR-0004); the old name carries
  the failed instrument's baggage.
- **New name at publication** — rejected as default: no benefit over `simic`
  once the seam is clean; revisitable only if an external constraint (e.g. a
  trademark-level collision) forces it.
- **Rename Tamiyo within Namespec 1.0** — rejected per the gate ruling above.

## Consequences

- Phase A proceeds with `src/simic/` and no naming contingency; `pyproject`,
  `NOTICE`, `CITATION.cff` and the GitHub repository all carry the name.
- The open-decision entry is marked decided
  (`../design/programme/risks-and-open-decisions.md#271-project-level-name--decided`);
  the "name may change" caveats in `README.md` and `AGENTS.md` are removed.
- Future history/autopsy documents about the predecessors use the canonical
  framing formula above.
- **Name shelf** (owner, 2026-08-08): *weatherlight* is available if a
  future subsystem or component needs a proper noun — recorded here so it
  isn't lost.
- **Reversal trigger:** reopen only if an external naming constraint
  surfaces at the publication gate. Absent that, the decision stands
  unrevisited — naming churn is pure cost.
