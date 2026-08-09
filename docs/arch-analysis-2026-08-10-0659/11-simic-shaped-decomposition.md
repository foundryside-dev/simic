# 11 — Simic-Shaped Decomposition of the Kernel Demo

**Target:** `experiments/kernel_demo.py` (4,066 LOC), `experiments/kernel_demo_plots.py` (151 LOC)
**Date:** 2026-08-10
**Evidence base:** `02-subsystem-catalog.md` (9 subsystem entries), `00-coordination.md` (coordinator adjudications)
**Authority for domain semantics:** `docs/design/02-constitution.md`, `docs/design/05-leyline-contracts.md`, `docs/design/07-counterfactual-engine.md`

---

## 0. What this document is, and what it is not

> **This is a paper decomposition. It is not a proposal to refactor the demo.**
>
> The single-file layout is a **locked spec decision** (rev 6.1,
> `docs/superpowers/specs/2026-08-09-kernel-demo-design.md` line 4; rationale at
> line 574: *"a reader can open the one file and follow the whole loop
> top-to-bottom"*). Nothing here should be executed as a refactor. The demo stays
> one file.
>
> What we extract is the **boundary schema**. The value of drawing the domain
> lines on paper is that the information flows become visible, and where a flow
> crosses a line, a record must already exist to carry it. Those records are the
> Leyline contract shapes, discovered from a system that actually runs rather
> than invented from the HLD.

A second framing constraint, from the demo itself. The module docstring
(`kernel_demo.py:3–7`) states:

> *"Deliberately NOT Simic: the seed menu is fixed and human-authored, which is
> exactly what Simic proper rejects (generation from live host state). This demo
> proves the substrate loop and the counterfactual-fan supervision economics, not
> generative morphogenesis."*

Divergences from Simic that follow from that sentence are **by design**, and are
reported below as design boundaries, not gaps. Only divergences the demo does not
claim are reported as findings.

**A third framing point, and it does real work: an absent domain is not a blank.**
Where an authority is missing, the demo still has a **socket** — the position that
authority would occupy, with a real type signature on each side. §A.2 documents
each socket, its inbound record and its outbound record, because that is exactly
where the contract lives. Two results from that pass are worth reading even if
nothing else here is: **Momir's output contract is already complete and tested**
(§A.2.1), and **Urabrask's socket is not missing but explicitly welded shut, with
the reason recorded** (§A.2.5).

---

## A. Domain presence table

Verified against the catalog rather than assumed. **Two corrections to the
briefing list are recorded below the table.**

| Domain | Presence | Evidence | If absent/partial: what the demo cannot test |
|---|---|---|---|
| **Tolaria** — trains, executes, snapshots, branches, replays | **Present** | `train_one_epoch` (:1058), `_run_span` (:1236) as the *single* implementation shared by base and arms (:1243–1245), `run_base` (:1268), `run_arm` (:1285), `take_snapshot` (:1155), `run_replay` (:3925), `enable_class1` (:917) | — |
| **Urborg** — append-only history, retains failures | **Present** | `Store` (:1579), append-only JSONL shards, `RECORD_KINDS` includes `void_event` (:1426), diverged arms retained as results (:1341–1345), `--void-preregistration` appends rather than deletes (:3437–3461) | — |
| **Nissa** — observes and reports, blind by construction | **Present** | `TelemetryRecord` (:357), field list :358–369 carries **no** seed/arm/pathology/provenance field; `attach_stat_hooks` / `_saturation_hook` (:614, :620); `confusion_stats` (:424) | — |
| **Wrenn** — embodies, slots, maturation, blending | **Present** | `Slot` (:785), `Stage` 6-state enum (:769), `germinate` (:1167), α/β cosine ramps (:779, :853), `trust_region_loss` (:822), `append_seed_group` (:892) | — |
| **Jin-Gitaxias** — tests, certifies evidence | **Present** | `run_selftest` 10-step battery (:2061), gates 1–8 (:2547–2827), `GateResult` (:2502), `run_preflight` (:2919), `run_refan` (:2418) | — |
| **Leyline** — contracts, schemas, versions, resolver | **Partial** | Present: `FanRecord` (:1433), `SCHEMA_VERSION` (:55), `make_fan_record` as sole validating constructor (:1473), three closed vocabularies (:1426–1428) whitelisted at :1501–1506, fail-closed `decode_record` (:1567). Absent: dependency direction (INV-02) is untestable in one file; the deployment resolver exists but is implemented **twice** (:1754 vs :3562–3573) | Cannot demonstrate INV-02 (contracts import nothing from subsystems) — there is no package boundary to lint. Cannot demonstrate INV-11 (no covert request channel) — there is no request to resolve. |
| **Aurelia** — commissions, tactical timing | **Partial** | The `Policy` WHEN head (`now_head`, :1720) *is* tactical intervention timing; `decide_live`'s window guard (:1762–1765) is the operational constraint. Absent: no `GrowthIntent` record, no insertion-region choice (site fixed at :575/:602), no `StrategicEnvelope` to act under | Cannot test INV-09 (assignment-brief boundary) or INV-12 (no hidden-state coupling): there is no designer to brief and no channel to smuggle a conclusion through. |
| **Isperia** — judges, no-op comparison, warrants | **Partial** | Present: measured no-op (:1381, :1390), no-op utility exactly zero (:3587), `verdict()` five pre-registered booleans (:3313–3325) with all thresholds hash-frozen. Absent: no `admission_warrant` — `germinate` (:1167) requires no token; no tail-risk veto; `verdict()` never ANDs its five booleans (:3319–3325) | Cannot test INV-26 (admission warrant), INV-45 (lexicographic admission — the five booleans are peers, so a veto stage has no representation), INV-33 (hysteresis band). |
| **Tamiyo** — reveals, must not steer | **Partial** | Isolation is **real**: `kernel_demo_plots.py` declares no `@semantic`/`semantic_const`, has no repo caller, imports one-way (catalog :877, :890). But revelation work also lives *inside* the execution modules — `run_report` (:3829) and the print-tables inside `run_eval` | Cannot test INV-35 at the boundary that matters: the isolated witness is the *optional* one; the load-bearing tables are fused into the judge. |
| **Momir** — designs candidates | **Absent** *(by design)* — **socket §A.2.1** | Docstring :3–6 states this explicitly. `SEED_NAMES` (:634) is a fixed 4-tuple `semantic_const`; `build_seed` (:721) is a name→class dispatch over a hard-coded menu | No `RawGrowthGraph`, no `ProposalBatchRequest`, no `BootstrapAncestryContext`. Cannot test whether generation-from-live-state beats a fixed menu — **which is the entire Simic thesis**. Cannot test INV-13 (bootstrap provenance) or "Momir must not approve its own work". |
| **Elesh** — conforms, canonicalises | **Partial** — *correction below; socket §A.2.2* | The conformance **contract** exists and is enforced: `SeedDelta` (:638) fixes `forward(h) = gain * f(h)`; all four seeds take `channels: int` and map `[B,64,8,8]→[B,64,8,8]`; `build_seed` raises on unknown name (:729); `tau_init` (:735) drives four structurally dissimilar seeds to a measured `rms_ratio = 0.0500 = cfg.tau` despite `rms(f0)` spanning orders of magnitude. What is missing is a conformance **step** — nothing arrives unconformed | Cannot test INV-19 (raw-to-canonical traceability) or INV-21 (semantic preservation): there is no raw form to trace from. "Elesh must not judge utility" is untestable because there is no rejection path. |
| **Urabrask** — compiles | **Absent** *(by design)* — **socket §A.2.5, explicitly welded shut** | Nothing compiles; seeds go from `nn.Module` straight to execution. `FORBIDDEN_RELAXATIONS` (:900) explicitly bans `torch.compile` as voiding the Class-1 claim | No `ExecutableGrowthArtifact`. Cannot test INV-21 (compiler semantic preservation) or the "an artefact is not trusted merely because compilation succeeded" discipline. |
| **Ugin** — plans, allocates, budgets | **Partial, and the weakest of the partials** — *socket §A.2.3, which governs* | The socket is `draw_schedule` (:2307) + the frozen `cfg.window`: a seeded draw within declared bounds. **Not** `FROZEN_FIELDS` as a whole — of its 34 fields only ~6 are grant-shaped (`window`, `horizon`, `n_collect`, `fans_per_episode`, stage durations); nine are learning rates and batch sizes, and the largest group is gate/verdict thresholds, which `StrategicEnvelope` deliberately does **not** inline (it carries `admissibility_policy_id` instead) | Cannot test INV-29 (Ugin never issues local transitions) or INV-23 (budget declared, spend reported): budgets are constants, not grants, and nothing reports spend against them. |
| **Emrakul** — destroys, sedates, decays, lyses | **Absent** — **socket §A.2.4** | `Stage` (:769) terminates at `FOSSILIZED`; there is no descent path, no sedation, no lysis anywhere in the file | Cannot test INV-25 (reversible influence), INV-27 (maintenance warrant), INV-30 (grace-period protection). **The demo measures admission economics only, never retention economics** — so INV-33's asymmetric admit/retain thresholds have no exercise at all. |

### Corrections to the briefing list

**1. Elesh is `partial`, not absent.** The briefing placed Elesh with Momir and
Urabrask as having no analogue. That understates what is there. The four-seed menu
is not merely *fixed* — it is *conformed*, and the conformance is measured. The
uniform `[B,64,8,8]` shape contract, the exactly-zero delta at construction, and
τ-normalisation landing all four seeds on a common scale (0.0500 measured, against
`rms(f0)` values spanning 0.9215 → 0.04998) is precisely Elesh's discipline:
"makes designs structurally legal and canonical … may reject malformed structure …
must not judge task utility" (`02-constitution.md`, Appendix B). Every clause holds
in the demo. What is absent is the *step*, because nothing arrives unconformed —
the menu is conformed by authorship. The distinction matters for Phase A: the
demo demonstrates that a delta contract can be made uniform and *verified* (gate 5,
:2687, checks `rms_ratio` at blend entry against a band), which is exactly the
evidence Elesh's contract will need.

**2. Ugin is `partial`, not absent — but on narrower evidence than this section
first claimed.** An earlier draft rested the case on `FROZEN_FIELDS` as a whole being
envelope-shaped. **The contract audit refuted that and is right:** of its 34 fields
only about six are grant-shaped; nine are learning rates and batch sizes, and the
largest group is gate and verdict thresholds — which `StrategicEnvelope` deliberately
does *not* inline, carrying `admissibility_policy_id` instead
(`05-leyline-contracts.md#91-strategicenvelope`). A block that is mostly thresholds
and optimiser constants is a pre-registration record, not an envelope.

**The verdict survives on the narrower evidence in §A.2.3**, which governs: the
socket is `draw_schedule` (:2307) plus the frozen `cfg.window` — a *bounded, seeded
allocation of intervention opportunities*, which is genuinely grant-shaped, plus the
handful of `FROZEN_FIELDS` entries that are real budgets (`horizon`, `n_collect`,
`fans_per_episode`).

> **Ugin is the weaker of the two partials, and a Phase-A reader should not
> over-credit it.** `FROZEN_FIELDS` is a **static config block, not a per-run issued
> grant**: the envelope's *shape* is present while its *issuance* — the thing that
> makes an envelope an envelope rather than a constant — is absent along with the
> issuer. Elesh's partial is materially stronger, because `tau_init` actually *runs*
> and its effect is measured (§A.2.2). The sharp end of Ugin's weakness is **INV-23**:
> budgets are declared and **nothing reports spend against them**. See §A.2.3 for why
> the non-varying envelope is not a cosmetic gap.

The rest of the briefing list is confirmed: Tolaria, Urborg, Nissa, Wrenn and
Jin-Gitaxias are present; Leyline, Aurelia, Isperia and Tamiyo are partial; Momir,
Urabrask and Emrakul have no implementation. **They are not, however, featureless
holes — see §A.2.**

---

## A.2 Sockets: where the absent authorities would sit

An absent domain is not a blank. It leaves a **socket** — a position in the demo
where that authority would sit, with a real type signature on each side. The socket,
its inbound record and its outbound record are precisely where the contract lives,
and a socket is often *more* legible than a present-but-tangled domain, because
nothing has grown over it.

Treatment below is proportionate to how legible each socket actually is. **Momir's
is the sharpest by a wide margin** and gets the most detail.

---

### A.2.1 Momir — the socket whose output contract is already finished

**Position.** `build_seed(name: str, channels: int, init_seed: int) -> SeedDelta`
(:721) occupies exactly the position where generation-from-live-host-state would go.
It is a degenerate Momir: a four-entry dict lookup (:722–727) that raises on an
unknown name (:729) and constructs under `rng_scope` (:730).

#### The outbound side is complete, specified and executable

This is the most reusable artifact the socket analysis produces. `SeedDelta` (:638)
is an abstract base that fixes the entire output contract:

```python
class SeedDelta(nn.Module):
    # gain is born 0.0 (exact zero delta before tau_init) and is the
    # ONLY parameter carrying tau.
    def __init__(self):     self.gain = nn.Parameter(torch.zeros(()))   # :643
    def f(self, h):         raise NotImplementedError                   # :645–646
    def forward(self, h):   return self.gain * self.f(h)                # :648–649
```

Everything a generator must produce is pinned:

| Contract clause | Where | Verification |
|---|---|---|
| Constructor takes `channels: int` and nothing else | :654, :663, :687, :704 | All four subclasses conform |
| Shape `[B,64,8,8] → [B,64,8,8]` | `f` implementations | **Verified by execution** across all four seeds (explorer 3) |
| `forward` is fixed by the base — a subclass implements only `f` | :648–649 | Structural: `forward` is not overridable in practice |
| Delta is **exactly zero** at construction | `gain = zeros(())` :643 | Verified: all four are zero-delta before `tau_init` |
| `gain` is the sole carrier of τ | :639–640 | `split_decay_groups` :760 keys on `endswith("gain")` |

**The demo therefore contains a complete, tested output contract for a component
that does not exist yet.** Momir's `RawGrowthGraph` will carry far more
(`raw_graph_ir`, `parent_lineages[]`, `latent_code`, `generation_spend`), but the
*interface at the socket's downstream edge* — what Wrenn must be able to embody — is
already specified and already exercised by four independent implementations.

#### The inbound side is deliberately thin, and the thinness is the finding

`(name: str, channels: int, init_seed: int)`. Field by field:

| Field | What it really is | Simic analogue |
|---|---|---|
| `name: str` | A **selection from a menu**, not a commission | This is where `GrowthRequest` would go — and see below |
| `channels: int` | A degenerate `input_output_contract`, flattened to one integer | `GrowthRequest.input_output_contract` + `region_contract_version` (cf. §C.6) |
| `init_seed: int` | The only field that survives into Simic essentially unchanged | `TrainingRunSpec.random_seed_manifest` |

#### What the socket would need to grow to satisfy INV-09 — the cleanest statement in this document

Contrast `name: str` against the assignment-brief boundary
(`02-constitution.md#55-the-evidence-routing-rule`, INV-09). `GrowthIntent` permits
scope and operational constraints only — `insertion_region_id`,
`requested_resource_class`, `maturity_mode`, `assurance_class`, `urgency_class`,
`tactical_deadline`, `reason_code`. It **explicitly forbids**
(`05-leyline-contracts.md#93-growthintent`):

```text
preferred_topology_family      preferred_operator        rank_hint
width_hint                     deficit_type              recommended_mechanism
suggested_ancestor             expected_internal_structure
```

**`name: str` is squarely on that forbidden list. It is `preferred_operator`
(`05-leyline-contracts.md:102`) in its purest possible form** — a literal operator
name, chosen upstream, handed to the constructor. The demo's Momir socket is fed by
exactly the field Simic's constitution declares schema-invalid. *Independently
verified at that line by the coordinator; this is a direct identification, not an
analogy.*

That is not a criticism of the demo — it is the docstring's own claim (:3–6) made
mechanical. But it is the sharpest available answer to "what changes when Momir
arrives": **the inbound edge inverts.** Today the socket receives a conclusion
(*which* operator). Under INV-09 it must receive only an assignment (*where*, *how
big*, *how urgent*, *how assured*) and the evidence arrives on a separate channel
direct from Nissa. The code-review question from the constitution applies verbatim:
*does this field specify the assignment, or does it smuggle a conclusion?* Here,
demonstrably the latter.

#### Two authorities are collapsed into this one socket

The `name` handed to `build_seed` comes from the policy's WHICH head
(`seed_head: Linear(d, 4)`, :1721) via `germinate` (:1174). In Simic, *designing*
candidates is Momir and *selecting* among certified ones is Isperia adjudicating
blind evidence. **With a fixed menu those collapse**: there is nothing to design, so
choosing *is* designing.

The consequence for Phase A is structural, not cosmetic. Filling the Momir socket
**splits** them — Momir generates a pool, Jin-Gitaxias certifies it blind, Isperia
selects — and **the WHICH head does not survive that split intact**. A
`Linear(d, 4)` over a fixed `SEED_NAMES` tuple has no meaning once the candidate set
is generated per-request and varies in size. What survives is the WHEN head; what
must be rebuilt is everything downstream of it.

#### What flows "that way" today, and what would flow

| Direction | Today | Under Simic |
|---|---|---|
| **Inbound** | `name` (a chosen operator), `channels` (a literal 64), `init_seed` | `GrowthRequest` (scope, budgets, `input_output_contract`, `grammar_profile_id`, `assurance_class`, `resolver_version`) + `TelemetryEnvelope` **direct from Nissa**, never via the commissioner + optional `BootstrapAncestryContext` |
| **Outbound** | A live `SeedDelta` instance, handed straight to `Slot.seed` (:1183) | `RawGrowthGraph` (not executable, not trusted) → Elesh → `CanonicalGrowthSpec` → Urabrask → `ExecutableGrowthArtifact` → Jin-Gitaxias |
| **Count** | Exactly one, chosen before the call | A pool — `ProposalBatchRequest.candidate_count`, with the generator invariant to batch representation (INV-11) |

---

### A.2.2 Elesh — the socket is occupied, verified, and unnamed

**Your hypothesis holds, and it is a significant finding.** `tau_init` (:735) is
canonicalisation in function if not in name:

```python
f0     = seed.f(host_feats)
rms_h  = float(host_feats.pow(2).mean().sqrt())
rms_f0 = float(f0.pow(2).mean().sqrt())
g      = cfg.tau * rms_h / max(rms_f0, cfg.tau_eps)     # :745
seed.gain.fill_(g)                                       # :746
```

It takes structurally dissimilar candidates and places them on a **common entry
scale**: all four seeds land at a measured `rms_ratio = 0.0500 = cfg.tau` exactly,
despite `rms(f0)` spanning 0.9215 / 0.3307 / 0.1187 / 0.04998 — a ~18× spread
collapsed to a single value (explorer 3, verified by execution). Without it, "which
seed wins" would partly measure which seed happens to enter loudest.

**So conformance exists in the demo without a domain to own it.** That is worth
stating plainly for Phase A: the demo demonstrates that unlike candidates can be
made comparable at a boundary, and that the normalisation can be *verified*
downstream — gate 5 (:2687) checks mean `rms_ratio_blend_entry` against a
`[tau/band, tau*band]` band and treats **no measurement as an explicit failure, not
a pass** (:2702–2703).

**But the socket is only half-occupied.** Elesh's `CanonicalGrowthSpec`
(`05-leyline-contracts.md#98-canonicalgrowthspec`) carries `canonical_graph_ir`,
`trainability_mask`, `zero_influence_proof`, `structural_pruning_report`,
`verification_report`, `canonical_semantic_hash`. `tau_init` produces **one float**.

| Elesh's job | Demo status |
|---|---|
| **Magnitude** canonicalisation | **Occupied** — `tau_init` (:735), verified by gate 5 (:2687) |
| **Structural** canonicalisation | **Empty** — nothing rewrites, prunes or canonicalises a graph; there is no graph |
| `zero_influence_proof` | **Analogue present, by construction rather than proof** — `gain = zeros(())` (:643) makes the delta exactly zero at construction. Established structurally, not proved about an arbitrary input |
| `canonical_semantic_hash` | **Empty** — the demo hashes *runs and source text* (`config_hash`, `state_hash`, `fan_identity`), never a *design* (see §D.10) |

Socket shape, precisely: `build_seed` output → **[`tau_init` + gate 5]** →
`Slot.seed` (:1181–1183). Occupied on the magnitude axis, verified, and belonging to
no named authority.

---

### A.2.3 Ugin — the randomised allocator the programme is asking for, already built

**Position.** `draw_schedule` (:2307) plus the frozen `cfg.window`:

```python
lo, hi = cfg.window
g    = make_generator(derive(episode_seed, label))
perm = torch.randperm(hi - lo + 1, generator=g)[: cfg.fans_per_episode]   # :2313
```

Uniform without replacement over an inclusive **declared window**, seed-derived,
fully deterministic, with `label` separating independent draws over the same
distribution (`"schedule"` for collection, `"evalgrid"` for the frozen eval grid).

**A resemblance to filigree simic-76fc6e6618, and it is only a resemblance — stated
carefully, because an earlier draft over-claimed here.** The issue (P1, `hld-review`,
wave:3-narset) asks for:

> *"A fixed schedule, or better, randomised within declared bounds on a seed… Build
> the random allocator now and keep it forever as the null."*

`draw_schedule` has that **shape**: a deterministic seeded random draw within
declared bounds. It does **not** have that **role**. It schedules the *harness's*
branch points — all three call sites are collection, refan and the eval grid — and
its output never reaches `Policy`, whose input width is `TELEMETRY_DIM = 20`
telemetry features. It allocates nothing to any actor.

**So the issue's allocator is not built.** What the demo contains is a
deterministic seeded draw of the same shape in a different role — reusable as a
*pattern*, not as the artifact. (An earlier draft of this section said the demo had
"already built" it; that was an over-read of the resemblance, corrected here.)

**But it instantiates the exact failure mode the issue warns against.** The issue's
argument is that a *non-varying* allocator teaches the actor nothing, because the
envelope never shifts and so the actor never learns to read it. In the demo:

- `cfg.window` is a **frozen field** (`FROZEN_FIELDS`, :188–223). The *draw within*
  the window varies per episode; the **envelope itself never varies at all.**
- The `Policy` (:1708) consumes a `TELEMETRY_DIM = 20` telemetry vector (:351) and
  nothing else. **There is no envelope input — not a constant one, none.** There is
  no slot in the feature space for an allocation to occupy.

So the demo is a live demonstration of the issue's premise: an actor trained under
an invariant envelope has no representation for envelope-conditional behaviour, and
here it provably cannot acquire one, because the input width admits no such feature.

That sharpens the issue's remedy. It is not only *"make the stub vary"* — it is
*"vary it **and** give the actor a field to read it in"*, and the demo shows why the
second half is not optional. Worth relaying to whoever picks up simic-76fc6e6618.

---

### A.2.4 Emrakul — the socket is a terminal state and an unused descent path

**Position.** `Stage` (:769) is a six-member enum:

```python
DORMANT → GERMINATED (zero-duration, D12) → TRAINING → BLENDING → FOSSILIZING → FOSSILIZED
```

`epoch_tick` (:853) drives the transitions and `FOSSILIZED` sets α=β=1 (:867–869)
and **stops**. There is no seventh state and no transition out of the fifth. The
socket is that missing state plus the missing edges.

**Consequence, stated precisely: the demo measures admission economics only, never
retention economics.** Untestable as a result:

- **INV-25** (reversible influence — every non-merged growth can be brought to zero
  influence without an uncontrolled discontinuity)
- **INV-27** (maintenance warrant for ordinary decay or lysis)
- **INV-30** (grace-period protection — contribution-based removal cannot fire
  before blend and holding windows complete)
- **INV-33** (ADR-0005: admit and retain thresholds are *deliberately asymmetric*,
  separated by a versioned hysteresis band). This one is worth emphasis — the whole
  hysteresis design exists to govern the admit↔retain relationship, and the demo has
  no retain decision whatsoever, so the band has **no exercise at all**.

**The socket is unusually well-prepared, which makes the absence cheap to fix
later.** `cosine_ease` (:779) is symmetric in `p` and clamped at both ends; α and β
are driven by a stage machine reading per-step ramps (`step_tick` :838), not by
monotone counters. Mechanically, a descent path is one enum member and one branch
in `epoch_tick` away. What is genuinely missing is not the mechanism but the
**authority and its warrant** — INV-27's maintenance decision, which requires
Isperia, which the demo also only partially has (§A).

---

### A.2.5 Urabrask — the socket is present and explicitly welded shut

**You offered that this one may genuinely have no socket. It has one, and the demo
names it.** `FORBIDDEN_RELAXATIONS` (:900–913) is a nine-entry tuple of changes that
void the Class-1 determinism claim, and two entries sit exactly at the compile step:

```python
"enabling AMP",                                                          # :908
"torch.compile (D10: compiled kernels void deterministic-algorithm
 guarantees)",                                                           # :912
```

The socket sits between `build_seed`'s output and `Slot.seed` — the point where a
canonical design would become an executable artifact. The demo has declared, with
the reason recorded inline, that **inserting a compiler there voids its central
claim.**

**This is the most informative thing the demo says about Urabrask, and it explains
why INV-21 exists.** Simic *must* have a compile step — that is Urabrask's entire
mandate ("may optimise implementation, must not change meaning"). And a compile step
is precisely what threatens the bitwise-replay contract the demo protects by banning
it. INV-21 (*"every Urabrask artefact passes Jin-Gitaxias runtime conformance
against the canonical reference"*) and the `05-leyline-contracts.md#99-executablegrowthartifact`
note that *"the artefact is not trusted merely because compilation succeeded"* are
**the price of re-opening the socket the demo welded shut.** The demo is not silent
on Urabrask; it is stating the cost of the domain in advance.

*Caveat, carried from §D.10 and the catalog:* the weld is prose. `FORBIDDEN_RELAXATIONS`
is deliberately **not** a `semantic_const` (:901–903, *"Documentation-only (printed
by --selftest)"*), so it never enters `config_hash` and nothing mechanically checks
it. Selftest step 1 prints the tuple and records an unconditional pass (:2079–2082),
asserting nothing.

---

### A.2.6 Socket summary

| Domain | Socket | Inbound today | Outbound today | What the contract must become |
|---|---|---|---|---|
| **Momir** | `build_seed` (:721) | `(name: str, channels: int, init_seed: int)` — `name` is `preferred_operator`, **INV-09 schema-invalid** | A live `SeedDelta`, straight to `Slot.seed` | Inbound: `GrowthRequest` + `TelemetryEnvelope` direct from Nissa. Outbound: `RawGrowthGraph` — a *pool*, not executable, not trusted |
| **Elesh** | `tau_init` (:735) + gate 5 (:2687) | A constructed `SeedDelta` + host features | One float (`g`), written into `gain` | `CanonicalGrowthSpec` with `canonical_semantic_hash`; magnitude axis already occupied, structural axis empty |
| **Ugin** | `draw_schedule` (:2307) + frozen `cfg.window` | `(episode_seed, cfg, label)` | `tuple[int, int]` — two fan epochs | `StrategicEnvelope` that **varies**, plus a field in the actor's input to read it (§A.2.3) |
| **Emrakul** | Terminal `FOSSILIZED` (:769, :867–869) | — (no transition exists) | — | A descent path + `MaintenanceDecision` + maintenance warrant (INV-27) |
| **Urabrask** | Between `build_seed` output and `Slot.seed`; **explicitly banned** at :908, :912 | — (welded shut) | — | `ExecutableGrowthArtifact` + INV-21 runtime conformance — the price of re-opening it |

---

## B. The proposed module tree

> **Paper decomposition — do not execute.** The single-file layout is locked
> (rev 6.1). This tree exists so the split lines are visible. **The split lines
> are the contract boundaries**; everything crossing one must already be a record
> in the demo, and section C shows that it is.

```
src/simic/
├── leyline/                          ← contracts; imports nothing below
│   ├── identity.py                     config_hash (:231), frozen_block_hash (:226),
│   │                                   derive (:101), fan_identity (:1459),
│   │                                   semantic/semantic_const/_NON_SEMANTIC (:60,:71,:87)
│   ├── records.py                      FanRecord (:1433), make_fan_record (:1473),
│   │                                   RECORD_KINDS/SEED_NAMESPACES/SPLIT_ROLES (:1426–1428),
│   │                                   encode_record/decode_record (:1560,:1565)
│   ├── telemetry_schema.py             TelemetryRecord (:357), record_to_vector (:397)
│   ├── resolver.py                     decide_live (:1754)  ← ONE implementation
│   └── policy_records.py               freeze_manifest (:2848), Normalizer (:451)
│
├── tolaria/                          ← substrate: trains, branches, replays
│   ├── determinism.py                  enable_class1 (:917), state_hash (:933),
│   │                                   env_block (:969), rng_scope (:123), make_generator (:112)
│   ├── data.py                         DataBundle (:252), split_indices (:262),
│   │                                   data_split_id (:268), CommonFuture (:308), augment (:332)
│   ├── episode.py                      EpisodeCtx (:999), make_episode (:1016),
│   │                                   train_one_epoch (:1058), evaluate_acc (:1041)
│   ├── branch.py                       Snapshot (:1142), take_snapshot (:1155), _run_span (:1236),
│   │                                   run_base (:1268), run_arm (:1285), run_fan (:1367),
│   │                                   BaseTrace (:1226), ArmResult (:1209), TwinDivergence (:1196)
│   ├── optimizer.py                    build_optimizer (:874), append_seed_group (:892),
│   │                                   split_decay_groups (:751)
│   └── replay.py                       run_replay (:3925), REPLAY_REFUSAL_KEYS (:952)
│
├── nissa/                            ← observes; publishes the blind envelope
│   └── observe.py                      attach_stat_hooks (:614), _saturation_hook (:620),
│                                       confusion_stats (:424), build_record (:508)
│
├── momir/                            ← ABSENT IN THE DEMO — stub marks the hole
│   └── seed_menu.py                    SEED_NAMES (:634), build_seed (:721), the four
│                                       SeedDelta subclasses (:653,:663,:687,:704)
│                                       ── human-authored; Simic generates this
│
├── elesh/                            ← conformance contract without a conformance step
│   └── delta_contract.py               SeedDelta (:638), tau_init (:735)
│
├── wrenn/                            ← embodies
│   ├── host.py                         Host (:555), PATHOLOGIES (:539),
│   │                                   feat_channels/slot site (:575, :602)
│   └── slot.py                         Slot (:785), Stage (:769), germinate (:1167),
│                                       cosine_ease (:779), trust_region_loss (:822)
│
├── aurelia/                          ← commissions (WHEN); see note
│   └── policy.py                       Policy (:1708), _PolicyBlock (:1682),
│                                       schedule_only_mask (:1737), train_policy (:1928),
│                                       policy_loss (:1880)
│
├── jin_gitaxias/                     ← tests and certifies; never judges a candidate
│   ├── selftest.py                     run_selftest (:2061), --certify artifact (:2288)
│   ├── gates.py                        gates 1–8 (:2547–2827), GateResult (:2502),
│   │                                   dataclass_gates_ok (:2843)
│   └── preflight.py                    run_preflight (:2919), run_refan (:2418)
│
├── isperia/                          ← judges
│   ├── statistics.py                   sign_flip_pvalue (:1979),
│   │                                   money_chart_permutation_pvalue (:1990),
│   │                                   wilson_interval (:3265), class_derangement (:3279),
│   │                                   when_contrast (:3291)
│   └── adjudicate.py                   verdict (:3313)
│
├── urborg/                           ← history
│   └── store.py                        Store (:1579), merge (:1612), load (:1659),
│                                       _assert_trainable (:1664), load_for_training (:1673),
│                                       train_tune_split (:1540)
│
├── tamiyo/                           ← reveals; must not steer
│   ├── report.py                       run_report (:3829), write_divergence_report (:3034)
│   └── plots.py                        kernel_demo_plots.py (entire file)
│
└── controls/                         ← orchestration only; owns no authority
    ├── collect.py                      run_collect (:3132), worker_main (:3063),
    │                                   run_collection_episode (:2319), draw_schedule (:2307)
    ├── train.py                        run_train (:3340)
    ├── evaluate.py                     run_eval's execution loop ONLY (:3507–3646)
    └── cli.py                          main (:4004), MODES (:240)
```

### The splits that are contract boundaries

Five catalog subsystems split across domains. **Each split line is a place where a
record already crosses in the demo.**

| Catalog subsystem | Splits into | The record that crosses |
|---|---|---|
| **Identity, Config & Determinism Spine** | `leyline/identity.py` + `tolaria/determinism.py` | The four hashes as `FanRecord` fields (:1445–1449); `env_block` output as `FanRecord.env` (:1450) |
| **Data, Episodes & Telemetry** | `tolaria/data.py` + `tolaria/episode.py` + `nissa/telemetry.py` | **`TelemetryRecord` (:357)** — the TelemetryEnvelope precursor. This is the single most important split line in the tree: it separates the substrate that produces measurements from the observer that publishes them. |
| **Host, Seeds & Slot Lifecycle** | `wrenn/host.py` + `wrenn/slot.py` + `momir/seed_menu.py` + `elesh/delta_contract.py` + `tolaria/optimizer.py` | The `SeedDelta` interface (:638) crosses momir→elesh→wrenn; `ArmResult.g_at_init` / `rms_ratio_blend_entry` (:1217–1218) carry the conformance measurement out to QA |
| **Records & Store** | `leyline/records.py` + `urborg/store.py` | **`FanRecord` (:1433)** — and this split is the one place where INV-02 (Leyline dependency direction) becomes mechanically testable: `leyline/records.py` must not import `urborg/store.py`, though the reverse is required |
| **Certification Battery** | `jin_gitaxias/gates.py` + `jin_gitaxias/selftest.py` + `leyline/policy_records.py` + `isperia/statistics.py` | **`GateResult` (:2502)** crosses to the freeze manifest; the statistics block crosses to `verdict()` — **and splitting `isperia/statistics.py` out of the certification battery is the QA/judgement split (INV-18) made structural** |
| **Run Orchestration & CLI** | `controls/` + `isperia/adjudicate.py` + `tamiyo/report.py` | The seam inside `run_eval` — see section E |

Note on `aurelia/policy.py`: the demo's `Policy` is **one network exercising two
authorities**. The WHEN head (`now_head`, :1720) is Aurelia's tactical timing; the
WHICH head (`seed_head`, :1721) is selection among candidates, which in Simic
belongs to Isperia adjudicating certified evidence. They are separate submodules
already (:1709–1711, for test addressability), so the seam is visible — but they
share a trunk, and `policy_loss` (:1880) trains them jointly with only a
`pi.detach()` stop-gradient separating them (:1903–1904). The demo is honest about
this: with a fixed menu there is nothing for Momir to design and no certified
evidence for Isperia to weigh, so collapsing design-selection into the actor is a
consequence of Momir's absence, not an authority leak.

---

## C. The contract suite

The core of the document. For each boundary crossing: the record that already
crosses it, what it would need to become a typed cross-boundary contract, its
absence encoding, and its identity binding. **Every row cites demo evidence.**

---

### C.1 `TelemetryRecord` (:357) → the **blinded projection**, not the envelope

> **Correction, adopted from the contract audit (critical).** An earlier version of
> this section treated `TelemetryRecord` as the `TelemetryEnvelope` precursor and
> told Phase A to keep it as-is. **That was wrong, and adopting it would have made
> INV-08 unimplementable.** `TelemetryEnvelope` is *supposed* to carry provenance and
> identity; the record that has them **absent** is the per-consumer blinded
> projection. The demo's single consumer set made the two accidentally identical —
> and that accidental identity is itself the finding.

**Three sources settle it:**

1. **The envelope carries provenance by design.**
   `05-leyline-contracts.md:49–69` lists `provenance`, `region_id`,
   `ablated_context`, `lifecycle_context`, `validity_mask` and
   `normalization_manifest` **as envelope fields**.
2. **Blinded consumers are not on the envelope's publication list.** `:46` publishes
   it to "Ugin, Aurelia, Momir, Urborg and Tamiyo" — **Jin-Gitaxias and Isperia are
   absent** — and `:75` names the mechanism: *"Independent publications and permitted
   per-consumer **projections** of one observation share `observation_id` but carry
   distinct `telemetry_id`s."*
3. **Nissa's mandate requires provenance.** Appendix B: *"May normalise and **attach
   provenance**"* (`02-constitution.md:274`). And INV-37 constrains **views** —
   "source fields are absent from **QA and adjudication views**" — not the envelope
   that feeds them.

**So the demo has one record doing two jobs**, because it has exactly one consumer
population and never needed to separate them. Splitting them is a Phase-A obligation,
not a refinement.

**Authority:** Nissa (sole producer). **Consumers in the demo:** the policy, the
normalizer fit, the gates, the store — all of which are, in Simic terms, *blinded*
consumers.

**Current shape** (:358–369): 12 fields — `epoch`, `train_loss`, `val_loss`,
`val_acc`, two loss deltas, four per-stage 3-tuples (`grad_norm_mean`,
`grad_norm_var`, `act_saturation`, `weight_norm`), `per_class_val_acc_std`,
`confusion_entropy`. `frozen=True`.

**What it already gets right — as a projection.** Blinding is **by field absence,
not by ignoring**. There is no seed name, arm name, pathology id, episode seed, or
provenance field anywhere in the dataclass. The identity is *not present to be
ignored*. That is exactly what INV-37 requires of a **view**, and it is what
`blinding-by-construction.md` prescribes as the first of three layers. The demo
achieves it, and `--selftest` step 6 (:2154–2163) greps the field names to keep it
that way.

**Read as a projection this is excellent and should be carried forward. Read as an
envelope it is a record that cannot satisfy INV-08**, which requires the intent, the
conditioning input and the snapshot to reconcile to one `observation_id` and to
**fail closed** on a mismatch — impossible when no field carries the observation
identity.

#### The envelope↔projection distinction is itself a contract shape

The demo needs exactly one telemetry record because it has exactly one consumer
population. Simic needs two record classes and a **projection function** between
them:

| | `TelemetryEnvelope` | Blinded projection (`TelemetryRecord`'s real analogue) |
|---|---|---|
| **Producer** | Nissa | Nissa, by allowlist projection from the envelope |
| **Identity** | `observation_id`, `telemetry_id`, `host_state_id`, `snapshot_id` | `telemetry_id` distinct; `observation_id` **only** if the blinding policy permits the join |
| **Provenance** | **Present** — mandated by Nissa's clause | **Absent by schema** |
| **Consumers** | Ugin, Aurelia, Momir, Urborg, Tamiyo (`:46`) | Jin-Gitaxias, Isperia (`:75`, and INV-17) |
| **Demo status** | **Not present** — no record carries observation identity | **`TelemetryRecord` (:357)**, and it is a good one |

The projection must be an **allowlist** — fields named in, never a deny-list — so a
future envelope field is excluded by default rather than leaked by default. That is
the layer the demo does not have and cannot have, because it has no envelope to
project *from*: its blind record is authored blind rather than derived blind. The
difference matters the moment a second consumer population exists.

**What the envelope side needs, all currently absent:**

`record_to_vector` (:397) inherits the property: it maps exactly those 12 fields
to a 20-float vector, and `epoch` (index 0, `EPOCH_FEATURE_IDX` :352) is the only
non-metric feature and carries no arm or seed information.

**What it needs to become a cross-boundary contract:**

| Need | Why | Demo evidence |
|---|---|---|
| `observation_id`, `host_state_id`, `snapshot_id` | The envelope is not independently addressable; identity lives entirely on the *containing* `FanRecord`. INV-08 requires intent, request, proposal and snapshot to reconcile to the same observation — impossible if the observation has no id | `FanRecord.telemetry: list[dict[str, object]]` (:1452) — telemetry is a nameless payload inside another record |
| `schema_version` on the envelope itself | Currently versioned only by containment; a telemetry field change is invisible unless `SCHEMA_VERSION` (:55) is bumped for reasons that may have nothing to do with telemetry | :1434 vs :1452 |
| `normalization_manifest` | The `Normalizer` is fit at preflight and frozen into `frozen.json` (:2878), then loaded read-only (:3347, :3493). Correct discipline, wrong location: the envelope says nothing about the basis its consumers will use | :2958–2961, :2878 |
| `validity_mask` | See below | — |

**Absence encoding.** Currently *stronger than a mask for the finite case and
absent for every other case*. `__post_init__` (:371–393) raises
`TelemetryDivergence` on any non-finite float or tuple element, so a numerically
diverged epoch **cannot become a record** — absence-as-a-number is unrepresentable
at the construction boundary. Callers convert the exception into a recorded
`diverged` outcome (:1256, :2437, :3518) rather than a crash. This is
`silent-default-elimination.md` done right.

Two holes, both live:

1. **`check_finite` has no `else: raise` (:372–381).** `float` and `tuple` are
   validated, `int` explicitly passes, and anything else falls through silently.
   A `None` — or a 0-dim tensor carrying NaN — passes the guard unchallenged.
2. **There is no way to say "this stage's hook never fired".** Every field is
   mandatory. The demo handles this by making absence loud at build time instead
   (`KeyError` on the stats dict; the comment at :1085 states the rule: *"KeyError
   = hooks never attached — loud, never silent zeros"*), which works inside one
   process and does not survive the wire.

**Identity/hash binding.** None of its own. It is bound only transitively, through
the `FanRecord` that contains it, to `config_hash`, `frozen_block_hash`,
`manifest_hash`, `common_future_hash` and `host_init_hash` (:1445–1449).

---

### C.2 `FanRecord` (:1433) → the whole Leyline suite, collapsed into one shape

**Authority:** `make_fan_record` (:1473) is the **sole constructor** for all six
record kinds — validating, keyword-only, and it derives `fan_id` itself (:1529) so
identity can never diverge from content. As a *validation* design this is
excellent. As an *authority* design it is one producer for six record classes that
have six different producers.

**Current shape:** **22** flat fields (verified by reflection), one shape for six kinds
(`RECORD_KINDS` :1426: `fan`, `refan`, `policy_run`, `preflight_iter`,
`extension_event`, `void_event`). Kind-specific payloads are nullable slots —
`decisions` (:1453) for `policy_run`, `gate_results` (:1454) for `preflight_iter`,
plus `fan_epoch` and `refan_k` — rather than a discriminated union.

**What it already gets right:**

- **Three closed vocabularies**, whitelisted in the sole constructor with
  `ValueError` on anything unknown (:1426–1428, checked :1501–1506). An invalid
  record cannot be built, let alone written.
- **Content-addressed identity over counters.** `fan_identity` (:1459) hashes the
  full identity tuple; the comment at :1498–1500 states the rule that keeps it
  stable across re-runs (`iteration` and `policy_checkpoint_id` must come from
  store state, never a process counter). Call sites honour it (:3174, :3448).
- **Fail-closed schema versioning.** `decode_record` (:1567–1573) raises on any
  `schema_version` inequality and the error text states the governing policy:
  additive-only post-collection, non-additive bumps are an owner decision, *"never
  silent."* This is `schema-versioning-and-evolution.md`'s fail-closed gate,
  implemented.
- **Four identity hashes carried on every record** (:1445–1449), binding it to
  source, config, freeze generation, data future and initial host state.

**What it needs:** a **discriminated union**, one record class per kind, one
producer each:

| Kind | Producer under the decomposition | HLD analogue |
|---|---|---|
| `fan` / `refan` | `tolaria/branch.py` | `BranchResult` (`05-leyline-contracts.md#913-branchresult`) |
| `preflight_iter` | `jin_gitaxias/preflight.py` | `QualityReport` |
| `policy_run` | `isperia/adjudicate.py` + `controls/evaluate.py` | `AdmissionDecision` |
| `void_event` / `extension_event` | `controls/collect.py` | `EventEnvelope` |

**Absence encoding.** Structural where it counts (`manifest_hash: str | None`, with
the reason stated inline: *"None pre-freeze"*, :1447), and convention-only where
it does not: nothing validates that a kind populates the right slots. A `fan` with
`gate_results` set, or a `policy_run` with `decisions=None`, constructs cleanly
(catalog line 437). The kind/payload correspondence is **convention, not contract**.

**Identity/hash binding.** `fan_id` = SHA-256 over
`[episode_seed, fan_epoch, kind, refan_k, policy_checkpoint_id, iteration]`
(:1468). One omission worth carrying forward: `seed_namespace` is **not** in the
tuple, so cross-namespace uniqueness rests on episode-seed derivation one layer up
(`derive(run_seed, "preflight"|"train"|"eval", i)` at :2937/:3196/:3508). That
derivation *is* domain-separated and `derive` length-prefixes its labels
(:104–107), so the guarantee holds — but it lives in a different section and is
undocumented at :1459. Under `canonical-identity.md`, an identity function whose
uniqueness argument is elsewhere is a contract with an unstated precondition.

---

### C.3 `ArmResult` (:1209) → `BranchResult`

**Authority:** `run_arm` (:1285), sole producer. **Consumers:** the gates, the
report, the plotting sidecar, the policy training path.

**Current shape:** 12 fields — `name`, `status`, `r_val`, `r_test | None`,
`curve_val`, `curve_test | None`, `init_seed`, `g_at_init | None`,
`rms_ratio_blend_entry | None`, `hash_after_training | None`, `host_hashes | None`,
`alpha_beta_log | None`.

**What it already gets right.** Absence is **structural, not sentinel-wise**:
`curve_test: list[float] | None` with the invariant stated in-line at :1011
(`None` iff `read_test=False`) — an explicit convention against empty-list
ambiguity. `host_hashes` is `| None` and documented as noop/nullseed-only (:1220).
`status` distinguishes `"ok"` from `"diverged"` (:1211) so a divergence is a
*result*, not a missing value.

**The defect: the typed record is discarded at the boundary.** `FanRecord.arms` is
`list[dict[str, object]]` (:1451), and **two incompatible shapes are written into
it**:

- full `dataclasses.asdict(ArmResult)` — 12 keys (:2376, :2492)
- a hand-built partial — 4 keys, `{name, status, r_val, r_test}` (:3608)

*(Correction: an earlier draft also cited `:2188` as a production writer of a partial
arm. It is neither — it is a **selftest fixture** (`config_hash="selftest"`,
`host_init_hash="selftest"`) and its fourth key is `curve_val`, not `r_test`. One
production site writes a partial, not two. The finding stands on :3608 alone.)*

Consumers index `rec.arms` by key (:1845, :2511, :2517) and `run_report` reads
`a.get("g_at_init")`, `a.get("curve_val")`, `a.get("status")` (:3857–3862) — so a
partial arm **silently under-counts** rather than failing. Today four independent
`kind` filters hold this off (:3649, :3842, `kernel_demo_plots.py:25`, and the
resume path reading `decisions` not `arms`), which is defence by coincidence: no
schema check enforces that an `arms` entry is a complete `ArmResult`.

A second, smaller hole: `arms[].name` has **no closed vocabulary**, unlike `kind`,
`seed_namespace` and `split_role` which do. At :3608, `name = chosen or "noop"`
labels a never-germinating comparator's arm `"noop"` — colliding with the name of
a genuine measured no-op arm while denoting something entirely different.

**Identity/hash binding.** `hash_after_training` (:1219) and `host_hashes` (:1220)
are the matching anchors — this is the field that makes the twin check (:1382–1388)
and the cross-arm bitwise assertion (:1396–1400) possible. Well designed; see
section D.

---

### C.4 `Snapshot` (:1142) → the branch-point contract

**Authority:** `take_snapshot` (:1155). **Consumer:** `run_arm` (:1300–1309).

**Current shape:** five fields — `host_state`, `opt_state`, `cpu_rng`,
`cuda_rng | None`, `epoch`.

**This is the demo's best contract, and it is best because of what it declares it
does not carry.** The comment at :1143–1146 states the sufficiency invariant
directly: snapshots are taken only on the base path, where the optimizer is always
the never-germinated 2-group state, and *"there is no restore_snapshot: arms are
built fresh from snapshot values."*

Compare against `05-leyline-contracts.md#911-snapshot`. The demo's is a strict
subset, and **every omission is principled and stated**:

| HLD field | Demo status | Stated reason |
|---|---|---|
| `host_scheduler_state` | absent | Constant LR by deliberate design (:874–878) — no scheduler state exists to capture |
| `dataloader_cursor` | absent | No sampler. `CommonFuture` is pre-drawn (:316–328) and indexed by **absolute** epoch (:1060, :1069), so there is no cursor to desynchronise |
| `growth_slot_states` | absent | Snapshots are taken only on the base path where the slot is `DORMANT`; `Slot` is never a submodule of `Host` (verified: seed params absent from `host.state_dict()`) |
| `random_number_states` | **present** | `cpu_rng` + `cuda_rng` (:1160–1161) |
| `device_and_determinism_manifest` | absent | `env_block` is stamped on the *record* (:1450), not on the snapshot |

**What it needs:** a `snapshot_id` — currently snapshots are keyed only by `epoch`
inside `BaseTrace.snapshots: dict[int, Snapshot]` (:1230), so they are addressable
within a base trace and nowhere else. And it is **never serialized**: it is an
in-process contract between `run_base` and `run_arm`, not a wire record. Making it
a wire record is precisely what Phase A needs for cross-process branching, and the
two absences that would then bite are `snapshot_id` and the determinism manifest.

**Absence encoding.** `cuda_rng: torch.Tensor | None`, `None` iff the device is not
CUDA (:1161) — structural, correct. **Scope limit worth recording:** RNG capture
covers torch's CPU and CUDA generators only, not Python's `random` nor NumPy. No
draw from either exists on the training path, and explorer 3 verified over all 80
pathology × seed × stage combinations that the model path consumes **zero** global
RNG — so this is a narrow-but-sound contract, undocumented as a contract.

---

### C.5 `CommonFuture` (:308) + `hash` (:328) → the matched-future contract

**Authority:** `CommonFuture.draw` (:316), called exactly once per episode (:1020).
**Consumers:** every arm.

This is the mechanism behind **INV-06 (common future)** and it is enforced by data
structure rather than by re-seeding. All per-step stochasticity for a whole episode
— batch `order` per epoch, `crops`, `flips` — is pre-drawn up front (:322–324); the
*same object* is threaded to the noop arm (:1381), each seed arm (:1392) and the
nullseed arm (:1402); `train_one_epoch` indexes it by absolute epoch (:1060, :1069)
and draws no RNG of its own. Arm epoch *e* therefore consumes byte-identical batch
order, crops and flips as base epoch *e*. `run_refan` (:2469) deliberately draws a
*different* future under a distinct label tuple to supply gate 3's noise floor —
the contract is used in both directions.

**What it needs:** it is already a `future_sequence_id` analogue
(`05-leyline-contracts.md#912-testplan`) and it is already a replay refusal anchor
(:3955). The gap is canonicalisation discipline: **`CommonFuture.draw` hashes its
three tensors without the length prefixing that `data_split_id` uses**
(:325–328 vs :271–275). Both hashes serve the same anchoring role; only one is
unambiguously encoded. Unreachable as a collision given fixed shapes, but under
`canonical-identity.md` two anchors with two canonicalisation rules is a contract
inconsistency, and the demo already knows the right rule — `derive` length-prefixes
its labels (:104–107) and `state_hash` length-prefixes its tensors (:938–944).

---

### C.6 The insertion-region contract — implicit and duplicated

**Authority:** Wrenn ("embodies legal, warranted growth and **declares
insertion-region contracts**", `02-constitution.md` Appendix B).

The demo has an insertion-region contract. It is not written down as a record, and
it is maintained by **two independent literals**:

- `Host.feat_channels = 64` — hardcoded at :575, not derived from `w2` (:563)
- the slot site itself — `forward_to_slot` (:598) → `forward(x, slot)` injecting
  between stage2 and stage3 (:602), producing `[B, 64, 8, 8]` for every pathology

The 64-wide slot genuinely *is* fixed across all four pathologies (`mild` alters
only `w1`/`w3`; `channel_starved` alters only stage2's *mid* channel, leaving
`out_ch = w2 = 64`), and this is confirmed empirically. But the invariant is held
by two literals rather than one, so a future width edit desynchronises the host
from the seed constructor with nothing detecting it.

**Contract shape it wants:** `RegionContract { region_id, input_output_contract,
region_contract_version }` — which is exactly what `GrowthRequest` binds
(`05-leyline-contracts.md#94-growthrequest`: `input_output_contract`,
`region_contract_version`). In the demo the contract is real, load-bearing, and
represented nowhere.

---

### C.7 `GateResult` (:2502) → `QualityReport`

**Authority:** Jin-Gitaxias. **Consumers:** `freeze_manifest` (:2860–2862),
`dataclass_gates_ok` (:2843), `run_collect` (:3153).

**Current shape:** four fields — `ok: bool`, `reason: str | None`,
`detail: dict[str, object]`, `remedy: str`.

**What it already gets right — `remedy` is a genuinely excellent contract field.**
It names the licensed knob per gate (gate 5's is *"tau, lambda, seed_lr — never the
sampler"*, :2688). A QA record that constrains the *permitted response* to its own
evidence is a strong anti-p-hacking device and it is the kind of field that stops a
certification record from drifting into a verdict. It has no HLD analogue and
Phase A should take it.

**Authority reading, stated once.** Jin-Gitaxias may certify the apparatus and
pass/fail on it — that is runtime conformance and evidence certification, his by
right ("Tests artefacts and certifies evidence. May report defects and
uncertainty"). What he may not do is adjudicate a *candidate*. The gates judge the
harness, not the seeds, so **the demo keeps that line**. Gates 1–8 are legitimately
Jin-Gitaxias territory.

**The actual contract finding: `ok: bool` has no severity lattice.** The HLD's
`QualityReport` carries `hard_defects[]` and `soft_warnings[]` and explicitly *"does
not contain ADMIT or REJECT"*. `GateResult` has a single boolean and no warning
level — and the consequence is visible in the code. **Gate 7 had to be encoded as
`return GateResult(True, ...)` unconditionally, with `remedy="report-only"`
(:2755).** There was no way to express "measured, informative, not blocking", so a
report-only gate is shimmed in as an always-passing blocking gate. `test_gate7_is_report_only`
(`test_preflight_gates.py:236`) pins the always-pass behaviour as intended rather
than accidental — the shim is deliberate and documented, which makes it a clean
demonstration rather than a bug. The cost is precise: **"8 gates passed" means
seven.** Gate 8 compounds it, returning `ok=True` with `"skipped (GPU-only)"` on
non-CUDA (:2761–2762) — a third meaning packed into the same boolean.

A boolean certification contract with no severity lattice forces exactly this shim.
That is the lesson.

**Absence encoding.** Gate 5 gets this right in a way worth copying: **no
measurement is an explicit failure, not a pass** (:2702–2703). Gate 3 likewise fails
outright with no paired refans (:2652–2653). Contrast gate 8's skip-to-`ok=True`.

---

### C.8 The five verdict booleans (:3313–3325) → `AdmissionDecision`

**Authority:** Isperia. **Producer:** `verdict()` (:3313), a pure function.

**Current shape:** `dict[str, bool]` with five keys — `lift_positive`,
`beats_schedule_only`, `agreement_beats_null`, `money_chart`,
`falsifier_collapses` (:3319–3325).

**What it already gets right.** All five are **pre-registered** and every threshold
is hash-bound: `cfg.alpha_level` and the verdict thresholds live in `FROZEN_FIELDS`
(:211–216) so editing one moves `frozen_block_hash` and invalidates every
downstream artifact; `AGREEMENT_MARGIN` is a `semantic_const` (:3256) and so enters
`config_hash`. The function is pure and takes `cfg` explicitly. Under
`versioned-policy-parameters.md` this is most of the discipline: **the thresholds
are not code constants, they are hash-frozen pre-registered parameters, and
post-hoc tuning is mechanically detectable.**

**What it needs to become an `AdmissionDecision`:**

| Need | Evidence of the gap |
|---|---|
| `decision_id` | It is a bare `dict[str, bool]`; the decision has no identity |
| `adjudication_policy_version` | Bound only *implicitly*, via `frozen_block_hash` on the containing record and `manifest_hash` in `eval_results.json`. The binding exists at the **file** level, never at the **record** level |
| `decision_reasons[]` | Absent — five booleans with no explanation attached |
| A single `verdict` field | **`verdict()` never ANDs its five booleans** (:3319–3325); every consumer just prints them (:3820, :3904, :3920, :4054). The conjunction is left to the reader |
| `tail_veto_results` and a lexicographic stage | All five booleans are **peers**. INV-45 requires the tail-risk veto to be adjudicated *before* any utility comparison and to be untradeable against measured benefit — a flat dict of five peer booleans has no way to express that ordering |

**Downstream consequence of the missing conjunction:** `eval` exits 0 regardless of
the verdict (:4054–4055), while `selftest` (:4039), `preflight` (:4043) and
`collect` (:4047) all gate their exit codes. A five-false verdict is
indistinguishable from a five-true one to CI or a shell `&&` chain. That is what a
decision record without a decision field costs.

---

### C.9 The `decisions` payload (:3588) → the per-episode adjudication record

Distinct from C.8: `verdict()` is the *run-level* judgement; this is the
*per-episode* one, and it carries the sharper absence defect.

**Current shape** (:3588):
`{germination_epoch, chosen, lift, r_noop_test}`, appended per comparator per
episode into `FanRecord.decisions` (:1453, :3610).

**The defect: the baseline's `status` is never recorded.** Every fan arm carries an
explicit `status` field (:1211). Here, only the bare float lands. But
`r_noop_test` falls back to `cfg.diverged_r` on `TelemetryDivergence` (:3519), and
so does the treated run (:3585). **If the baseline diverges and the treated run
does not, `lift = r_test − 0.10` reads as a large seed-attributable gain when the
real event is that the baseline fell over — and nothing downstream can separate the
two.**

This is `silent-default-elimination.md` exactly: a sentinel value (`0.10`) standing
in for a qualitatively different outcome (divergence), in a field typed `float`
where absence and failure are both unrepresentable. The demo does the separation
correctly elsewhere — the money chart has a diverged-excluded companion
(:3718–3732) — so the machinery exists; the lift table simply has no equivalent.

**What it needs:** `r_noop_status` beside `r_noop_test`, or better, a
`NoOpMeasurement { status, r_test }` union so that a diverged baseline is
structurally distinguishable from a poor one.

---

### C.10 The freeze manifest (:2848) → the pre-registration / policy record

**Authority:** `freeze_manifest` (:2848). **Consumers:** every mode
(:3145–3154, :3343, :3463, :3946).

This is the demo's **only versioned policy record**, and it is the most instructive
contract in the file — both for what it gets right and for the one thing it gets
wrong.

**What it already gets right:**

- **Refusal-chained.** It raises on any not-ok gate (:2860–2862), a dirty worktree
  (:2863), a missing `certified.json` (:2866), or `HEAD != certified["git_rev"]`
  (:2870). Three of the four refusals plus write atomicity are pinned by tests
  (`test_preflight_gates.py:253, :262, :270, :280`).
- **It freezes every fitted quantity before any data is collected.** The
  `Normalizer` is fit on preflight-namespace fans only (:2958–2961), serialized into
  the manifest (:2878), and thereafter loaded read-only (:3347, :3493). The
  temperatures derive from the frozen density (:2880–2881) and `train_policy` takes
  `frozen_density` as a **keyword-only parameter with no default** (:1934) — so
  recomputation from the collected records is *impossible by signature*. That is
  contract design doing real work.
- **Atomic write** (:2914) and a `spec_rev` literal naming rev 6.1 (:2877).

**The defect: `manifest_hash` is a run identity wearing a policy identity's name.**

`manifest_hash` (:2909) is a SHA-256 over the *whole* manifest — including
`gate_results` detail, `det_mode_cost` and `concurrency_factor`, all of which are
**measured, run-varying values**. Therefore re-running `preflight --freeze` on the
*identical commit* produces a *different* `manifest_hash`. `freeze_manifest`
overwrites `frozen.json` unconditionally (:2914) with no guard for a store that
already holds records. `run_train` then reads the normalizer and betas from
manifest B (:3347–3354) while training on records collected under manifest A,
checking only `frozen_block_hash` and `config_hash` (:3343) — never the records'
own `manifest_hash`. `load_for_training` (:1673) filters on `split_role` and `kind`
only. Reachability is high: both freeze preconditions (clean worktree,
`HEAD == certified rev`) are satisfied by simply re-running preflight on the same
commit. And `Store.merge`'s duplicate backstop is keyed `(manifest_hash, fan_id)`
(:1636), so it **permits** the same fan under two generations — double-counted by
`tr_fan_counts` (:3486) and by `load_for_training`.

**In contract terms** (`versioned-policy-parameters.md`): one record is carrying two
identities that must not share a hash.

| Part | Contents | Identity rule |
|---|---|---|
| **Policy** | normalizer, temperatures, gate thresholds, `schedule_id`, `data_split_id`, `n_train`, `spec_rev` | Content-hashed; changes **only** through a recorded lifecycle event. This is the hash records bind. |
| **Evidence** | `gate_results` detail, `det_mode_cost`, `concurrency_factor`, `gate8_outcome` | Recorded *beside* the policy, referenced by it, and **not** part of the policy identity |

Split that way, re-freezing on the same commit yields the same policy hash, records
stay bound to the calibration that produced them, and `run_train` gains a check it
can actually make.

#### The split does not weaken pre-registration — verified, and it is the fix

An earlier draft flagged this as the recommendation most likely to be wrong, on the
worry that removing measured values from the policy identity would weaken the
anti-p-hacking property. **That worry is retired.** The property never rested on
`manifest_hash`. Both enforcement sites check a different pair, read directly:

```python
# run_train, :3343
if manifest["frozen_block_hash"] != frozen_block_hash(cfg) or manifest["config_hash"] != config_hash():
    raise RuntimeError("train refused: manifest mismatch ...")

# run_eval, :3463  — the identical pair
if manifest["frozen_block_hash"] != frozen_block_hash(cfg) or manifest["config_hash"] != config_hash():
    raise RuntimeError("eval refused: manifest mismatch ...")
```

Threshold tampering is caught by `frozen_block_hash` (all eight gate thresholds live
in `FROZEN_FIELDS` :211–216) and code tampering by `config_hash`. **Neither
enforcement site consults `manifest_hash` at all** — `run_eval` reads it at :3469
only to *stamp* onto records, never to compare.

I checked every one of its **48** occurrences (38 in `kernel_demo.py`, 10 in the
sidecar). `manifest_hash` is **compared** in exactly **three** places, all of which
want a *run* identity — which is what it correctly is. A fourth row below is a
**dedup key, not a comparison**, and is listed because it is part of the defect:

> **Correction, from the contract audit (finding 10).** An earlier version of this
> table classified all four consumers as "survives, unchanged." That conflated two
> different claims — *no consumer breaks* and *the split is complete* — and asserted
> the first where §F.2 promises the second. The right discriminator is **what
> question each check asks**, because that determines which identity it needs.

| Site | The question it asks | Identity that question depends on | Under the split |
|---|---|---|---|
| `run_replay` :3953–3954 | *"Is this the same execution?"* | **Run** identity | **Unchanged** — correctly stays on `manifest_hash` |
| `run_report` D6 :3834–3839 | *"May I pool these into one number?"* | **Calibration** — pooling validity depends on a shared normalizer and shared temperatures, **not** on a shared `concurrency_factor` | **Must be retargeted** to the policy hash |
| `kernel_demo_plots.py` :150–152 | *"May I pool these into one figure?"* | **Calibration** — same question | **Must be retargeted** |
| `Store.merge` :1636 | *"Is this fan already counted?"* | **Calibration** — the comment at :1630–1632 scopes uniqueness to "within one `manifest_hash` generation" | **Must be retargeted** — keying on `(policy_hash, fan_id)` is what makes the duplicate **collide and raise** |

**What this changes about the recommendation.** Splitting the record alone fixes the
**train** path and leaves two things broken:

1. **The report path stays broken in exactly the scenario the split exists to make
   benign.** An operator who re-freezes on the identical commit still cannot run
   `--report` across the boundary, because D6 refuses on a hash that moved for
   reasons unrelated to calibration.
2. **The double-count is not fixed.** §E.5 files it as part of the same defect, and it
   is only fixed if `merge`'s dedup key moves to the stable hash — at which point the
   same fan re-collected across a re-freeze collides and raises, which is the desired
   behaviour.

So the action is **two records *and* a consumer-retargeting pass**, not two records
alone. Each consumer must be re-pointed at whichever identity its own question
depends on.

**And the split would actually *deliver* a stable hash, not merely permit one.**
`run_preflight` is idempotent on the fan set — it resumes fan-granularly and skips
what is already durable (:2938, :2953) — so a re-freeze on the same commit refits the
**same** normalizer over the **same** telemetry vectors and re-derives the **same**
temperatures. Every field destined for the policy side is reproducible. The values
that genuinely vary between two freezes are gate 8's live `concurrency_factor` and
`det_mode_cost` — both measured, both landing on the evidence side by construction.
So the policy hash is stable *by the demo's own existing behaviour*; nothing new has
to be built to make it so.

**So the conclusion is stronger than "the split is safe": the split is what makes the
binding possible.** Explorer 8's re-freeze defect exists *precisely because*
`manifest_hash` moves for reasons unrelated to policy, so it cannot serve as a stable
key binding records to their calibration. A content-hashed policy record would be
stable across a re-freeze on the same commit and could serve as that key — while
`manifest_hash` continues to serve the three consumers above, unchanged.

**Implementation caveat for whoever does the split.** Everything policy-relevant must
land in the policy record, and `plan_authored_constants` (:2892–2907) currently mixes
the two categories in one block: genuine policy constants (`gate1_min_mild_noop_wins`
… `gate6_late_density_mult`, `tau_eps`, `preflight_refans`, `policy_lr`,
`policy_steps`, `warmup_frac`) sit beside operational knobs (`fsync_every`,
`eval_chunk`, `policy_batch_size`) — and `fsync_every` is in **neither**
`FROZEN_FIELDS` nor `config_hash`. The split is the natural moment to sort that:
policy constants into the policy identity, operational knobs into the evidence
record. That also closes the definition-lifecycle gap noted immediately below.

**A second, smaller finding — a definition-lifecycle gap.**
`plan_authored_constants` (:2891–2907) is an echo *"for owner sign-off"*. It
includes `fsync_every`, which is in **neither** `FROZEN_FIELDS` nor `config_hash`
(`Config` is `_NON_SEMANTIC` by explicit opt-out, :91). So a value is presented for
signature that the signature does not bind, and the durability cadence can change
between freeze and collect without invalidating the manifest. Under
`definition-lifecycle.md`, sign-off on an unbound value is sign-off on nothing.

---

### C.11 `host_init_hash=""` (:3606) → a broken semantic-identity binding

Small field, large lesson.

`FanRecord.host_init_hash` is typed **`str`** (:1449) — not `str | None`.
`run_collection_episode` fills it with `state_hash(ctx.host)` for every fan
(:2342, :2374). `run_eval`'s comparator loop fills it with `""` (:3606).

**This is the textbook silent default** (catalogue entry #1): absence encoded as a
*value of the field's own type*, so no reader can distinguish "not applicable" from
"not measured" from "measured as empty". And the field is not incidental — it is
the one field that would let a post-hoc auditor confirm that the baseline episode
and the treated episode started from the same host state. INV-20 requires artefact,
QA report, decision and embodiment to reference the same canonical hash; here the
decision record's binding is a placeholder.

The consequence is section E's headline. `common_future_hash` is recorded for the
treated episode (:3605) but is never computed for `noop_ctx` at all.

**The fix is small and the demo already has every piece:** `policy_run` should carry
**two** host-init hashes — baseline and treated — and compare them. One
`state_hash` call, one comparison, and the resume path gains a real anchor. And the
type should make `""` unrepresentable.

---

### C.12 The deployment rule (:1754 vs :3562–3573) → the resolver contract

Under `deterministic-resolution.md`, the demo's deployment rule **is** a resolver:

```
resolve(telemetry_prefix, frozen_normalizer, policy_checkpoint, window, cfg)
    → (act: bool, seed: str | None)
```

It is pure, it is a function of recorded inputs only, and its tie-break is pinned
to the lowest `SEED_NAMES` index (:1780, mirrored :3417–3419). It even raises on
non-finite logits (:1774–1777) rather than letting `NaN > 0.5 == False` read as
"never germinate, lift 0" — the deliberate refusal of a silent default at exactly
the point where one would be catastrophic.

**The defect: it is implemented twice, and the tested copy is not the deployed
copy.** `decide_live` (:1754) has **zero production callers** — its only caller
repo-wide is `tests/unit/kernel_demo/test_policy.py:64` (coordinator-verified).
`run_eval` re-implements the rule inline at :3562–3573. The author knows and asks
for manual lockstep (*"the inline twin of the unit-tested `decide_live`… Keep the
two in lockstep: `decide_live` is the tested owner"*, :3568–3571). The arrangement
inverts the guarantee: **the function that produces every recorded eval decision has
no direct unit test; the function the tests pin produces nothing.** **They already differ in three ways, not one** — and the drift is worse than an
earlier draft of this section recorded:

| # | Difference | `decide_live` | Deployed twin |
|---|---|---|---|
| 1 | **Window guard** | Owned internally (:1763) | Delegated to the caller's `lo <= e <= hi` (:3551) |
| 2 | **Finiteness layer** | Checks the **raw logit** (:1774) — rejects `-inf` | Checks **post-sigmoid/softmax** (:3397) — **admits `-inf`**; see §E.8 |
| 3 | **Tie-break representation** | `logits == logits.max()`, `.nonzero()[0]` on raw logits (:1780) | `max(pi.values())` then first match in `SEED_NAMES` order, on **softmax probabilities** (:3420–3421) |

Difference 2 is a live defect (§E.8). Difference 3 currently agrees — equal logits
give equal probabilities — but it is float equality on *transformed* values, so the
two are pinned to the same answer by monotonicity rather than by construction.

**Three independent drifts in a rule the author explicitly asked to be kept in
lockstep is the strongest possible argument for recommendation §F.3.** Manual
lockstep did not hold, and the one copy that drifted into a defect is the copy that
produces every recorded eval decision.

**What the contract needs:** one resolver, and `resolver_version` stamped on its
output — which `GrowthRequest` already requires
(`05-leyline-contracts.md#94-growthrequest`). The demo's `decisions` payload (:3588)
carries `germination_epoch`, `chosen`, `lift`, `r_noop_test` and **no resolver
version** beyond `policy_checkpoint_id` on the containing record.

A related note for Phase A's dead-code policy: both `decide_live` and the fully-dead
`query_teacher_forced` (:1786) are `@semantic`, so their source is inside
`config_hash` — deleting an unused function invalidates every recorded hash and
makes `run_train` refuse (:3343–3344). **Dead code on the semantic surface is
load-bearing dead code**, costlier to remove than to keep. A contract-identity
scheme that hashes source text creates that incentive; one that hashes a declared
*schema* does not.

---

### C.13 The two telemetry encoders (:397 vs :1811) → one canonical encoder, split in two

`record_to_vector` (:397) takes a `TelemetryRecord`. `_telemetry_vector_from_dict`
(:1811) takes a decoded dict. They must emit the same 20 values in the same order,
and **that contract is enforced only by a comment** (:1812: *"the field order MUST
mirror it"*). Nothing compares them — verified by exhaustive grep across
`experiments/` and `tests/`: `_telemetry_vector_from_dict` is referenced in **zero
tests**; `record_to_vector` appears in exactly one (`test_telemetry.py:32`) which
pins only `v.shape` and `v[EPOCH_FEATURE_IDX]`.

The exposure is asymmetric and severe. The dict twin feeds **every live path** —
the normalizer fit (:2959), policy training features (:1843), eval queries (:3386)
and gate 2's own inputs (:2588) — while `record_to_vector` survives only on
`decide_live`'s dead path (:1749). **A field-order drift would silently permute the
feature space between what the normalizer was calibrated on and what a decision
reads, with every gate still green.** Two explorers found this independently
(catalog :108, :482, :652).

**Why the twin exists, and why that matters for Phase A.** It is not an accident of
carelessness — it is a **consequence of the untyped payload**. `FanRecord.telemetry`
is `list[dict[str, object]]` (:1452), so once a record is decoded there is no
`TelemetryRecord` to hand to `record_to_vector`, and a second decoder had to be
written. Type the payload and one encoder disappears.

**But typing the payload is necessary and not sufficient.** A decode-then-reconstruct
round-trip cannot be *relied* on, in both directions:

1. **Encode is lossy.** `_sanitize_json` (:1550–1551) maps every non-finite float to
   `None`. That is the right choice against JSON's non-standard `NaN` literal, but
   on the wire a diverged measurement and an absent one become the same token.
2. **Reconstruction has no floor.** `TelemetryRecord.__post_init__`'s `check_finite`
   (:372–381) validates `float` and `tuple`, explicitly passes `int`, and has **no
   `else: raise`**. `None` is none of those, so it falls straight through. A
   reconstructed `TelemetryRecord` would construct cleanly with `train_loss=None` in
   a field annotated `float` — dataclasses do not validate types.

**Reachability, stated honestly.** This is *not* a live defect on the normal path.
`__post_init__` (:375) makes a non-finite `TelemetryRecord` unrepresentable at
construction, so a record carrying NaN never exists and `dataclasses.asdict(t)`
(:3609) always serializes finite telemetry — the lossy branch of `_sanitize_json` is
effectively unreachable *from telemetry*. The ways into the hole are narrower: a
hand-edited or externally produced record, `json.loads` accepting `NaN`/`Infinity`
literals by default (catalog :486), or the 0-dim-tensor case where `check_finite`'s
fall-through lets a NaN past the guard in the first place (catalog :110).

So the status is "the guard has no floor", not "the round-trip is broken today" —
and the Phase-A lesson is unchanged and stronger than "type the payload": **a
diverged epoch needs a version-gated absence encoding on the wire, or the typed
round-trip cannot be relied on** — and the construction guard must have no
fall-through branch. That is `silent-default-elimination.md`'s validity-mask
discipline and its fail-loud-parsing rule, both needed, neither optional.

---

## D. Where the demo already satisfies a Simic invariant

This is as valuable as the gaps and easy to under-report. Every item below is
verified in the catalog, not inferred from a name.

### D.1 INV-15 and INV-16 — the mandatory no-op, satisfied *twice over and differently*

These are two different claims and the demo satisfies them by two different
mechanisms. Keeping them apart matters.

**INV-15 (no-op availability — the measurement frame):** *"every admission and
continued-tenancy case includes a measured no-intervention alternative."* The demo's
no-op is a **real, executed arm**, not an assumed zero. `run_fan` runs `"noop"`
through the *identical* `run_arm` → `_run_span` → `train_one_epoch` path as every
seed arm (:1381); its reward comes from `end_state_R(ctx.curves_val)` (:1341); it is
the first element of the returned `arms` list (:1390). It is measured **and** it
doubles as the harness twin (:1382–1388), so the demo gets integrity verification
out of the same execution that gets it the baseline.

**INV-16 (no-op convention — the utility frame):** *"Isperia assigns no-op policy
utility exactly zero."* Satisfied structurally by the lift definition: `lift`
is `r_test - r_noop_test`, so the no-op's own lift is identically zero, and
`lift = 0.0` is written explicitly for a never-germinating comparator with the
reason inline (`# never-germinate = 0`, :3587).

The demo therefore gets right the thing that is easiest to get wrong: the no-op is
**measured** (a real number from a real run) *and* **conventionally zero** (its
policy utility), and those are not the same statement.

### D.2 INV-31 and INV-36 — Urborg-style complete history

*"structural rejects, compilation failures, QA failures, adjudication rejects, no-op
decisions and abstentions are stored"* — and *"corrections create new records
rather than rewriting causal history."*

- `void_event` is a first-class record kind (`RECORD_KINDS`, :1426). A base
  divergence records one carrying `diverged_at` and the skipped fan epochs
  (:2382–2414); `run_refan` records a `refan_k`-distinct one rather than crashing
  (:2437–2467).
- **Diverged arms are retained as results, not dropped.** `status="diverged"` plus
  the sentinel `cfg.diverged_r` (:1343–1345), and diverged arms still reach training
  examples (:1841–1842).
- **Rejected pools are retained.** Every fan records all four seed arms plus the
  no-op plus (1-in-10) the null-seed arm — the *whole pool*, never winners-only.
- **Every preflight attempt is counted**, with `iteration` derived from store state
  (:2980).
- **Append-only under pressure.** `--void-preregistration` writes a permanent
  `void_event` (:3437–3461) rather than deleting `eval_results.json`. Re-rolling is
  possible; it is never invisible.

### D.3 INV-35 — Tamiyo isolation, genuinely by construction

*"disconnecting Tamiyo cannot alter training outcomes."* **Re-verified against the
current 432-line sidecar, not inherited from the catalog** (see §E.7): the module
declares **zero** `@semantic` and **zero** `semantic_const` — grep returns a count of
0 — so `config_hash` is genuinely untouched. The import edge is **one-way**: the
sidecar imports `kernel_demo`, never the reverse, and `kernel_demo.py:29` states the
intent. Nothing in `kernel_demo.py` references matplotlib, so the demo runs on a box
without it.

**One refinement since the catalog.** The claim "no repository caller at all" is now
false in a way that *improves* the picture: `tests/unit/kernel_demo/test_plots.py`
(239 lines) imports it. That is a test caller, not a production one — the demo's
execution path still never reaches the sidecar, so the isolation property is intact
and the module is no longer unverified. The direction that matters is unchanged.

The sidecar also now imports `end_state_R` and `AGREEMENT_MARGIN` (plots :28) rather
than duplicating their definitions. Worth noting precisely: this *deepens* the
sidecar's dependency on the semantic surface without breaching isolation — a change
to `end_state_R` changes the plots, which is correct, because the plots should
follow the kernel's definition of reward rather than invent a second one.

The isolation is real. See §E.7 for the one place the *witness* nevertheless
acquires an opinion.

### D.4 INV-37 — blinding by construction

Covered in C.1 and worth restating as an invariant satisfaction: `TelemetryRecord`
(:358–369) has **no provenance field to strip**, so no consumer can accidentally
read one. The blind view is the only view. `--selftest` step 6 (:2154–2163) greps
the field names to keep it that way. Under `blinding-by-construction.md` the demo
has layer 1 (the view type) solidly and a weak layer 3 (a grep, not a canary with a
positive control).

### D.5 INV-32 — grouped statistics, closed at every layer

*"branches from one base trajectory never cross splits or inflate independent sample
counts."* Closed four separate times:

- **Storage:** `train_tune_split` (:1540) is a deterministic function of
  `episode_seed`, stamped once per episode *before any fan exists* (:2339) and
  inherited by every fan (:2367). One base trajectory structurally cannot straddle
  train and tune. Refans never assign train/tune at all (:2447, :2478).
- **Learning:** `train_policy` reads the recorded field verbatim and never
  re-derives (:1944–1946); minibatch sampling draws `torch.randint(len(train_ex))`
  (:1957), so tune examples are **outside the index space** — the wall is enforced
  by an index bound, not a convention.
- **Gates:** `_first_fans` (:2522) takes the lowest-`fan_epoch` fan per episode, one
  unit per trajectory, explicitly against pseudo-replication (:2522–2523); gate 2's
  probe holdout is by episode (:2592).
- **Statistics:** the money-chart permutation unit is the **episode** — `remap`
  moves every grid point of an episode together (:2029–2030) and it raises if one
  episode carries two pathology labels (:2022–2023). The falsifier CI and the
  agreement MDE use the episode count, not the grid-point count (:3693–3698,
  :3814–3816).

### D.6 INV-04 and INV-06 — parity and common future, both structural

**INV-04 (mainline–branch parity):** `_run_span` (:1236) is *deliberately the single
implementation shared by base and arms*, with the reason stated at :1243–1245:
*"base/twin drift is structurally impossible."* Parity by construction, not by
discipline — the strongest available form.

**INV-06 (common future):** see C.5. Enforced by data structure, not by re-seeding.

### D.7 INV-05 and INV-24 — replay and fail-closed compatibility

**INV-05:** `run_replay` (:3925) refuses on env keys, `config_hash`,
`frozen_block_hash`, `manifest_hash`, `data_split_id` and `n_train`, then localises
in causal order — pathology derivation → future derivation → seeding → arm status
flip → kernel selection (:3970–4000). `REPLAY_REFUSAL_KEYS` (:952) promotes exactly
seven of ten env facts, and **each demotion carries a written reason at the point of
exclusion** (:954–956, :980–982) rather than being silent. The comparison is
fail-closed: `rec.env.get(k) != live_env.get(k)`, so a record carrying only
`{"git_rev": …}` reads `None` for all seven and is **refused**, not admitted
(:3943).

**INV-24 (typed compatibility fails closed):** `decode_record`'s `schema_version`
equality check (:1567–1573), with the governing policy in the error text.

### D.8 INV-38 — failure visibility; no silent fallback

The project's silent-zero scar taken seriously, in eight places:

| Mechanism | Evidence |
|---|---|
| Direct subscript, never `.get()`, on the decode path | `d[key]` at :1814 — a missing key raises `KeyError` |
| `bool` rejected as a number (it subclasses `int`) | `_as_float` :1805 |
| `None` rejected on the numeric path | `_as_float` :1806 |
| 3-vector arity validated before conversion | :1816–1820 |
| Non-finite logits raise rather than reading as restraint | :1774–1777 — **`decide_live` only. The deployed twin at :3397–3400 does NOT hold; see §E.8.** |
| An undefined conditional mean is `None`, never `0.0` | `when_contrast` :3305–3307 |
| No measurement is a gate **failure**, not a pass | gate 5 :2702–2703; gate 3 :2652–2653 |
| A resumed record with a malformed payload raises rather than defaulting to "never germinated, lift 0" | :3524–3531, with the scar named in the comment |
| A stray `CUBLAS_WORKSPACE_CONFIG` is refused, not overwritten | :919–924 — *"a tolerated stray value is a silent Class-1 relaxation"* |

### D.9 The codebase caught a silent-default class eight reviewers missed — and left one open in the same function

Worth recording as a positive in its own right, because it is evidence about the
project's discipline rather than about any one invariant.

The sidecar's review-fix pass (`853e9ef`, `aa86388`) closed the two silent-default
findings this analysis reported — and then closed a third that **nobody in the
analysis had found**. `_finite_points` / `_gapped` (plots :65–90) keep the
**original epoch index** with each value and emit `nan` at dropped positions, so
matplotlib leaves a visible gap and the x axis stays true. The reason is stated
inline: `curve_val` entries are `null` wherever `_sanitize_json` saw a non-finite
number, and *"dropping them and replotting at contiguous x would silently relabel
the epoch axis."*

That is exactly the class this document is about — an absence quietly becoming a
plausible value, here by shifting every subsequent point one epoch left — and it was
caught by the author, in the witness layer, unprompted by any of the eight explorer
entries. `_spike_then_crash` (plots :93–102) carries the companion discipline in its
comment: it consumes the **finite** values while the x axis keeps the original
indices, and the two views *"are deliberately different and must not be merged."*

#### And the same function carries an open instance of the pattern this document is about

**This is the more useful half, and I would have missed it** — the contract audit
(finding 11) caught that the catalog independently flags `_finite_points` for a
silent default *in the very function §D.9 holds up as the exemplar*.

`_finite_points` (plots :72–79) keeps a value only `if math.isfinite(f)`, with **no
`else`**. A JSON `null` is skipped deliberately (that is the gap-preserving behaviour
praised above), but a **live `inf`** is skipped by the same branch — and rendered as a
gap **indistinguishable from a recorded null**. Three lines away, `require_number`
(plots :48–51) treats exactly that condition as proof the producer changed and
**refuses**. Two validators in one module, opposite policies on the same input class,
and the one that loses information is the one on the rendering path.

Why this belongs in *this* document rather than a bug list — it is the document's own
signature finding, recurring:

| This defect | Where the document already makes the same point |
|---|---|
| A type-dispatch chain with no `else: raise`, so an invalid value falls through silently | **§C.1** — `check_finite` (:372–381) validates `float`/`tuple`, passes `int`, and has no `else`. Escalated to **Phase-A recommendation 1** |
| Two distinct absences (`null` vs live `inf`) collapsed into one rendering | **§C.13** — the wire lesson: a diverged epoch and an absent one become the same token. Here it recurs at the **render** boundary |
| Two validators with opposite policies on one input class | **§E.3** — the two telemetry encoders, coupled by comment only |

Phase-A blast radius is **low** — the witness layer becomes no Leyline record. But the
finding *strengthens* recommendation 1 rather than qualifying it: **the fall-through
pattern recurs independently, in the same codebase, in the same commit that closed
two other instances of it.** A defect class that reappears while its author is
actively fixing that class is precisely the kind that must be closed by construction
rather than by attention.

So §D.9 holds both: the epoch-index preservation is a genuine and unprompted closure,
**and** the same function carries an open instance of the pattern. The relevance to
Phase A is not the fix but the reflex — the silent-default class is already what this
author reaches for first, *and reaching for it by hand is demonstrably not sufficient*.
§F's recommendations are asking for that reflex to be made **structural** rather than
repeated.

### D.10 A declared semantic subset with a completeness gate

Not an INV-nn, but the central discipline of `canonical-identity.md`, and the demo
demonstrates it: `@semantic` (:60) and `semantic_const` (:71) register at **import
time only** (both carry the same prohibition against call-time registration, traced
to a named historical defect at :61–63); `_NON_SEMANTIC` (:87) is an explicit
opt-out register mapping symbol → *stated reason*; `config_hash` (:231) sorts both
streams so the digest is order-independent. **And it has a completeness gate**:
`tests/unit/kernel_demo/test_derive.py:93` walks `vars(k)` and fails on any public
class or function that is neither registered nor opted out.

That is a declared semantic subset with mechanical enforcement — 109 registered
objects against 11 opt-outs. The gate's limits are known and recorded: it filters to
`isclass or isfunction` (:100) so module constants are uncovered, it skips
`_`-prefixed names (:99) so `_git_rev`/`_worktree_clean` escape, and `FROZEN_FIELDS`
has no completeness test of its own.

---

## E. Findings translated into contract terms

The architecture analysis found real defects. Read as contract failures, they map
cleanly onto the `axiom-contract-engineering` catalogue — which means Phase A can
close them by construction rather than by review. Catalogue entries are cited as
**[#n]**.

### E.1 The headline: `run_eval` collapses QA, judgement and revelation — in embryo

**This is the most instructive item in the document.**

`run_eval` (:3425) is ~400 lines carrying seven responsibilities: resume
bookkeeping, the comparator execution loop, the frozen eval grid, refans, six
statistical computations, results assembly, and the atomic write. In domain terms it
**tests** (executes the comparator episodes — Tolaria under Jin-Gitaxias's plan),
**certifies** (computes the p-values, the agreement, the money chart, the falsifier
— Jin-Gitaxias), **judges** (applies `verdict()`, :3820 — Isperia), and **reveals**
(prints the tables — Tamiyo). Four authorities, one function.

INV-18 forbids exactly this: *"Jin-Gitaxias cannot issue admission or maintenance
warrants; Isperia cannot execute or alter tests."* The sentence test in
`02-constitution.md#54-the-sentence-test` lists *"Isperia reran the branch with a
more favourable batch"* as a sentence that should trigger review — and `run_eval`
is the function in which that sentence would be *easy to write*.

**The mechanism is what makes it instructive, and it is a contract mechanism:**

> Because test, judge and reveal occupy one function, **there is no record at the
> boundary between them — and an authority boundary with no record cannot be
> verified.**

The observable consequence is coordinator-verified and precise. The fan path is
verified **twice** — `TwinDivergence` at runtime (:1382–1388) and `--replay` post
hoc. The headline lift path is verified **neither** way:

- **No twin.** `run_eval` never calls `take_snapshot`, `run_base`, `run_arm` or
  `run_fan`. The baseline is an independently constructed episode
  (`noop_ctx = make_episode(...)`, :3512) trained through the full horizon in a
  plain loop; each comparator builds *another* independent episode from the same
  seed (:3542). `lift = r_test − r_noop_test` (:3587) therefore differences **two
  separately executed episodes**, matched only because `make_episode` is
  deterministic from `es`. Nothing hashes the two prefixes and compares them.

  *Precision, corrected from an earlier draft:* that draft claimed a grep over
  :3425–3660 for `state_hash|host_init|host_hashes|TwinDivergence` "returns no
  comparison at all". **That sentence was false** — `TwinDivergence` **is** present
  at :3637. It belongs to the eval **grid** path, which runs through
  `run_collection_episode` → `run_base`/`run_fan` (:3624) *with* the twin machinery,
  exactly as the coordinator's precision note says. The accurate claim is narrower
  and still sufficient: **within the comparator loop (:3512–3588) there is no
  snapshot, no twin, and no prefix comparison**, and the only `host_init` tokens in
  the whole range are two empty-string literals (:3454, :3606).
- **Structurally excluded from `--replay`.** `run_replay` refuses anything that is
  not a fan: `if rec.kind != "fan" or rec.fan_epoch is None: raise` (:3957–3958).
  `run_eval`'s comparator loop writes `kind="policy_run"` with `fan_epoch=None`
  (:3592, :3597). **The headline comparator records fail the replay guard twice
  over** — wrong kind *and* null fan epoch.

**Precision note, per the coordinator's adjudication (00-coordination.md, 08:52):**
this applies to `policy_run` **comparator records specifically**. The eval *grid*
fans remain `kind="fan"` and **are** replayable — they go through
`run_collection_episode` → `run_base`/`run_fan` (:3624) with the full twin and
null-seed machinery. Do not overstate this as "eval is unreplayable." Scope: two of
five verdict booleans are affected (`lift_positive`, `beats_schedule_only`,
:3320–3321); `agreement_beats_null`, `money_chart` and `falsifier_collapses` all
rest on properly matched branches.

Note also that the supporting evidence for the assumption is strong — explorer 3
verified zero global-RNG consumption across all 80 pathology × seed × stage
combinations; explorer 1 verified no dependence on the global stream; explorer 2
verified `CommonFuture` is precomputed per-episode from `es`. So this is **an
unverified assumption, not a known error**. The severity is: *the one place where a
codebase that otherwise proves its claims asserts one instead.*

**In contract terms:** split `controls/evaluate.py` (execution, :3507–3646) from
`isperia/statistics.py` (:3651–3818) from `isperia/adjudicate.py` (`verdict`) from
`tamiyo/report.py` (tables) — the seam is clean, with no shared mutable state beyond
`grid`, `per_comp` and `merged`. **The moment those are four modules, a record must
cross each boundary — and a record that crosses can be hashed, replayed and
refused.** The fix for the headline gap then follows for free: `policy_run` carries a
real `host_init_hash` (C.11), the boundary record is a `BranchResult`-shaped thing
that `--replay` accepts, and the assumption becomes a check.

### E.2 Two implementations of one resolver — **[#10] dual sources of truth**

`decide_live` (:1754) vs the inline twin (:3562–3573). Full treatment in C.12. The
catalogue framing: one schema — here, one *resolution rule* — defined in two places
that drift independently, with the drift already begun (the window guard, :1763 vs
:3551). The sheet is `deterministic-resolution.md`; the fix is one resolver with
`resolver_version` on its output.

### E.3 Two encoders for one canonical record — **[#10] dual sources of truth**

`record_to_vector` (:397) vs `_telemetry_vector_from_dict` (:1811). Full treatment
in C.13. This is the clearest **silent-failure class** in the codebase: a desync
passes certification with every gate green, corrupts gate 2's own inputs, and
permutes the feature space between calibration and inference. The root cause is the
untyped payload (`FanRecord.telemetry: list[dict[str, object]]`, :1452), and the
fix requires a wire-level absence encoding for divergence as well as typing.

### E.4 `host_init_hash=""` — **[#1] silent default**

Full treatment in C.11. Absence encoded as a value of the field's own type, in the
one field that would let an auditor verify INV-20's semantic-identity binding on the
headline path.

### E.5 The re-freeze decoupling — **[#11] unversioned policy**

Full treatment in C.10. `manifest_hash` (:2909) hashes measured, run-varying values,
so it is a run identity being used as a policy identity; re-freezing on the same
commit silently decouples the calibration from the records it calibrates, with
nothing on the train path detecting it. Highest-reachability defect in the analysis.

Its sibling, **[#12] silent definition edits**: `plan_authored_constants` (:2906)
presents `fsync_every` for owner sign-off while neither hash binds it.

And in the witness layer, **[#11] again**: `SPIKE_CRASH_MARGIN = 0.05`
(`kernel_demo_plots.py:21`) does not merely render a recorded number — it
**classifies** an arm as "spike-then-crash" and prints that classification into a
figure legend (plots :41). The threshold is plan-authored, not in `Config`, not in
the freeze manifest, not hash-bound. A reader citing a "spike-then-crash" arm is
citing an uncertified criterion that can be edited with no hash moving and no replay
refusing. Tamiyo *"must not steer the system through the act of observing it"* — a
witness that classifies has acquired an opinion, and here it is an unversioned one.

### E.6 `decode_record`'s tolerant reader — **[#2] tolerant readers**

`kwargs = {f.name: data.get(f.name) for f in dataclasses.fields(FanRecord)}` (:1574)
fills any absent field with `None` **at the same `schema_version`**. With
`SCHEMA_VERSION = 1` (:55) there are zero additive-evolution cases today, so the
tolerance is currently **pure hazard with no beneficiary**: a field-dropping record
decodes without complaint, a `None` `split_role` drops it from the training filter
(:1674) silently, and a `None` `episode_seed` surfaces only as a `TypeError` in the
merge sort key (:1648).

This one is subtle and worth stating carefully, because the *versioning* gate two
lines above it (:1567) is exemplary. The tolerance is deliberate — the error text at
:1570 explains it (*"the decoder fills absent new fields with None"*) as the
mechanism that makes additive evolution work. The contract-engineering objection is
not to the policy but to its **scope**: the leniency is unconditional rather than
version-gated, and it applies to *required* fields as well as future additive ones.
`silent-default-elimination.md`'s answer is a required-field non-`None` check after
construction, which costs one loop and closes it entirely.

### E.7 The witness layer — **three defects closed, seven contract-shaped concerns still open**

> **Staleness correction, since resolved upstream.** An earlier version of the
> catalog's Plotting Sidecar entry described a 151-line file.
> `experiments/kernel_demo_plots.py` is now **432 lines** — rewritten by `853e9ef`
> (*"plotting sidecar refuses to invent data (review fix pass)"*) and finished by
> `aa86388` (*"an empty tune curve is a skip, not a crash"*). I re-read the current
> file rather than inherit the older findings, and **two of the three silent-default
> findings are closed.** The catalog has since been re-merged (07:34, against
> `aa86388`) and now carries a version anchor; it is no longer stale, and this note
> is retained only to explain why the findings below differ from the entry as first
> written.

**Closed — `.get()` defaults on headline numbers.** Replaced by `require_number`
(plots :38–52), which uses direct indexing and raises `PlotDataError` on a missing
key, a non-number, a `bool`, **and** a non-finite value — with the reasoning in the
comment: *"Direct indexing, not `.get(<default>)`: a wrong or truncated results file
must fail here rather than become a chart of zeros"* (plots :39–40). `require_dict`
(plots :55–62) does the same for sections.

**Closed — `per_seed[n] or [0.0]`.** Gone. The module docstring now states the rule
directly: *"this module never invents a datum. A missing required field is an error,
not a zero; … an absent measurement is labelled absent rather than plotted at the
origin"* (plots :7–11). `_finite_points` / `_gapped` (plots :65–90) go further than
the original defect required — they preserve the **original epoch index** with each
value and emit `nan` at dropped positions so matplotlib leaves a visible gap, with
the reason stated: dropping nulls and replotting at contiguous x *"would silently
relabel the epoch axis."* That is a silent-default class the review found and closed
that nobody had reported.

**Closed — no test coverage.** `tests/unit/kernel_demo/test_plots.py` now exists
(239 lines).

> **Under-inheritance correction (audit).** An earlier version of this section named
> `SPIKE_CRASH_MARGIN` as the sole survivor. The re-done catalog entry carries
> **eleven** open concerns. Both passes were done against the same file at
> `aa86388` roughly two hours apart and neither absorbed the other — the same
> failure mode as the original staleness, inverted. The ones that instantiate a
> catalogue entry are pulled in below; the remainder (test-suite gaps,
> `--include-refans` labelling, partial-output staleness) are real but are witness-layer
> operational issues rather than contract shapes, and stay in the catalog.

**Still open — `SPIKE_CRASH_MARGIN` remains an unversioned classification threshold
— [#11].** It is still module-local at plots :30 and still *classifies* rather than
renders: `_spike_then_crash` (plots :93–102) returns `max(vals) > end_state_R(vals) +
SPIKE_CRASH_MARGIN`, and that verdict reaches a figure legend. It is not in `Config`,
not in the freeze manifest, and not hash-bound, so a reader citing a
"spike-then-crash" arm is citing an uncertified criterion that can be edited with no
hash moving and no replay refusing. Tamiyo *"must not steer the system through the
act of observing it"* — a witness that classifies has acquired an opinion, and this
one is unversioned.

The fix is now visibly cheap, because the same commit demonstrates the pattern: the
sidecar already imports `AGREEMENT_MARGIN` — **a `semantic_const` (:3256)** — and
`end_state_R` from `kernel_demo` (plots :28), reusing hash-bound definitions instead
of duplicating them. `SPIKE_CRASH_MARGIN` is the one classification constant that did
not make that move.

**Also still open, and each instantiates a catalogue entry:**

| Open concern | Evidence | Catalogue entry |
|---|---|---|
| **The money chart hardcodes a pre-registered verdict rule the kernel owns.** Panel 2 correctly draws `majority + AGREEMENT_MARGIN` from the imported `semantic_const`; panel 1 hardcodes `axhline(3, label="required matches")` and `ylim(0, 4.2)`, duplicating the `>= 3` rule `verdict()` owns at :3323 and the 4-pathology denominator. A change to the money-chart rule moves the verdict and leaves the chart's own reference line stale — **and the chart is the artifact a reader trusts.** The author demonstrably knows the right pattern, having applied it one panel over | plots :259–260 vs :265 | **[#10] dual sources of truth**, and **[#11]** — a policy constant duplicated in the witness layer |
| **`_finite_points` silently drops a live `inf` while `require_number` refuses one** — two validators, opposite policies, one module | plots :78 vs :48–51 | **[#1] silent default** — see §D.9, where this recurs as the document's own signature finding |
| **The population-refusal invariant holds on two of three axes.** Mixed namespace and mixed manifest are refused; **mixed `split_role` is silently pooled** when `--split-role` is omitted. A `--namespace train` store legitimately holds both `train` and `tune` (`train_tune_split`, :1540), and `tune` is the held-out selection split — so pooling them is the fabricated aggregate the module's own comment says it guards against | plots :135–138 vs :148, :151 | **[#1]**, and it breaches §D.5's grouped-statistics discipline at the render boundary |
| **The mixed-manifest guard excludes `manifest_hash=None` from its own ambiguity check**, so a population mixing hashed and un-hashed records reads as one generation and is pooled. Latent only because preflight records also carry `seed_namespace="preflight"`, so the namespace guard happens to catch the realistic case — **correct by correlation, not by construction** | plots :150 | Same shape as §C.2's `fan_identity` omitting `seed_namespace`: a guarantee that lives one layer away and is undocumented where it is relied on |
| **`plot_alpha_beta` refuses on a legitimate absence its sibling skips.** An all-diverged population has no non-empty logs — a state the kernel names explicitly (`_all_arms_diverged`, :2515). `plot_tune_curve` returns and skips; `plot_alpha_beta` aborts the whole run | plots :229 vs :297 | Absence-encoding inconsistency — two policies for one class of legitimate absence |
| **`plot_manifest.json` records what was selected but not what drew it** — no `config_hash`, no sidecar revision, no `SPIKE_CRASH_MARGIN`. It cannot answer *"which plotting code, with which thresholds, drew this PNG"* — precisely the question the kernel's identity machinery answers for every other artifact | plots :400–427 | **[#11]**, and a canonical-identity gap: a provenance record that does not bind its producer |
| **No exit-code discipline.** `main` does not catch `PlotDataError`, so a refusal is an uncaught traceback rather than a diagnostic, and no test asserts exit status | plots :367 | Mirrors §C.8's finding that `eval` exits 0 regardless of verdict |

**New, and it bears on §F.2.** The sidecar now refuses rather than pools on two axes:
several seed namespaces without `--namespace` (plots :148–149), and **several manifest
generations without `--manifest`** (plots :150–152). It also emits its own
`plot_manifest.json` provenance record. That makes it a genuine `manifest_hash`
consumer — and per §C.10's finding-10 table, one asking a **calibration** question, so
it is among the three that must be **retargeted** to the policy hash under the split.

### E.8 The deployed finiteness guard admits the case its own comment forbids — **[#1] silent default, in shipped code**

**This is the only finding in this document that is a defect in the demo's running
code rather than in a contract shape — and it is the sharpest thing here.** It was
found by the contract audit after an earlier draft of §D.8 wrongly certified the two
guards as "mirrored". They are not. **Verified by execution:**

| | `decide_live` (:1774) | `_query_dicts` (:3397) — the **deployed** path |
|---|---|---|
| What is checked | `torch.isfinite(p_logit)` — the **raw logit** | `math.isfinite(p)` — **after** `sigmoid` (:3394) |
| Given `p_logit = -inf` | `isfinite → False` ⇒ **raises**, correct | `sigmoid(-inf) = 0.0`, `isfinite(0.0) → True` ⇒ **admits** |
| Downstream | — | `p > 0.5` is `False` ⇒ **reads as restraint, lift exactly 0** |

The comment sitting directly under the deployed guard (:3398–3399) states the
prohibition it fails to enforce:

> *"NaN > 0.5 is False: a non-finite checkpoint would silently read as restraint
> (lift exactly 0) on every query. Loud, never that."*

Because the check runs **after** the squashing function, a `-inf` logit produces
exactly the silent restraint the comment forbids. The same applies to the WHICH head:
`pi = softmax(seed_logits)` (:3395) maps a `-inf` entry to a finite `0.0`, so
`isfinite(pi).all()` also passes — verified: `softmax([-inf, 1, 2, 3])` returns all
finite values.

**Why this matters beyond one guard.** §C.8 records that `train_policy`'s checkpoint
selector fails open if the *first* tune evaluation is `NaN` (`score < best_score` is
`False` for `NaN`, so `best_state` stays `None` and the final policy is saved). The
stated mitigation for that was "any query against such a checkpoint raises at :1777
or :3400". **Half that mitigation does not exist.** A checkpoint that saturates its
WHEN logit to `-inf` is saved, passes the deployed guard, and reports lift exactly
0 for every episode — indistinguishable from a policy that correctly learned
restraint.

**Contract lesson (this is why it belongs in §E, not just a bug list):** a finiteness
guard is a **validity check on a contract field**, and it must run on the field the
contract carries — the logit — not on a derived presentation of it. Checking after a
transform that maps the invalid domain into the valid range is the numeric form of a
tolerant reader. `silent-default-elimination.md`'s fail-loud-parsing rule applies to
computed values, not just parsed ones.

*Recommended fix:* check `torch.isfinite(p_logit).all() and
torch.isfinite(seed_logits).all()` **before** the sigmoid/softmax at :3394–3395 —
i.e. make the deployed path do exactly what `decide_live` already does. Which is
recommendation §F.3 arriving from a second direction.

---

### E.9 The kind/payload correspondence — **[#13]-adjacent: a contract that cannot be tested**

One flat schema for six kinds (C.2) with four kind-conditional nullable slots and no
validation that a kind populates the right ones. There is no assertion to write,
because there is no rule expressed in the type. A discriminated union makes the
whole class of test unnecessary — which is the point of
`contract-first-boundaries.md`'s "illegal states unrepresentable".

The same shape appears in `arms[].name`, which has no closed vocabulary while
`kind`, `seed_namespace` and `split_role` do (:1426–1428, checked :1501–1506) — so
`name = chosen or "noop"` (:3608) can collide a comparator's non-germinating arm
with a genuine measured no-op.

---

## F. What Phase A should take from this

Phase A is Namespec, Leyline contracts and dependency boundaries
(`programme/phases.md`), and it comes **first**. Ranked by what would cost most to
get wrong, with the demo evidence for each.

---

**1. Type the payload all the way to the wire — and give divergence a wire
encoding, because typing alone is not enough.**

*Evidence:* `FanRecord.telemetry: list[dict[str, object]]` (:1452) forced a second
telemetry encoder into existence (:1811) whose divergence from the first is checked
by nothing and would corrupt calibration silently (C.13, E.3).
`FanRecord.arms: list[dict[str, object]]` (:1451) admitted two incompatible arm
shapes (:2376 vs :3608) that four `kind` filters hold apart by coincidence (C.3).

*But:* the typed round-trip cannot be relied on in either direction.
`_sanitize_json` (:1551) maps non-finite → `None`, so on the wire a diverged
measurement and an absent one are the same token; and `check_finite` (:372–381) has
no `else: raise`, so reconstruction would build a `TelemetryRecord` with
`train_loss=None` in a field annotated `float` without objecting. **Not a live
defect** — `__post_init__` (:375) keeps non-finite telemetry from ever being
constructed, so the lossy branch is unreachable from the normal path; the guard
simply has no floor under a hand-edited record, a `NaN` JSON literal, or the
0-dim-tensor case (C.13).

*Phase-A action:* `TelemetryEnvelope` and `BranchResult` must round-trip as
**themselves**, with an explicit `validity_mask` (or a tagged union per field) that
distinguishes *measured* / *unmeasured* / *diverged*, and a construction guard whose
type dispatch has no fall-through branch. Sheets: `silent-default-elimination.md`,
`contract-first-boundaries.md`.

---

**2. Split policy identity from evidence identity in the freeze manifest.**

*Evidence:* `manifest_hash` (:2909) hashes `gate_results` detail, `det_mode_cost`
and `concurrency_factor` — all measured and run-varying — so re-running
`preflight --freeze` on the *identical commit* yields a different hash,
`freeze_manifest` overwrites unconditionally (:2914), and `run_train` reads
calibration from manifest B while training on records collected under manifest A
(:3343–3354) with nothing detecting it (C.10, E.5). Highest reachability in the
analysis: both freeze preconditions are met by simply re-running preflight.

*Phase-A action — **two records and a consumer-retargeting pass***. The records: a
**policy record** (normalizer, temperatures, thresholds, `spec_rev`) content-hashed
and changed only through a recorded lifecycle event; an **evidence record** (gate
results, measured costs) recorded beside it and referenced by it, not part of its
identity. Then re-point **every** consumer at the identity its own question depends
on — a run-identity question keeps `manifest_hash`, a calibration question moves to
the policy hash. Per the audit (finding 10), three of the four current consumers ask
calibration questions, so **the split alone fixes the train path and leaves the
report path and the double-count broken**. The retargeting is not optional polish;
it is half the fix. Table and reasoning in §C.10. Sheets:
`versioned-policy-parameters.md`, `definition-lifecycle.md`.

*Confidence note:* this was flagged in an earlier draft as the recommendation most
likely to be wrong. **That flag is withdrawn on evidence.** Pre-registration is
enforced by `frozen_block_hash` + `config_hash` at :3343 and :3463; `manifest_hash`
is consulted by no enforcement site, and its three real consumers all want a run
identity and all survive the split. **The split is not a risk to the property — it
is the repair.** Full reasoning and the occurrence audit are in §C.10. When doing it,
sort `plan_authored_constants` (:2892–2907), which currently mixes policy constants
with operational knobs including the unhashed `fsync_every`.

---

**3. One resolver, versioned, with `resolver_version` on its output.**

*Evidence:* `decide_live` (:1754) has zero production callers; the deployed twin
(:3562–3573) is untested and already differs on the window guard (:1763 vs :3551);
the author asks for manual lockstep in a comment (C.12, E.2). And `decisions`
(:3588) records no resolver version at all.

*Phase-A action:* Leyline's `GrowthRequest` already mandates `resolver_version`
(`05-leyline-contracts.md#94-growthrequest`) — enforce it as the pattern for every
derived record, and let the test suite pin the *deployed* function by construction
(there being only one). Sheet: `deterministic-resolution.md`.

---

**4. Absence is a type, never a sentinel value.**

*Evidence:* `host_init_hash=""` (:3606) in a field typed `str` (:1449) — the one
field that would verify INV-20's binding on the headline path (C.11, E.4). And
`r_noop_test` falling back to `cfg.diverged_r = 0.10` with no `status` beside it, so
a diverged baseline is indistinguishable from a poor one (C.9).

*Phase-A action:* no measurement field on a Leyline record may be inhabited by a
sentinel. Tagged unions or validity masks; the type makes `""` and `0.10`-as-failure
unrepresentable. Sheet: `silent-default-elimination.md`.

---

**5. One record class, one producer — use a discriminated union, not nullable slots.**

*Evidence:* `make_fan_record` (:1473) is the sole constructor for six kinds
(:1426) with four kind-conditional nullable slots and no validation that a kind
populates the right ones; a `fan` with `gate_results` set constructs cleanly
(C.2, E.8).

*Phase-A action:* the HLD already prescribes this — `BranchResult`, `QualityReport`,
`AdmissionDecision` and `EventEnvelope` are four record classes with four producers
(`05-leyline-contracts.md`). Keep them four. The demo's *validation* discipline
(closed vocabularies whitelisted in the sole constructor, :1501–1506) is worth
carrying forward verbatim. Sheet: `contract-first-boundaries.md`.

---

**6. Certification records need a severity lattice, not a boolean.**

*Evidence:* `GateResult.ok: bool` (:2503) has no warning level, so gate 7 had to be
encoded as an unconditionally-passing blocking gate with `remedy="report-only"`
(:2755), and gate 8 packs a third meaning (`"skipped (GPU-only)"`, :2761–2762) into
the same field. **"8 gates passed" means seven** (C.7).

*Phase-A action:* `QualityReport`'s `hard_defects[]` / `soft_warnings[]` split
(`05-leyline-contracts.md#914-qualityreport`) is the right shape and the demo
demonstrates the cost of not having it. **Also take `remedy` forward** — a QA record
that names the licensed response to its own evidence has no HLD analogue and is a
genuinely good anti-p-hacking device (gate 5's *"tau, lambda, seed_lr — never the
sampler"*, :2688).

---

**7. Keep blinding by field absence — and upgrade the grep to a canary with a
positive control.**

*Evidence:* `TelemetryRecord` (:358–369) has no provenance field to strip; the blind
view is the only view. Enforcement today is one `--selftest` grep over field *names*
(:2154–2163).

*Corrected framing (§C.1, critical audit finding):* **`TelemetryRecord` is the
precursor of the blinded projection, not of `TelemetryEnvelope`.** An earlier draft
of this lesson said "keep layer 1 exactly as the demo has it" while treating it as
the envelope — which would have produced an envelope with no `observation_id`, no
`host_state_id` and no provenance, making **INV-08's fail-closed reconciliation
unimplementable** and leaving the blinded view undesigned. Nissa's own mandate is to
*"normalise and **attach provenance**"* (`02-constitution.md:274`); INV-37 constrains
**views**, not the envelope.

*Phase-A action:* build **two** record classes and the function between them.
1. `TelemetryEnvelope` **with** provenance and full identity — published to Ugin,
   Aurelia, Momir, Urborg, Tamiyo (`05-leyline-contracts.md:46`).
2. A **blinded projection** for Jin-Gitaxias and Isperia, whose schema is
   `TelemetryRecord`-shaped: the forbidden fields are *absent*, not redacted.
3. An **allowlist** projection function — fields named in, never a deny-list — so a
   future envelope field is excluded by default. This is the layer the demo cannot
   have, because its blind record is *authored* blind rather than *derived* blind.

Then add layer 3, a canary test **with a positive control** — the demo's grep has
none and would pass if it were silently broken. Sheet:
`blinding-by-construction.md`.

---

**8. Make INV-02 mechanical on day one — the demo cannot demonstrate it, and that is
the point.**

*Evidence:* the dependency direction is the one Leyline invariant with **no analogue
at all** in the demo, because a single file has no import graph to constrain. The
split line between `leyline/records.py` and `urborg/store.py` (section B) is where
it becomes testable.

*Phase-A action:* `import-linter` (or equivalent) configured before the second
package exists, with `src/simic/leyline/` as a leaf that may import stdlib and torch
and **nothing under `src/simic/`**. A gate written after the violation exists is a
migration; written first it is free. Sheet: `dependency-direction.md`.

---

**9. Extend the `@semantic` completeness gate to constants and config fields — and
prefer schema identity over source-text identity.**

*Evidence:* `test_derive.py:93` is a real completeness gate over 109 registered
objects and 11 opt-outs (§D.10). Its limits are known: it filters to
`isclass or isfunction` (:100) so `semantic_const` registrations are ungated;
`FROZEN_FIELDS` (:188–223) is a hand-maintained list parallel to `Config` with no
completeness test; `_`-prefixed names are skipped (:99), so `_git_rev` /
`_worktree_clean` — certification-gate primitives — are neither hashed nor
classified.

*A second-order lesson worth stating:* hashing **source text** creates a perverse
incentive. Because `decide_live` and the fully-dead `query_teacher_forced` (:1786)
are `@semantic`, deleting them invalidates every recorded hash and makes `run_train`
refuse (:3343–3344) — **dead code on the semantic surface is load-bearing dead
code** (C.12). Hashing a declared *schema* rather than source text does not create
that incentive, and Leyline's contracts are schemas.

---

**10. Carry forward, unchanged, the things the demo already proved.**

Not everything needs redesign. These are working and should be transplanted:

| Take | Evidence |
|---|---|
| Fail-closed version gate with the policy in the error text | `decode_record` :1567–1573 |
| Closed vocabularies whitelisted in the sole constructor | :1426–1428, :1501–1506 |
| Content-addressed identity over counters, with the derivation rule stated | `fan_identity` :1459, rule at :1498–1500 |
| Structural absence encoding with the invariant stated in-line | `curve_test: list[float] \| None`, :1011 |
| A contract that declares what it does **not** carry, and why | `Snapshot` :1143–1146 (C.4) |
| Every demotion from a refusal set carries a written reason at the point of exclusion | `REPLAY_REFUSAL_KEYS` :952–965, :954–956, :980–982 |
| Refuse rather than tolerate, at every entry point | :919–924, :81–82, :2860–2871, :3149–3152 |
| No measurement is a failure, not a pass | gate 5 :2702–2703 |
| Pre-registration enforced by *signature* — a required keyword-only parameter with no default makes recomputation impossible | `train_policy(frozen_density=...)` :1934 |

That last row deserves emphasis. Making an illegal operation impossible **by
function signature** is the cheapest form of "illegal states unrepresentable" in the
whole demo, and it is exactly the discipline Leyline contracts should encode.

---

## Confidence Assessment

**Overall Confidence: High** for the decomposition and the contract inventory;
**Moderate** for two forward-looking design recommendations, flagged individually.

| Decision | Confidence | Basis |
|---|---|---|
| Domain presence table (section A) | **High** | Every row cites catalog evidence or source lines I read directly. The two corrections (Elesh, Ugin) rest on catalog findings I verified against `02-constitution.md` Appendix B clause by clause. |
| Momir socket, outbound contract (A.2.1) | **High** | Read `SeedDelta` :636–650 and `build_seed` :720–731 directly. Every clause in the contract table is either visible in those lines or was verified by explorer 3 through execution across all four subclasses. |
| Momir socket, `name` as INV-09-invalid (A.2.1) | **High** | `preferred_operator` is listed verbatim in `05-leyline-contracts.md#93-growthintent`'s forbidden block, which I read in full. The identification is direct, not analogical. |
| Momir socket, "WHICH head does not survive the split" (A.2.1) | **Moderate** | Follows from `seed_head: Linear(d, 4)` (:1721) being fixed-width over `SEED_NAMES`, which I read. That a generated pool varies in size is inference from `ProposalBatchRequest.candidate_count`, not from demo evidence. |
| Elesh socket occupied by `tau_init` (A.2.2) | **High** | Read `tau_init` :734–747 directly; the measured 0.0500-for-all-four result and the 18× `rms(f0)` spread are explorer 3's, established by execution. The half-occupied framing is checked field-by-field against `CanonicalGrowthSpec`. |
| Ugin socket + simic-76fc6e6618 alignment (A.2.3) | **High** | Read `draw_schedule` :2305–2315 directly and retrieved the issue body via `mcp__filigree__issue_get` — the "randomised within declared bounds on a seed… keep it forever as the null" quote is verbatim. The no-envelope-input claim rests on `TELEMETRY_DIM = 20` (:351) being the policy's entire input width. |
| Emrakul socket (A.2.4) | **High** on the terminal state; **Moderate** on "cheap to fix later" | `Stage` :769–775 read directly — six members, no seventh. The claim that a descent path is one enum member and one branch away is my reading of `cosine_ease`'s symmetry (:779–781) and the stage-machine structure; I did not attempt it. |
| Urabrask socket welded shut (A.2.5) | **High** | Read `FORBIDDEN_RELAXATIONS` :898–913 directly; entries :908 and :912 are quoted verbatim, including the D10 rationale. This **corrects my own earlier position** — I had accepted "possibly no socket" before checking. |
| Module tree (section B) | **High** for the split lines; **Moderate** for the exact package granularity | The split lines are determined by where records already cross; the file-level granularity within a domain is a judgement call with no evidence forcing it. |
| `TelemetryRecord` → `TelemetryEnvelope` (C.1) | **High** | Read :357–420 directly; blinding-by-absence and the `check_finite` fall-through both verified in source. |
| `FanRecord` (C.2) | **High** | Read :1420–1535 directly, including all three vocabularies and the constructor's validation. |
| `ArmResult` (C.3) | **High** | Read :1207–1233 directly; the two-shapes finding is catalog-verified at four call sites. |
| `Snapshot` (C.4) | **High** | Read :1140–1163 directly; every HLD-field omission cross-checked against the stated reason in source. |
| `CommonFuture` (C.5) | **High** | Catalog-verified by construction (explorer 4 traced CRN to absolute-epoch indexing, not to the type name). |
| Insertion-region contract (C.6) | **Moderate** | The two-literal duplication is catalog-verified and empirically confirmed; that it *should* be a `RegionContract` record is inference from `02-constitution.md` Appendix B, not from demo evidence. |
| `GateResult` (C.7) | **High** on the gate-7 shim; **Moderate** on the authority reading | Gate 7's unconditional `True` and its pinning test are directly cited. The judgement that gate batteries are legitimately Jin-Gitaxias territory is my reading of INV-18's scope ("candidate" vs "apparatus") and is arguable. |
| Verdict booleans (C.8) | **High** | Read :3312–3325 directly; the never-ANDs finding is catalog-verified at four consumer sites. |
| `decisions` payload (C.9) | **High** | Read :3583–3614 directly; the diverged-baseline path at :3519/:3585 is catalog-verified. |
| Freeze manifest policy/evidence split (C.10) | **High** — *upgraded from Moderate* | The re-freeze decoupling is explorer 8's finding, coordinator-endorsed as possibly the most severe in the analysis. My flagged worry — that the split might weaken pre-registration — is **retired on evidence**: I read `run_train` :3343 and `run_eval` :3463 directly (both check only `frozen_block_hash` + `config_hash`) and audited all 45 `manifest_hash` occurrences. It is compared in exactly three places, all of which want a run identity and all of which survive the split. The split is not merely safe — it is the fix for the defect that motivated it (C.10). |
| `host_init_hash=""` (C.11) | **High** | Read :3606 and :1449 directly; the field's type is `str`, not `str \| None`. |
| Resolver duplication (C.12) | **High** | Coordinator-verified by repo-wide grep (one test caller, zero production callers). |
| Encoder twin + wire-encoding lesson (C.13) | **High** on the mechanism; **High** on the narrowed reachability | I verified the fall-through personally: read `_sanitize_json` :1546–1556 and `check_finite` :371–393. `None` is neither `float`, `tuple` nor `int`, and there is no `else`. I also checked the reachability and **narrowed my own claim**: `__post_init__` (:375) forecloses the normal path, so this is "the guard has no floor", not a live defect. Stated that way in C.13 and F.1. |
| Invariant satisfactions (section D) | **High** | Every claim is catalog-verified, and several were established by the explorers through *execution* rather than reading (the 80-combination RNG probe, the τ-RMS measurements, the torn-tail sequence). |
| `run_eval` authority-collapse reading (E.1) | **High** on mechanism and scope; **Moderate** on severity framing | The mechanism is coordinator-adjudicated between two conflicting explorers and re-verified against source (:3957–3958 vs :3592/:3597). I have preserved the coordinator's precision note limiting it to `policy_run` records. Severity framing ("unverified assumption, not a known error") is the coordinator's, and I adopt it. |
| Phase-A ranking (section F) | **Moderate** | The individual lessons are High-confidence; their *ordering* is my judgement about future cost and is the most contestable content in the document. |

---

## Risk Assessment

**Implementation Risk: Low.** This document is analysis, not a change. Its risk is
in being *believed too literally* in two specific ways, both mitigated in the text.

**Reversibility: Easy** for the document. **Difficult-to-Irreversible** for the
Phase-A decisions it informs — which is the actual risk surface.

| Risk | Severity | Likelihood | Mitigation |
|---|---|---|---|
| **The module tree is read as a refactor plan.** A reader who skips the framing sees a `src/simic/` tree and starts moving code, breaking a locked spec decision and invalidating every recorded hash (`config_hash` covers source text, so *any* move refuses `run_train` at :3343). | **High** | Moderate | Banner at §0 and repeated at the head of §B. **The hash consequence is itself the strongest deterrent and is stated in C.12.** |
| **Schema decisions harden the moment records exist.** Recommendations 1, 4 and 5 (payload typing, absence encoding, discriminated union) are nearly free before Phase A writes a record and expensive after — the demo's own `SCHEMA_VERSION = 1` / additive-only policy (:1570) exists precisely because post-collection changes are an owner decision. | **High** | High if deferred | Ranked 1, 4, 5 in §F for exactly this reason. **These three should land before the first Leyline record is persisted.** |
| **The Elesh/Ugin corrections are over-read as "the demo has these domains".** Both are `partial` in a specific, narrow sense (contract-without-step; record-without-issuer) and neither exercises its invariants. | Medium | Moderate | Each correction states the limit explicitly and the "cannot test" column enumerates the untested INV-nn. |
| **A Phase-A reader treats the demo's `@semantic` source-text hashing as the model for Leyline identity.** It works for a single-file demo and creates the load-bearing-dead-code incentive (C.12) at package scale. | Medium | Moderate | Stated explicitly as a second-order lesson in §F.9 with the recommendation to hash schema, not source. |
| **Compliance/correctness risk:** none of the demo's *published* results is invalidated by anything here. The E.1 finding is an unverified assumption with strong supporting evidence, affecting 2 of 5 verdict booleans. | Low | — | Coordinator's precision note preserved verbatim; scope stated in E.1. |
| **Maintenance risk:** this document cites ~120 line numbers in a file that is expected to change. | Medium | High over time | Every citation is paired with a symbol name, so a reader can re-locate by name after drift. The catalog it derives from has the same property. |

**Which decisions harden first:** payload typing (§F.1), absence encoding (§F.4)
and the discriminated union (§F.5) are cheap now and expensive after records exist.
The dependency gate (§F.8) is free before the second package exists and a migration
after. The policy/evidence split (§F.2) is cheap until the first manifest is
frozen against real collected data.

---

## Information Gaps

1. **I did not run the demo.** Every claim in this document, and in the catalog it
   rests on, is static analysis plus targeted micro-execution by the explorers. No
   CLI mode was executed; no hash value, gate outcome, refusal path or p-value has
   been observed against a real run. *What it would change:* nothing structural —
   contract shapes are static properties — but the severity of E.1 would move if a
   real run showed prefix agreement or disagreement.

2. **I did not read `experiments/kernel_demo.py` linearly.** Per the briefing I
   navigated by the catalog's line citations, reading roughly 500 lines directly.
   Sections I did not open include most of the gate bodies (:2547–2827), the
   statistics block (:3651–3818) and `run_preflight` (:2919–3033) — the last of
   which explorer 8 also did not read, which is why its entry is graded Medium.
   *What it would change:* possibly additional contract shapes inside the statistics
   block; I have treated it as one unit ("the evidence certification stage") rather
   than enumerating its records.

3. **The Phase-A record inventory is not settled by anything I can see.** I do not
   know which of the twenty HLD contract classes Phase A intends to implement first,
   nor whether `docs/design/05-leyline-contracts.md`'s shapes are locked at field
   granularity or only at record granularity. Plainweave baseline status is
   "seeding pending" (simic-357c92664c), so no definition-lifecycle state was
   available to check. *What it would change:* the ranking in §F, and whether
   recommendation 5 (discriminated union) is a decision still open or already made.

4. **I did not verify the spec-rev claims against the spec.** I have taken the
   locked-layout decision (rev 6.1, line 4, line 574) and the "≲1200 lines" target
   (line 560) from the coordination log rather than from
   `docs/superpowers/specs/2026-08-09-kernel-demo-design.md` directly. The
   coordinator holds the spec and adjudicated one finding against it (the
   `d_model`/`n_layers` downgrade), so this is second-hand but well-sourced.

5. **One file moved under me; the main file did not. Both halves verified.**

   *What actually happened:* `experiments/kernel_demo_plots.py` was rewritten after
   the catalog entry I first read was produced (`853e9ef`, the review-fix pass, then
   `aa86388`). I caught it by following a citation, re-read the current file, and
   corrected §E.7 and §D.3 against it.

   *What did **not** happen:* **`experiments/kernel_demo.py` is byte-stable.**
   Verified directly — `git diff --stat HEAD -- experiments/kernel_demo.py` is
   empty, `git status --porcelain` reports zero modified files (three untracked
   directories only), and its mtime is 06:51:12, unchanged since before the analysis
   began. HEAD is `aa86388`. So all 4,066 lines of the main file, and eight of the
   nine catalog entries, rest on a fixed artifact.

   *Correction of an earlier draft of this entry:* it claimed `kernel_demo.py` was
   "also shown modified" and generalised that inherited citations may have drifted.
   **That was false** — I had read `M experiments/kernel_demo_plots.py` in a
   session-start snapshot and generalised it to the main file without checking.
   Recorded rather than silently fixed, because the error class matters: it is the
   same one as §Gaps.5's real lesson below, committed while writing about it.

   *The lesson that does survive:* I inherited a snapshot from the catalog and did
   not re-check it against HEAD. That is a real methodological gap and it caught a
   real defect — it simply applied to exactly one file, and the catalog now carries
   a version anchor recording which entries are anchored where.

6. **Whether the eval-path prefix assumption actually holds at runtime is unknown
   and knowable cheaply.** One `state_hash` on `noop_ctx.host` at construction,
   stored instead of `""` (:3606), would settle it. I am recommending the contract
   change; I have not measured whether the assumption it protects is currently
   violated.

---

## Caveats & Required Follow-ups

**Must verify before acting on this document:**

1. **That the reader understands §B is not a refactor plan.** If any part of this
   document is quoted onward, quote the §0 banner with it.
2. **That §A's two corrections are accepted.** I have contradicted the briefing on
   Elesh and Ugin. Both are defensible from `02-constitution.md` Appendix B, but the
   coordinator holds the spec and the domain semantics and should adjudicate.
3. ~~That the freeze-manifest policy/evidence split (§F.2) is compatible with the
   pre-registration discipline it is meant to protect.~~ **RESOLVED** — adjudicated
   by the coordinator and independently re-verified here. `run_train` (:3343) and
   `run_eval` (:3463) enforce pre-registration through `frozen_block_hash` +
   `config_hash` and never consult `manifest_hash`; all 48 occurrences audited. The
   split is safe and is the fix for the defect that motivated it. Reasoning recorded
   inline in §C.10. **No longer an open question.**
4. ~~That the Plotting Sidecar entry in `02-subsystem-catalog.md` is now stale.~~
   **RESOLVED, and my warning was itself stale.** The catalog's sidecar entry was
   rewritten in full at 07:34 against `aa86388`, and the merged catalog (now 911
   lines) carries a **version anchor** at lines 6–9 recording which entries are
   anchored to which commit — including the verification that `kernel_demo.py` is
   unchanged from `2b48431` through `aa86388`. I had read the pre-re-merge version.
   No action needed; the current catalog is correct.

**What this document rests on:**

- The correctness of `02-subsystem-catalog.md`. It is a completed, validated
  analysis and I did not re-derive it, per the briefing. Where I cite a line I did
  not read myself, the claim is the catalog's and inherits its confidence — which
  the catalog states per entry (eight High, one Medium).
- The coordinator's adjudications in `00-coordination.md`, which I have treated as
  authoritative where they correct an explorer. Three mattered here: the
  `run_eval`-mechanism adjudication (08:45), the `policy_run`-replay precision note
  (08:52), and the test-suite existence correction (08:02).

**What this document does not cover:**

- The *full* contract for a domain absent from the demo (Momir, Urabrask, Emrakul).
  §A.2 documents each socket — position, inbound and outbound type signatures, and
  what the contract must become — which is what the demo can actually evidence. The
  remaining fields of `RawGrowthGraph`, `CanonicalGrowthSpec` and
  `ExecutableGrowthArtifact` must be designed from the HLD; nothing in the demo
  speaks to them.
- The statistical validity of the demo's design. That is
  `yzmir-counterfactual-statistics` territory; the two touchpoints here (grouped
  statistics in D.5, the diverged-baseline confound in C.9) are reported as contract
  properties, not as statistical findings.
- Test-plan design for the Phase-A contract suite. §F names what to test but not the
  fixture inventory or coverage rule; `contract-testing.md` supplies both.

**Recommended next steps, in order:**

1. **Coordinator adjudicates §A's two corrections** (Elesh, Ugin) and the §F.2
   caveat.
2. **Run `/review-contracts`** against this document — I designed the suite; an
   independent `contract-reviewer` pass against the 13-entry catalogue is the check.
   Per the pack's own discipline, a zero-finding audit would be a defect of the
   audit.
3. **Land §F recommendations 1, 4 and 5 before the first Leyline record is
   persisted** — payload typing, absence-as-a-type, discriminated union. These are
   free now and expensive later.
4. **Configure the import-lint gate (§F.8) before `src/simic/` has a second
   package.**
5. **Optional, cheap, and settles §Gaps.5:** store `state_hash(noop_ctx.host)` in
   `policy_run.host_init_hash` instead of `""` and compare it against the treated
   episode's. One hash, one comparison — and the demo's headline claim becomes
   verified rather than assumed.
6. **Relay §A.2.3 to whoever picks up filigree simic-76fc6e6618** ("the Ugin stub
   must vary — randomised allocator now, kept forever as the null control"). Two
   findings bear on it directly: `draw_schedule` (:2307) **is already** the
   seed-derived randomised allocator within declared bounds that the issue asks to
   be built; and the demo demonstrates the issue's own failure mode, because
   `cfg.window` is frozen and the `Policy` has **no envelope input at all**
   (`TELEMETRY_DIM = 20`, :351). The remedy is therefore two-part — vary the
   envelope *and* give the actor a field to read it in — and only the first half is
   currently written down.
