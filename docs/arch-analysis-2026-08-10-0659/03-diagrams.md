# 03 — C4 Diagrams

**Target:** `experiments/` (the Simic kernel demo)
**Date:** 2026-08-10
**Version anchor:** `experiments/kernel_demo.py` at `c666a4c` plus the three pre-data
guards (PR #11); `experiments/kernel_demo_plots.py` at `aa86388` (PR #10). Both PRs are
open at time of writing — the structure below is unaffected by either, since neither adds
or removes a subsystem or an edge.

Every edge is taken from the dependency blocks in
[`02-subsystem-catalog.md`](02-subsystem-catalog.md), which derived them by AST walk over
the assigned line ranges rather than by reading declarations. No edge here was inferred
from prose. Where the catalog labels an edge `serialized-shape` (a consumer reading field
*names* out of a dict it did not construct) that is drawn distinctly, because those are
the edges no type checker can see.

Diagrams are Mermaid rather than Structurizr: this workspace is standalone markdown, and
these render in GitHub, in the wiki pipeline, and in a plain editor without the pinned
`structurizr-cli`/`plantuml` jars.

---

## Level 1 — System Context

The demo is an offline, single-process research harness. It has no network surface, no
auth, and no external service dependency; that is why the security-surface and
dependency-analysis options were deliberately omitted from this analysis
([`00-coordination.md`](00-coordination.md)).

```mermaid
flowchart TB
    operator["<b>Researcher-operator</b><br/><i>[person]</i><br/>Runs the phases, present at<br/>freeze and at the one-shot eval"]

    subgraph sys["Simic Kernel Demo &mdash; 'Simic in 20 minutes'"]
        demo["<b>kernel_demo</b><br/><i>[Python, 4k LOC, one module]</i><br/>Generates structure from host state,<br/>screens it against doing nothing"]
        plots["<b>kernel_demo_plots</b><br/><i>[Python, sidecar]</i><br/>Renders figures. Deliberately outside<br/>the semantic surface"]
    end

    cifar[("<b>CIFAR-10</b><br/><i>[torchvision download]</i><br/>Fixed train/val/test split")]
    torch["<b>PyTorch + CUDA</b><br/><i>[runtime]</i><br/>Class-1 determinism knobs,<br/>deterministic algorithms pinned"]
    store[("<b>Run artifacts</b><br/><i>[filesystem, append-only]</i><br/>shards/, frozen.json, certified.json,<br/>policies/, eval_results.json")]
    mpl["<b>matplotlib</b><br/><i>[Agg backend]</i><br/>Sidecar only &mdash; the demo runs<br/>without it installed"]

    operator -->|"7 CLI modes:<br/>selftest, preflight, collect,<br/>train, eval, report, replay"| demo
    operator -->|"reads figures"| plots
    demo -->|"loads, splits by fixed seed"| cifar
    demo -->|"trains hosts and policies"| torch
    demo -->|"appends records, never rewrites"| store
    plots -->|"reads records + results.<br/>NEVER writes"| store
    plots --> mpl

    classDef sysStyle fill:#1a4d5c,stroke:#2d7d8f,color:#fff
    classDef extStyle fill:#3a3a3a,stroke:#666,color:#ddd
    classDef personStyle fill:#2d5016,stroke:#4a7c26,color:#fff
    class demo,plots sysStyle
    class cifar,torch,store,mpl extStyle
    class operator personStyle
```

**The load-bearing context fact:** the arrow from `kernel_demo_plots` to the store is
one-way and read-only, and there is no arrow back. The sidecar cannot influence any
recorded number. That is the property the separate module exists to guarantee, and it is
enforced by absence — the sidecar carries no `@semantic`/`semantic_const` registration, so
it is not in `config_hash`.

---

## Level 2 — Containers

"Container" here means an independently invocable execution unit — the CLI modes — plus
the persistent stores they exchange state through. The modes are strictly ordered: each
refuses to run until its predecessor's artifact exists and matches.

```mermaid
flowchart TB
    operator(["Researcher-operator"])

    subgraph phases["Execution phases &mdash; ordered, each gated on the last"]
        direction TB
        selftest["<b>selftest --certify</b><br/>10-check battery.<br/>Writes certified.json<br/>pinned to git HEAD"]
        preflight["<b>preflight --freeze</b><br/>8 gates. Writes frozen.json<br/><b>OWNER PRESENT</b> &mdash; constants<br/>sign-off"]
        collect["<b>collect</b><br/>300 episodes, sharded<br/>by worker, fan-level resume"]
        train["<b>train</b><br/>Fits trained +<br/>schedule_only policies"]
        evalm["<b>eval</b><br/><b>ONE-SHOT</b> &mdash; refuses if<br/>results exist. OWNER PRESENT"]
        report["<b>report</b><br/>Reads results,<br/>computes verdict"]
        replay["<b>replay &lt;fan_id&gt;</b><br/>Re-runs one fan,<br/>bitwise comparison"]
    end

    certj[("certified.json<br/><i>git rev + battery result</i>")]
    frozenj[("frozen.json<br/><i>normalizer, density, betas,<br/>manifest_hash</i>")]
    shards[("shards/worker_N.jsonl<br/><i>append-only record log</i>")]
    pols[("policies/*.pt + *.json<br/><i>checkpoints keyed by<br/>state-dict hash</i>")]
    resultsj[("eval_results.json<br/><i>the pre-registered numbers</i>")]
    sidecar["<b>kernel_demo_plots</b><br/><i>read-only sidecar</i>"]

    operator --> selftest --> preflight --> collect --> train --> evalm --> report
    operator --> replay

    selftest -.->|writes| certj
    certj -.->|"freeze refuses unless<br/>HEAD matches"| preflight
    preflight -.->|writes| frozenj
    frozenj -.->|"calibration read by"| train
    frozenj -.->|"manifest gate"| collect
    frozenj -.->|"manifest gate"| evalm
    collect -.->|appends| shards
    shards -.->|"records read by"| train
    train -.->|writes| pols
    pols -.->|"loaded by"| evalm
    evalm -.->|appends policy_run| shards
    evalm -.->|writes| resultsj
    resultsj -.->|read| report
    shards -.->|"one fan re-run"| replay

    shards -.->|read| sidecar
    pols -.->|read| sidecar
    resultsj -.->|read| sidecar

    classDef phase fill:#1a4d5c,stroke:#2d7d8f,color:#fff
    classDef gated fill:#5c3a1a,stroke:#8f6b2d,color:#fff
    classDef data fill:#2a2a3a,stroke:#555,color:#ccc
    classDef side fill:#3a2a4a,stroke:#6a4a8a,color:#eee
    class selftest,collect,train,report,replay phase
    class preflight,evalm gated
    class certj,frozenj,shards,pols,resultsj data
    class sidecar side
```

**Amber = owner-present.** `preflight --freeze` takes the constants sign-off; `eval` is
pre-registered and unrepeatable — a second run requires `--void-preregistration`, which
writes a permanent `void_event`.

**The gap this analysis found is on the `frozen.json → train` edge.** `train` read
calibration from `frozen.json` and records from `shards/` as two independent reads, with
nothing tying them to the same manifest generation, while `freeze_manifest` overwrites
`frozen.json` in place. Now refused (PR #11, finding F6).

---

## Level 3 — Components

The nine subsystems. Solid = `call`, dashed = `serialized-shape` (field names read out of
a dict the consumer did not build — invisible to mypy, and the edge class most likely to
break silently).

Drawn as two views. Every subsystem depends on the spine, so drawing those eight edges
explicitly buries the structure under crossings — they are stated once below instead. The
second view isolates the `serialized-shape` edges, which is where the risk actually sits.

### 3a — Dependency layers

```mermaid
flowchart TB
    RUN["<b>Run Orchestration &amp; CLI</b><br/>7 modes, worker fan-out,<br/>content-addressed resume"]
    CERT["<b>Certification Battery</b><br/>10 selftest checks,<br/>8 preflight gates"]
    POL["<b>Policy &amp; Learning</b><br/>Transformer,<br/>tune-scored checkpointing"]
    FAN["<b>Counterfactual Fan Executor</b><br/>Matched arms from one snapshot,<br/>bitwise twin, TwinDivergence"]
    DATA["<b>Data, Episodes &amp; Telemetry</b><br/>Pre-drawn futures,<br/>blinded TelemetryRecord"]
    HOST["<b>Host, Seeds &amp; Slot Lifecycle</b><br/>Pathologies, seed menu,<br/>STE stage schedule"]
    REC["<b>Records &amp; Store</b><br/>Schema, shards, split walls<br/><i>verified leaf &mdash; spine only</i>"]
    SPINE["<b>Identity, Config &amp; Determinism Spine</b><br/>config_hash, frozen_block_hash, derive, rng_scope<br/><i>pure leaf &mdash; ZERO outbound edges</i>"]

    RUN <==>|"the only cycle"| CERT
    RUN --> POL
    RUN --> FAN
    CERT --> POL
    CERT --> FAN
    POL --> DATA
    FAN --> DATA
    FAN --> HOST
    DATA --> HOST
    RUN --> REC
    CERT --> REC
    FAN --> REC
    HOST --> SPINE
    REC --> SPINE

    SPINE -.->|"every subsystem<br/>depends on the spine"| SPINE

    classDef leaf fill:#1a3d2a,stroke:#2d7d4f,color:#fff,stroke-width:2px
    classDef normal fill:#1a4d5c,stroke:#2d7d8f,color:#fff
    class SPINE,REC leaf
    class RUN,CERT,FAN,HOST,DATA,POL normal
```

Edges to the spine from `RUN`, `CERT`, `FAN`, `DATA` and `POL` are omitted for legibility;
all five exist and are `call`-kind. `HOST → SPINE` and `REC → SPINE` are drawn because they
are those subsystems' *only* outbound edges.

### 3b — The edges no type checker can see

Three `serialized-shape` edges carry field *names* across boundaries. A rename on either
side type-checks cleanly and fails at runtime — or worse, reads a default. The sidecar's
edge is drawn too: it crosses a process boundary via JSON files rather than imports.

```mermaid
flowchart LR
    POL["<b>Policy &amp; Learning</b>"]
    DATA["<b>Data, Episodes<br/>&amp; Telemetry</b>"]
    FAN["<b>Counterfactual<br/>Fan Executor</b>"]
    CERT["<b>Certification Battery</b>"]
    PLOT["<b>Plotting Sidecar</b><br/><i>zero inbound</i>"]
    RUN["<b>Run Orchestration &amp; CLI</b>"]
    REC["<b>Records &amp; Store</b>"]

    POL -. "20 telemetry key names<br/><b>AND their order</b>" .-> DATA
    POL -. "rec.arms &rarr; ArmResult<br/>field names" .-> FAN
    CERT -. "ArmResult field names" .-> FAN
    PLOT -. "eval_results.json,<br/>policies/trained.json<br/><i>JSON, not imports</i>" .-> RUN
    PLOT ==>|"FanRecord, Store<br/>read-only"| REC

    classDef risk fill:#5c1a1a,stroke:#8f2d2d,color:#fff
    classDef normal fill:#1a4d5c,stroke:#2d7d8f,color:#fff
    classDef side fill:#3a2a4a,stroke:#6a4a8a,color:#eee
    class DATA,FAN risk
    class POL,CERT,RUN,REC normal
    class PLOT side
```

### What the shape shows

**Two verified leaves, green.** The spine has *zero* outbound edges within the file — it
references no symbol defined later in the narrative order. Records & Store depends on the
spine and on nothing else, while six of the seven other subsystems depend on it. That is
the dependency-direction property the parent programme states as a rule (contracts import
nothing from their consumers), achieved here by discipline rather than by enforcement:
the single-file layout is a locked spec decision, so there is no import gate keeping it
true and no linter would catch a future edit that reached from the store range into the
fan or telemetry sections. It currently holds completely.

**The sidecar has no inbound edge at all.** Its only importer anywhere is its own test
module. Combined with its absence from the semantic surface, this is what makes "plots
never touch the recorded numbers" a structural fact rather than a convention.

**`Certification Battery ↔ Run Orchestration` is the only cycle.** It is genuine, not an
artifact: `run_preflight` calls the shared episode machinery, and the CLI dispatches into
the battery. Both live in the author's own section map.

**The dashed edges are where the risk concentrates.** Three `serialized-shape` edges carry
field names across boundaries with no type checking: `Policy & Learning` reads 20
telemetry key names *and depends on their order*; two consumers read `ArmResult` field
names out of `rec.arms`. A rename on either side type-checks cleanly and fails at runtime,
or worse, reads a default.

---

## Caveats

These carry over from [`02-subsystem-catalog.md`](02-subsystem-catalog.md) and
[`04-final-report.md`](04-final-report.md), and they bound how much weight the pictures
can take:

1. **The partition cuts mid-section in 9 of 15 boundaries.** Subsystems were derived by
   line-range partition over one 4k-line module, and the author's own section map does not
   align with the range boundaries everywhere. One phantom edge was caught and removed.
   The 1142 boundary is a confirmed section-internal case: the `Fan Executor ↔ Data` edge
   is real at citation level but intra-section under the author's map, so it **inflates
   apparent coupling** in the Level 3 diagram without hiding anything.

2. **Edge counts are not shown.** The catalog carries per-edge counts (e.g. `call(29)`);
   the diagrams show presence only. A thin edge and a 29-call edge look identical here.

3. **Level 2 shows the intended ordering, not every reachable path.** `--resume-eval`
   appears in `run_eval`'s signature and nowhere else — it is dead, and no edge is drawn
   for it. `report` and `replay` can be run at any time after their inputs exist.

4. **All four diagrams were rendered and visually inspected** before this file was
   committed (`mmdc` against system Chrome, 1500px). The Level 3 view was restructured
   after the first render: drawing all eight spine edges explicitly produced a crossing
   mess that buried the layering, so those edges are stated in prose instead. Note this
   means the *rendering* is verified, not the *claims* — every edge still traces to
   [`02-subsystem-catalog.md`](02-subsystem-catalog.md), and a wrong edge there is a wrong
   edge here.

5. **The host-hash experiment is no longer outstanding.** [`04-final-report.md`](04-final-report.md)
   lists it as the one open item that could change a finding's severity. It was run on
   2026-08-10: twelve `make_episode` pairs reconstructed from one episode seed each,
   comparing `state_hash` of the no-op baseline host against the treated arm's —
   **12/12 matched, 0 differed**. So the lift path's prefixes do agree, and F2
   (`host_init_hash=""`) is an integrity/provenance gap rather than a live wrong-number
   defect. The assumption is now also checked at runtime rather than inferred (PR #11).
