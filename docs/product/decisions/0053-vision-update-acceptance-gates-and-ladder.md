# PDR-0053 — Vision update: the acceptance-gate clause is split by level; the ladder and its evidence are written into the vision

Date: 2026-10-09   Status: accepted (owner-directed); **ratification pending**   Author: Claude (session 17)
Owner sign-off: the owner directed the update (*"ok, please update the
vision"*), replying to Claude's note that `vision.md`'s carried-over clause
read differently from PDR-0050's window. The split text below has not yet
been read back to the owner.
Related: PDR-0038 (grant ratified), PDR-0040 (handover), PDR-0050 (ladder,
GPU window), PDR-0051, PDR-0052; `docs/product/vision.md`

## Context

The authority grant carried over a line from esper-lite's grant:
"Pre-registered acceptance gates stay owner-gated." Since PDR-0050, Claude
has written, reviewed and launched per-study pre-registered plans inside
the GPU window: PDR-0051 and PDR-0052, each with three Fable reviews and a
gating dry run. The owner directed the work ("proceed autonomously with
fable reviews"), so practice was settled, but the text was not. The
PDR-0052 product critique flagged the ambiguity, and it was surfaced to the
owner rather than edited.

The vision also predated the ladder. Its strategy lived only in PDR-0050
and `roadmap.md`, and its first claim (Purpose) names static
over-provisioning as a comparator, which rung 3 has now measured.

## Options

1. **Literal.** Every pre-registered reading rule needs owner sign-off.
   This is safe, but it stalls the ladder inside a time-limited GPU window
   and contradicts the owner's direction.
2. **Delete the line.** This is fast, but it loses the real protection,
   which is that the *programme's* gates must not move without the owner.
3. **Split by level (chosen).** Programme-level gates stay owner-gated.
   Per-study plans inside an approved rung are Claude's, under mandatory
   independent review, a gating dry run and a launch-time hash freeze. The
   owner keeps a veto before launch and a reversal after.

## The call

Option 3. The vision now says:
- **Programme-level gates stay owner-gated.** These are:
  - the success criteria of `docs/design/01-claim.md#28-success-criteria`;
  - the ladder's rungs;
  - each rung's stop condition, recorded in the owner-signed DECIDE PDR that
    opens the rung;
  - any reading that would treat a stopped rung as passed or move a gate
    after its data is seen.

  Host, seed type and horizon are rung parameters. Floor and reading rule
  are plan parameters, as PDR-0049 delegated the floor.
- **Per-study plans and reading rules are Claude's to author.** Each is a
  PDR, independently reviewed before launch, dry-run gated, and frozen by
  hash. A published reading is never re-read.

Two other changes:
- **A "Strategy now" section** records the ladder as the sequencing
  authority and the evidence through rung 3. It says plainly that static
  over-provisioning beats the scheduled graft at bounded scale: a recorded
  negative for that comparison in the first claim, not a refutation of the
  claim.
- **"Once Tolaria exists"** in the run-authorisation line now also covers
  today's bounded-ladder runs, which is how runs have actually been
  launched since PDR-0044.

## Rationale

The protection the esper-lite line was meant to give is that nobody moves
the goalposts. That is kept at the level where it matters, and
strengthened: "move a gate after its data is seen" is now named
explicitly. The per-study process the owner endorsed, with independent
review, dry run and hash freeze, is now the written rule rather than an
in-session understanding. The evidence paragraph keeps the vision honest
about where the first claim stands, so a future session cannot read
"static wins" as progress.

## Reversal trigger

- The owner says any per-study plan must come to them first. Revert to
  option 1 for that class of study.
- A per-study plan is found to have moved a programme-level gate. The
  review process failed: tighten it, and record which gate moved.
- Rung 4 or later reverses the static-over-provisioning finding. Rewrite
  the evidence paragraph from the new records, as an owner-signed vision
  update, never at checkpoint, and never by softening the old one.

## Pre-merge critique (Fable product-decision critic)

The critique returned SHIP-WITH-CHANGES. All ten text fixes were applied:
- a reversal trigger that self-granted a future vision edit;
- a status line claiming a read-back that had not happened;
- a false "nothing else changed";
- stop conditions attributed to PDR-0050, which has none;
- a pooled 0/240 that no record states;
- precision and cost wording in the evidence paragraph.

Three items go to the owner at read-back:
- whether a live evidence summary belongs in the vision;
- how much pre-launch visibility the owner wants;
- ratification of the split, including that the rung-4 DECIDE PDR's stop
  condition is owner-signed.
