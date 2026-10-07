# PDR-0040 — Claude takes over Simic and is given carriage to bring it to green

Date: 2026-10-08   Status: accepted   Author: Claude (session 17)
Owner sign-off: given in-session on 2026-10-08. This is a grant change on
`vision.md`'s escalate list, made at the owner's explicit direction.
Related: ADR-0018 (bounded reboot), PDR-0035/0038 (git-remote grant),
`simic-dda0d0188c` (reboot issue, reclaimed from `codex-astra`)

## Context

On 2026-10-04 Codex (`codex-astra`) implemented the bounded reboot
(ADR-0018), and a separate Codex reviewer accepted it. The work then stalled
for four days, for three reasons:

- An approved CPU pilot was withheld behind an OS-hard artifact quota that the
  host could not provide (`simic-e2f56cfbae`).
- Ten commits, including PDR-0039 and ADRs 0016–0018, never reached `main`.
- The product workspace still described the August kernel-demo queue.

The owner's words, in order, on 2026-10-08:

> "lift the cap, the server has hardware its an artificial constraint"
>
> "update the documentation … commit what needs to be commiited, clean out the
> tools that aren't aailbile anymore including wardline and the othe two"
>
> "you're taking over the project, merge it into main, and update all your
> findings - you have carriage to bring simic to green"

## Options

1. **Hand the issue back to Codex** and only document the queue. This repeats
   the stall that this session found.
2. **Take over for this session only**, merge, and return control. This leaves
   the next session without a clear owner.
3. **Standing ownership.** Claude owns the reboot issue and the product loop
   from here, inside the existing authority boundary.

## The call

Option 3. Claude is the implementing and owning agent for Simic from
2026-10-08. "Green" has a checkable meaning, recorded in `metrics.md`:

- `main` carries all the work;
- the full test suite passes;
- the documentation and tracker describe reality;
- no configured tool points at a binary that does not exist.

The authority grant gains one clause (`vision.md`, dated 2026-10-08). The
merge itself is inside the active bet, so the PDR-0035 clause already
licenses it. Everything on the escalate list stays reserved to the owner:
- vision changes;
- tags, releases and publication;
- GPU or paid campaigns;
- opening outer/test data;
- deleting run data.

## Rationale

Every blocker the session found was an artificial or administrative stall,
not a scientific one. The quota could never have bound: the pilot wrote
1.9 MB, against a 64 MiB cap. The branch had been reviewed and accepted but
never merged. The tools that failed had binaries that no longer exist. An
owner who can close those loops without a round-trip is worth more than
another handoff.

## Reversal trigger

The owner reassigns `simic-dda0d0188c`, or revokes the 2026-10-08 grant line.
Either one ends standing ownership immediately, and no further PDR is needed.
