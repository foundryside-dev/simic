# PDR-0002 — Design-documentation tiering: one constitutional HLD, ADRs, just-in-time LLDs, contracts-as-code

Date: 2026-08-08   Status: accepted   Author: Claude (product-owner session)
Owner sign-off: yes — strategy discussed and confirmed in-session 2026-08-08.
Related: PDR-0003 (build strategy), HLD §30 (ADR mandate), simic-aff80b1843
(tracked internal-consistency defects), simic-e84fe6737c (section-ref drift)

## Context
HLD v4.1 is a 4,718-line monolith about to absorb implementation-era churn, with
43 open `hld-review` items amending it. The owner asked whether each of the
fourteen subsystems should get its own HLD before Python work starts.

## Options considered
1. **Fourteen per-subsystem HLDs** — pro: local ownership, smaller files; con:
   the load-bearing content (newsroom routing, 44 invariants, warrant chain,
   blinding) is cross-cutting — every seam gets described from both ends, every
   invariant fragments, and fourteen documents drift independently with no single
   place where "the design" lives. Rejected.
2. **Single monolith absorbs everything** — pro: one source of truth; con: mixes
   constitutional material (stable, ADR-gated) with elaboration that must evolve;
   every edit is high-risk (internal inconsistency is already a tracked defect);
   implementation detail (schemas, APIs) doesn't belong in an HLD. Rejected.
3. **Four-tier architecture (chosen)** — elaboration flows down, authority flows
   up.

## The call
- **Tier 0 — constitution:** `docs/concept/simic.md` stays the single canonical
  document for everything inter-subsystem. Changes only via ADR (per §30).
- **Tier 1 — ADRs** (`docs/adr/`): absorb design change. Decision-gate rulings
  land as the first content ADRs; Phase A opens with the Namespec 1.0 ADR.
- **Tier 2 — per-subsystem LLDs** (`docs/design/<subsystem>.md`): written
  just-in-time in the phase that builds each subsystem, never all up front. Each
  opens with a standard header: verb, authorities, forbidden knowledge (§8,
  Appendix B), bound invariants, contracts produced/consumed. LLDs elaborate,
  never override; conflicts resolve upward (the LLD is wrong, or an ADR changes
  the HLD). Location `docs/design/` is a reversible default — design docs should
  not move when code refactors.
- **Tier 3 — contracts as code:** from Phase A, Leyline schemas are the
  executable truth for every seam; documents cite contract names rather than
  restating field lists.
- **Citation convention:** derived documents cite invariants as `INV-nn` and
  contracts by name — never by section number. Grounded in two observed
  section-drift failures (v2.0→v4.1 renumbering broke the skill-pack prompts and
  AGENTS.md) plus one in-session error (§18.1 cited for what is invariant 5).
  No derived document restates an invariant; it cites it.

## Rationale
The design's own principles (single canonical hash, one source of truth, Leyline
imports nothing) describe the right documentation shape. §30 already mandates the
ADR mechanism; the §24 stub ladder and Phases A–K make just-in-time LLDs natural;
stable IDs make the citation graph survive restructures and become lintable.

## Reversal trigger
Revisit the tiering if: LLDs start restating rather than citing the HLD; two LLDs
describe the same seam differently; or constitutional ADRs land faster than
~monthly (the "constitution" is then holding material that belongs in a lower
tier).
