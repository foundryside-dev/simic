<!-- hld: simic HLD v4.1 chapter (ADR-0001 decomposition) · index: ../00-INDEX.md -->
[← HLD index](../00-INDEX.md)

<!-- hld: source: v4.1 monolith lines 2292–2321 -->
### 13.12 Wrenn — Host and Growth Physiology

#### Responsibilities

- implement the host network and insertion regions;
- publish immutable `RegionContract` records for each insertion region;
- provide reversible growth slots;
- expose ablated and active forward paths;
- isolate gradients according to declared trainability;
- install verified executable artefacts;
- manage alpha blending and lifecycle state;
- support bounded nursery maturation;
- serialize complete host and slot state for Tolaria;
- enforce lifecycle transition authority and warrants;
- and recycle slots after removal.

#### Invariants

- Wrenn does not decide whether a growth is good.
- Wrenn owns no preferred stock blueprint or reference-seed catalogue.
- Region contracts describe attachment legality and tensor shape, not a suggested phenotype.
- It will not raise influence without a valid Isperia admission warrant.
- The embodied canonical semantic hash matches Isperia’s selected hash and Jin-Gitaxias’s tested hash.
- Removal uses gradual blend-out except for declared emergency containment (Tolaria detects and contains; Isperia adjudicates the containment back to the admitting warrant — INV-28, ADR-0010).
- Occupant-specific economy state resets on slot recycling.

#### Smell

> If Wrenn ranks candidates, calculates admission utility, or regains an internal Norm/Attention/Conv catalogue, physiology has acquired opinions and design authority.
