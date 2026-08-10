# ADR-0008 — Adopt Namespec 2.0: the Phyrexian industrial compleation constitution
<!-- adr-meta:begin — append-only; rules: README.md#metadata-and-immutability -->

Date: 2026-08-09 · Status: accepted
Deciders: John (owner; directive of 2026-08-09, prompts/namespec.md) · Tracker: simic-d8369760b9

Amends: —
Amended-by: —
Supersedes: —
Superseded-by: —
<!-- adr-meta:end — everything below is IMMUTABLE body (ADR-0017) -->

## Context

Namespec 1.0 was locked in `../design/02-constitution.md#57-change-control` and
reaffirmed unamended in ADR-0003 after the peer review challenged the
Tamiyo-as-strategist assignment (simic-3a17fe545d, ruled WONTFIX 2026-08-08).
On 2026-08-09 the owner directed a final consistency pass over the conceptual
design and issued a locked replacement naming constitution — **Namespec 2.0**
— superseding Namespec 1.0 in its entirety, with no legacy aliases. The
architecture remains HLD v4.1: every authority boundary, contract schema,
lifecycle rule, determinism policy, scaffold withdrawal gate, and the 45
INV-nn invariants are unchanged in content. Only the subsystem codenames,
their narrative grammar, and the thematic framing change.

The change also settles, on new terms, the ambiguity the peer review raised:
Tamiyo leaves the strategic role entirely. Strategy goes to a name with no
pre-pivot history (Ugin), and Tamiyo moves to the witness role — the one that
matches the character (the Moon Sage who records histories without steering
them) — replacing Oona, whose secret-hoarding Fae-queen character was always
a poor fit for an agent whose verb is *reveals*.

## Decision

Adopt Namespec 2.0 as the locked naming constitution. The concordance:

| Role | Namespec 1.0 | Namespec 2.0 | Verb / context |
|---|---|---|---|
| Constitutional infrastructure | Leyline | **Leyline** (retained) | *under/through Leyline* |
| Training & execution substrate | Tolaria | **Tolaria** (retained) | *trained/executed/tested in Tolaria* |
| Historical infrastructure | Sarpadia | **Urborg** | *recorded in/retrieved from Urborg* |
| Strategic agency | Tamiyo | **Ugin** | *plans* |
| Tactical commissioning | Narset | **Aurelia** | *commissions and acts* |
| Observation | Nissa | **Nissa** (retained) | *observes and reports* |
| Synthesis — design | Momir | **Momir** (retained) | *designs* |
| Synthesis — conformance | Elesh | **Elesh** (retained) | *conforms* |
| Synthesis — compilation | Tezzeret | **Urabrask** | *compiles* |
| Assurance & evidence | Urabrask | **Jin-Gitaxias** | *tests* |
| Adjudication | Augustin | **Isperia** | *judges* |
| Embodiment & physiology | Kasmina | **Wrenn** | *embodies* |
| Maintenance & destruction | Emrakul | **Emrakul** (retained) | *destroys* |
| Witness & revelation | Oona | **Tamiyo** | *reveals* |

The canonical sentence becomes:

> **Under Leyline, Ugin plans, Aurelia commissions and acts, Nissa observes,
> Momir designs, Elesh conforms, Urabrask compiles, Jin-Gitaxias tests in
> Tolaria, Isperia judges, Wrenn embodies, Emrakul destroys, and Tamiyo
> reveals; every precedent is kept in Urborg.**

The thematic framing is upgraded from decorative lore to a **warning system**:
the architecture is a Simic engine run under Phyrexian industrial discipline.
Momir (bio-foundry) → Elesh (standardisation) → Urabrask (manufacturing) →
Jin-Gitaxias (quality control) form the **Phyrexian industrial synthesis
core** — a single compleation assembly line inside the architecture — and
the non-Phyrexian authorities (Ugin, Aurelia, Isperia, Tamiyo, Nissa, Wrenn)
form the **governance cage** that contains it. The tension between core and
cage is the architecture's central narrative, and it makes authority
violations audible: a Phyrexian name showing up on a governance decision, or
a cage name inside the assembly line, is a sentence that sounds wrong before
it is a diff that reads wrong.

Urabrask's chapter must state his **dual compilation mode** explicitly:
on-demand manufacturing (compile the canonical specification under deadline
and budget when Aurelia commissions a growth) and background industrial R&D
(idle-cycle compilation of canonical backlogs and discovery of production
optimisations, reported as versioned compiler improvements). Neither mode may
invent topology (Momir's domain) or alter semantic meaning (Elesh's
canonical identity; INV-21). This is framing made explicit, not new
authority.

