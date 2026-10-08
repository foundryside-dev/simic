# Simic — Counterfactual Generative Morphogenesis

A lifecycle-driven neural training system in which new computational structure
is **generated from the live state of a host network** — not selected from a
fixed menu of human-authored blueprints — then conformed, compiled, QA-tested
in matched counterfactual branches, adjudicated against doing nothing,
embodied reversibly under warrant, and eventually retired.

> **Status (2026-10-08): bounded experimental implementation.** The runnable
> [bounded comparison](docs/bounded-comparison.md) trains one fixed host three
> ways: no growth, static added capacity, and a scheduled graft. Outer
> evaluation is a separate command. A pre-registered 48-seed screen on CIFAR-10
> development data showed that the paired measurement resolves differences of
> ±0.018 nats. At that scale the graft earns nothing, and neither does static
> capacity ([result](docs/results/2026-10-08-bounded-screen-v1.md)). The next
> round first establishes a host with a real deficit. No growth-superiority or
> learned-controller result exists. The full HLD under
> [`docs/design/`](docs/design/00-INDEX.md) remains a design, `src/simic/` is a
> package scaffold, and the August kernel-demo campaign is parked.

## The idea

Growing a neural network at runtime raises four questions that existing
systems tend to blur together: *what* new structure to add, *whether* it is
structurally sound, *whether* it actually helps, and *who* gets to decide.
Simic separates those concerns constitutionally. Structure is designed from
live host telemetry; verified and canonicalised; compiled without semantic
change; tested in flash-cloned counterfactual branches that share an
identical future with the mainline; and admitted only if it beats a
**mandatory no-op alternative** under a provider-blind judge. Everything —
including failures, rejected pools, and no-op wins — is retained as history.

Admitted structure is never permanent by default: it matures behind the host,
blends in reversibly, must keep earning its tenancy, and is sedated or lysed
when it no longer does.

## The fourteen domains

Authority is split across fourteen bounded domains with deliberately vivid
codenames (they act as an architecture linter — a subsystem acting contrary
to its verb is exercising authority it must not have). Three are
infrastructure: **Leyline** (contracts and the deterministic request
resolver), **Tolaria** (the single training/execution substrate for mainline
and branches), and **Urborg** (append-only history, ancestry, retrieval).
The other eleven are agents, summarised by the canonical sentence
([`docs/design/02-constitution.md`](docs/design/02-constitution.md)):

> Under Leyline, Ugin plans, Aurelia commissions and acts, Nissa observes,
> Momir designs, Elesh conforms, Urabrask compiles, Jin-Gitaxias tests in
> Tolaria, Isperia judges, Wrenn embodies, Emrakul destroys, and Tamiyo
> reveals; every precedent is kept in Urborg.

The load-bearing routing rule: **Nissa publishes the evidence directly to
the designer; Aurelia sends only the assignment brief** — evidence never
arrives pre-captioned by the desk that commissioned it (INV-07, INV-09).
And for readers who would rather picture an institution than learn a
mythology, [`docs/design/appendices/newsroom.md`](docs/design/appendices/newsroom.md)
retells the whole authority model as a newsroom — the same separations, no
new vocabulary.

## Guarantees

The constitution ([`docs/design/02-constitution.md`](docs/design/02-constitution.md))
defines 45 blocking invariants, cited as INV-nn. The spine:

- **Determinism (INV-05):** identical snapshot + identical future data ⇒
  bitwise-identical traces under the Academy execution profile; non-exact
  profiles carry measured uncertainty instead of pretending.
- **Doing nothing is a real competitor (INV-15, INV-16):** every admission
  and tenancy review includes a measured no-intervention branch with policy
  utility exactly zero; the whole candidate pool may lose to it.
- **Tail risk cannot be bought (INV-45):** admission is lexicographic — a
  tail-risk veto precedes utility comparison, and no measured benefit can
  offset a veto.
- **Evidence and judgement never mix (INV-17, INV-18, INV-37):** Jin-Gitaxias
  (QA) certifies evidence but cannot issue verdicts; Isperia (judge)
  decides but cannot touch tests — and neither ever sees candidate
  provenance (blinding by construction).
- **No influence without a warrant (INV-26, INV-27):** Wrenn cannot raise
  a growth above zero influence, and Emrakul cannot retire committed
  structure, without a valid Isperia warrant.
- **Complete history (INV-31, INV-36):** Urborg is append-only and keeps
  failures and abstentions — never winners-only.
- **Observability is inert (INV-35):** disconnecting Tamiyo cannot change
  training.

## Repository map

```text
docs/design/                     Canonical HLD chapter set; entry point 00-INDEX.md
docs/adr/                        Architecture decision records
docs/product/                    Product workspace (vision, roadmap, decisions)
docs/bounded-comparison.md       How to run the current experiment, and its contract
docs/results/                    Dated result notes with archived run evidence
docs/prereg/                     Frozen pre-registered analysis plans
experiments/                     Runnable code: bounded comparison and screen, kernel demo
docs/concept/archive/            Archived v4.1 monolith and superseded v2.0 — historical only
ARCHITECTURE.md                  One-page digest of the system shape (start here)
AGENTS.md / CLAUDE.md            Orientation digest for coding agents
```

Target code layout (once implementation starts) is one package per domain
under `src/simic/`, with authority-boundary tests under `tests/` — see
[`docs/design/ops/repo-structure.md`](docs/design/ops/repo-structure.md).
Implementation follows Phases A–K, and the minimum viable system is defined,
in [`docs/design/programme/phases.md`](docs/design/programme/phases.md).
Python is the working language.

## Lineage

Simic is the third incarnation of this research programme, redesigned around
discoveries from **ESPER** and **ESPER LITE**. The morphogenetic chassis
(reversible slots, staged maturation, lifecycle states) carries over; what
changed is that growth is now *generated* from host state and *causally
screened* against doing nothing, under separated authorities.

## Working on this repo

Work is tracked in filigree (dashboard at `http://localhost:9328` when
running; `filigree session-context` at session start); design-review findings carry the
`hld-review` label. The repo also uses loomweave (code map) and plainweave
(definition lifecycle) from the Weft tooling suite; see `AGENTS.md` for
agent-facing instructions. Wardline, Warpline and Legis were retired from this
repo on 2026-10-08 (PDR-0042).

Run the test suite from the repository root (CPU only):

```bash
PYTHONPATH=.:src .venv/bin/python -m pytest tests -q
```
