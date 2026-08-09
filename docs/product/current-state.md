# Current State — Simic        Checkpoint: 2026-08-09 (session 12, second)

## The bet right now
Design hardening — the hld-review burn-down (31 → 0 by 2026-08-31, pacing
signal; ~1.5 closures/working day). The **worked cost model is landed**
(ADR-0014, pulled forward from wave:5 — PDR-0026): the north-star's K and
N are now fixed (K = 1.5, N = 256 pools = 32 trajectories), the 40-HER
restructure trigger is armed, and the model is provisional until §27.5
(QA horizon) closes. Next band: **wave:2-momir** (8 items). The second Now
bet, the ADR-0002 information-management regime (simic-357c92664c),
remains unstarted — the constitution's shapes keep moving (ADR-0014 landed
today), so the plainweave seeding gate needs owner presence soon.

## In flight
- Nothing claimed. Wave:2-momir heads with simic-0e6445d894 (Momir critic
  ADR, unblocks simic-c90afdb156); simic-0bf2c40dec → simic-38a07fad39
  (§9 contract shapes) stays the cross-band leverage play.
- **Publish queue (owner-gated):** local main is ahead of origin by **9
  commits** — the design-wiki Astro/Starlight design (692014f), the kernel
  demo spec **now final** (revs 1–5, panel round 3 verified, ends f2ece1d;
  recorded in PDR-0028), and this session's cost-model landing + plugin
  config + checkpoints. Working tree clean. Publish = PR branch + merge,
  never direct push.
- Plugin roster: axiom-experiment-formalisation v0.2.1 installed at
  project scope (PDR-0027) — **loads from the next session**;
  contract-engineering confirmed current (post-ship fixes included).
- simic-b67434134e: cryptography bump still blocked upstream (PDR-0023).

## Open questions / blocked-on-owner
- **Publish the queue?** Five design commits + this session are local-only.
- Carried: yzmir-training-state applied prompt
  (`commissioning/yzmir-training-state-engineering-updated-prompt.md`)
  still awaits owner relay; the pack is confirmed absent upstream as of
  today's marketplace fetch — re-commissioning fresh (PDR-0012 reversal
  path) may now beat relaying.
- Kernel demo (PDR-0029): **spec LOCKED rev 6, implementation GO**
  (owner, parallel session, 98083fd). Purpose owner-stated: the
  proof-of-concept — "how do you know it works" pointer; maths is proved,
  risk is engineering. Now a Next-band bet; sequencing vs burn-down/Phase A
  is the open call. Never citable as §28 evidence.
- Wiki replatform implementation (PDR-0028): approved design, untracked as
  work. Enter into filigree when the owner wants it scheduled. Until
  built, the mkdocs build path stays live.

## Last checkpoint did
- PDR-0026: cost model pulled forward, dispatched
  (counterfactual-statistician), accepted, landed (ADR-0014 + chapter +
  committed pre-registration); simic-642c2c1823 closed; owner decided D1
  (pre-registered 1.5× inferiority margin) and D2 (rate primary, cost
  descriptive) in-session.
- PDR-0027: experiment-formalisation pack installed (project scope);
  contract-engineering verified current.
- PDR-0028: parallel-session artifacts recorded (wiki replatform design,
  kernel demo spec).
- Metrics: north-star K/N slots filled; burn-down 31/23.

## Next session, start here
Claim simic-0e6445d894 to open wave:2-momir. Alternatively run the
plainweave seeding gate (simic-357c92664c) with the owner present —
ADR-0014 just added more named definitions worth locking. Note the
experiment-formalisation skills are loadable for the first time next
session; the ADR-0002 regime work is their natural first consumer.
