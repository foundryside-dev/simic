# ADR-0017 — Give ADRs an append-only metadata block, and draw the immutability line at it
<!-- adr-meta:begin — append-only; rules: README.md#metadata-and-immutability -->

Date: 2026-08-11 · Status: accepted
Deciders: John (owner-directed, in-session 2026-08-11: "engineer the ADR problem
by adding 'metadata' to ADRs that lets us add additional context and point to
new ADRs") · Tracker: —

Amends: —
Amended-by: —
Supersedes: —
Superseded-by: —
<!-- adr-meta:end — everything below is IMMUTABLE body (ADR-0017) -->

## Context

`README.md` states the Tier-1 rule: ADRs are *"numbered, immutable once
accepted; supersede, never edit."* The intent is sound and matches INV-36's
append-only posture — corrections create new records rather than rewriting
causal history.

**The rule as written is already violated, in seven of sixteen records.**
ADR-0001 through ADR-0007 each carry a retroactively inserted
`> **Namespec note (ADR-0008):**` block explaining that the record predates
Namespec 2.0 and how to read its subsystem names. Those insertions were right —
a reader who lands on ADR-0004 without knowing the names moved is misled — but
under the stated rule they are prohibited edits to accepted records.

The same pressure recurred on 2026-08-11. ADR-0016 amended ADR-0014's gating
status, and a reader landing on ADR-0014 would otherwise believe the programme
is still making a confirmatory claim. An eight-line explanatory block was added
to ADR-0014's body, then removed on the same grounds — leaving only a status-line
pointer, which `TEMPLATE.md` sanctions but which cannot carry a dated note.

The rule has no legitimate mechanism for the two things that are actually
needed and are not reinterpretations of any decision:

1. **Forward pointers.** An accepted record must be able to say "my standing
   changed; go read ADR-nnnn." Nothing about the original decision changes.
2. **Reading context discovered later.** "This predates Namespec 2.0" is not a
   revision; it is navigation.

Absent a mechanism, the choice is to violate the rule (what happened) or to
leave readers misled (worse). Both are avoidable.

## Decision

**Every ADR carries a delimited, append-only metadata block. The immutability
line is drawn at that block's end, not at the file.**

### Mechanics

The block sits between the title and `## Context`, delimited by machine-readable
markers:

```text
# ADR-NNNN — Title
<!-- adr-meta:begin — append-only; rules: README.md#metadata-and-immutability -->

Date: … · Status: …
Deciders: … · Tracker: …

Amends: — | ADR-nnnn
Amended-by: — | ADR-nnnn
Supersedes: — | ADR-nnnn
Superseded-by: — | ADR-nnnn

Notes:
- YYYY-MM-DD (ADR-nnnn | PDR-nnnn): one line on what changed about standing.
<!-- adr-meta:end — everything below is IMMUTABLE body (ADR-0017) -->

## Context
```

### The four rules

1. **One mutable region.** Everything between `adr-meta:begin` and
   `adr-meta:end` is append-only-mutable. **Everything after `adr-meta:end` is
   immutable once `Status: accepted`** and changes only through a new ADR. One
   boundary, machine-checkable, no ambiguity about which part of a record is
   settled.
2. **Append-only, never rewrite.** `Status` may advance; cross-reference fields
   may gain entries; `Notes` may gain dated lines. Nothing already written is
   deleted or reworded. A mistaken note is corrected by a later note, per INV-36.
3. **No uncaused annotation.** Every cross-reference entry and every `Notes`
   line **must name the record that caused it** — an ADR or a PDR. An annotation
   with no causing record is prohibited. This is the rule that prevents the block
   becoming a back door for silent revision, and it is the one to enforce first.
4. **Metadata states standing, never substance.** A note may record *that* the
   record's standing changed and *where* to read why. It may not restate,
   qualify, narrow, or reinterpret the decision. If the sentence you want to
   write explains the decision differently, you are writing a new ADR.

### Migration

A one-time, **purely additive** format migration applies the block to ADR-0001
through ADR-0016. Because `adr-meta:end` is placed immediately above each
record's existing `## Context`, the seven `Namespec note (ADR-0008)` blocks fall
inside the new mutable region **with no text moved** — they are grandfathered as
conforming `Notes` in their original wording, retroactively legitimate rather
than retroactively edited. No decision content is touched by the migration.
`Amends` / `Amended-by` are populated only where a real relationship exists
(ADR-0014 ↔ ADR-0016); they are left `—` elsewhere rather than inferred.

### Enforcement (named, not yet built)

The single boundary makes a mechanical check cheap: digest the bytes after
`adr-meta:end` and flag any change on an accepted record. This is the natural
home for a legis policy at the git/CI boundary and is consistent with ADR-0002's
sign/lock regime for named definitional units. **Not wired in this record** —
naming it here so the next person does not redesign the boundary.

## Displaced constraints

**None constitutional.** No INV-nn is amended. INV-36 (append-only history;
corrections create new records) is the invariant this decision serves rather
than displaces: it moves an already-occurring practice from
outside the rules to inside them, under constraints that keep the causal history
intact.

`README.md`'s Tier-1 sentence is amended from *"immutable once accepted;
supersede, never edit"* to *"body immutable once accepted; supersede, never
edit — metadata block append-only, see ADR-0017."*

## Options considered

- **Sidecar metadata files** (`docs/adr/meta/0014.md`). Lost on discoverability:
  a reader who opens ADR-0014 must see that it is amended, and a sidecar they
  never open fails the only requirement that matters.
- **A central amendment ledger** (`docs/adr/AMENDMENTS.md`). Same failure, plus
  it becomes a second source of truth about ADR standing.
- **Status line only** (the current sanctioned form). Insufficient: it cannot
  carry a date, a cause, or the reading context that the Namespec notes exist to
  provide — which is why those notes were written into bodies instead.
- **A trailing amendment log as a second mutable region.** Rejected for two
  boundaries where one suffices; two regions doubles what a drift check must
  know and creates a "which one does this go in" question with no good answer.
- **Do nothing and keep violating the rule.** Rejected: an unenforced rule
  teaches that the ADR discipline is decorative, which is the failure mode this
  corpus can least afford.

## Consequences

- ADR-0014 can now carry `Amended-by: ADR-0016` with a dated note, and a reader
  landing on it cannot mistake the confirmatory claim for live.
- The seven Namespec notes become conforming rather than tolerated.
- New ADRs cost four boilerplate lines. `TEMPLATE.md` carries them.
- A future body-digest check has one boundary to verify. Until it is wired,
  rule 1 is honour-system — the same standing as most of this corpus's
  discipline pre-Phase-A, and worth stating plainly rather than implying
  enforcement that does not exist.
- **The failure mode to watch** is rule 4 eroding: notes that begin as pointers
  and grow into commentary that quietly re-argues the decision. If a `Notes`
  entry ever needs a second sentence, that is the signal it should have been an
  ADR.

## Reversal trigger

If any `Notes` entry is found restating or reinterpreting a decision rather than
its standing — rule 4 breached — this record returns to DECIDE, because the
mechanism will have become the silent-revision channel it was designed to
prevent.