The agent/infrastructure grammar is preserved: agents carry verbs (Ugin,
Aurelia, Nissa, Momir, Elesh, Urabrask, Jin-Gitaxias, Isperia, Wrenn,
Emrakul, Tamiyo); infrastructure carries prepositions (Leyline, Tolaria,
Urborg). The Python package for Jin-Gitaxias is `jin_gitaxias`; document
files and anchors use `jin-gitaxias`.

**Historical-interpretation rule.** Two names appear in both namespecs with
different referents: *Urabrask* (1.0: QA/testing → 2.0: compilation) and
*Tamiyo* (1.0: strategic planning → 2.0: witness/revelation). Any document
whose content predates this ADR — the archived v4.1 monolith, the
`docs/concept/reviews/` records, the bodies of ADR-0001..0007, and PDR
bodies through 0019 — uses Namespec 1.0 names where it names domains at all,
and is read through the
concordance above. Those records are not rewritten (Urborg discipline:
corrections create new records; INV-36). ADR-0001..0007 receive a one-line
namespec banner pointing here; nothing else in them changes.

## Displaced constraints

- **Namespec 1.0 lock** (`../design/02-constitution.md#57-change-control`):
  displaced in its entirety by the Namespec 2.0 locked list above. This is
  exactly the amendment path §5.7 prescribes — a codename change through an
  ADR.
- **ADR-0003's Namespec 1.0 reaffirmation**: superseded in part. The
  project-level name (Simic, clean seam) and everything else in ADR-0003
  stand; only the "Namespec 1.0 stands unamended" ruling is displaced. The
  underlying gate ruling (Tamiyo does not return to the tactical role) is
  still honoured: under 2.0 the tactical role is Aurelia, and Tamiyo is the
  witness, not the tactician.
- **No INV-nn is amended in content.** All 45 invariants are re-worded only
  where they name an agent (e.g. INV-17 dual provider blindness now names
  Jin-Gitaxias and Isperia; INV-26/27 warrants now name Isperia and Wrenn;
  INV-35 Oona isolation becomes Tamiyo isolation). The obligations,
  thresholds and failure semantics are character-for-character equivalent
  modulo the concordance.

## Options considered

- **Keep Namespec 1.0** — rejected by owner directive. Beyond preference:
  1.0's thematic layer was inert (names as mnemonics only), and two of its
  castings fought their characters (Oona the secret-keeper as the revealer;
  Tamiyo the recorder as the strategist). 2.0 makes the mythology
  load-bearing — the synthesis-core/cage split encodes the QA/judgement and
  designer/compiler separations the invariants enforce.
- **Rename only the contested pair (Tamiyo/Oona)** — rejected: a partial
  amendment still breaks the lock and still needs the concordance machinery,
  but buys no coherent frame; the industrial-core narrative requires the
  Urabrask/Jin-Gitaxias and Tezzeret→Urabrask moves.
- **Choose 2.0 names with zero overlap against 1.0** (avoid reusing Urabrask
  and Tamiyo) — rejected: it would trade permanent character-role mismatch
  for a transitional reading hazard. The hazard is bounded — it lives only in
  pre-pivot records, which are all behind the clean seam (ADR-0003) — and the
  historical-interpretation rule plus banners pay it down once.

## Consequences

- **Cascade (this ADR's implementation):** `docs/design/02-constitution.md`
  rewritten (Namespec 2.0, thematic constitution, INV renames, Appendix B);
  all design chapters, `domains/` files (renamed, collision-safe), appendices
  (newsroom, glossary, sentence tests, smells) updated; `AGENTS.md`,
  `ARCHITECTURE.md`, `README.md` updated; `docs/design/assets/model.dsl` and
  the mermaid sources renamed and re-rendered; product workspace updated
  (PDR-0018); site pages and wiki rebuilt; open tracker issues retitled.
- **Phase A lands the 2.0 package layout:** `src/simic/{leyline, tolaria,
  urborg, ugin, aurelia, nissa, momir, elesh, urabrask, jin_gitaxias,
  isperia, wrenn, emrakul, tamiyo}` and the corresponding test directories.
  No code exists yet, so the rename costs nothing on the code side — this is
  the last cheap moment to make the change, which is why it happens now.
- **Future telemetry, test and audit names** use 2.0 names from birth.
- **Reading pre-pivot records now requires the concordance** for Urabrask
  and Tamiyo; the banners on ADR-0001..0007 and the clean seam (ADR-0003)
  bound the exposure.
- **Reversal trigger:** owner ruling only, before Phase A writes package
  names to disk; after Phase A, a reversal is a new ADR with a migration
  plan. Absent that, the decision stands unrevisited — naming churn is pure
  cost (ADR-0003's discipline applies to this ADR too).
