# Simic — Counterfactual Generative Morphogenesis

A lifecycle-driven neural training system in which new computational structure
is **generated from the live state of a host network** — not selected from a
fixed menu of human-authored blueprints — then conformed, compiled, QA-tested
in matched counterfactual branches, adjudicated against doing nothing,
embodied reversibly under warrant, and eventually retired.

> **Status: pre-implementation bootstrap.** The design is complete —
> [HLD v4.1](docs/concept/simic.md) is the authoritative
> repository-handoff target — but no source code exists yet. First
> engineering work is Phase A (Namespec, Leyline contracts, dependency
> boundaries). The project-level name may still change (HLD §27.1); the
> subsystem boundaries will not.

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
and branches), and **Sarpadia** (append-only history, ancestry, retrieval).
The other eleven are agents, summarised by the canonical sentence (HLD §5.3):

> Nissa observes and reports. Tamiyo plans. Narset commissions and acts.
> Momir designs. Elesh conforms. Tezzeret compiles. Urabrask tests the
> compiled result in Tolaria. Augustin judges the resulting evidence under
> Leyline. Kasmina embodies the admitted growth. Emrakul destroys what no
> longer earns continued tenancy. Sarpadia retains every precedent. Oona
> reveals the account.

The architecture deliberately resembles a newsroom (HLD §5.5, Appendix E):
observation, assignment, authorship, standards, production, fact-checking,
publication judgement, and archive are separate desks, because letting one
desk control the whole chain corrupts both evidence and accountability. The
load-bearing routing rule: **Nissa sends the photograph directly to the
designer; the assignments editor sends only the assignment brief.**

## Guarantees

HLD §18 defines 44 blocking invariants. The spine:

- **Determinism:** identical snapshot + identical future data ⇒
  bitwise-identical traces under the Academy execution profile; non-exact
  profiles carry measured uncertainty instead of pretending.
- **Doing nothing is a real competitor:** every admission and tenancy review
  includes a measured no-intervention branch; the whole candidate pool may
  lose to it.
- **Evidence and judgement never mix:** Urabrask (QA) certifies evidence but
  cannot issue verdicts; Augustin (judge) decides but cannot touch tests —
  and neither ever sees candidate provenance (blinding by construction).
- **No influence without a warrant:** Kasmina cannot raise a growth above
  zero influence, and Emrakul cannot retire committed structure, without a
  valid Augustin warrant.
- **Complete history:** Sarpadia is append-only and keeps failures and
  abstentions — never winners-only.
- **Observability is inert:** disconnecting Oona cannot change training.

## Repository map

```text
docs/concept/simic.md            Authoritative HLD (v4.1, Namespec 1.0 — locked)
docs/concept/archive/            Superseded designs, historical reference only
AGENTS.md / CLAUDE.md            Orientation digest for coding agents
```

Target code layout (once implementation starts) is one package per domain
under `src/simic/`, with authority-boundary tests under `tests/` — see HLD
§20. Implementation follows Phases A–K (HLD §25); the minimum viable system
is defined in HLD §24. Python is the working language.

## Lineage

Simic is the third incarnation of this research programme, redesigned around
discoveries from **ESPER** and **ESPER LITE**. The morphogenetic chassis
(reversible slots, staged maturation, lifecycle states) carries over; what
changed is that growth is now *generated* from host state and *causally
screened* against doing nothing, under separated authorities.

## Working on this repo

Work is tracked in filigree (dashboard at `http://localhost:9328` when
running; `filigree session-context` at session start); design-review findings carry the
`hld-review` label. The repo also uses the Weft tooling suite — loomweave
(code map), wardline (trust-boundary gate), warpline (change impact), and
legis (governance) — see `AGENTS.md` for agent-facing instructions.
