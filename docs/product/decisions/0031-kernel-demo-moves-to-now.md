# PDR-0031 — Kernel demo moves Next → Now: plan panel-green, execution owner-authorized, task claimed

Date: 2026-08-10   Status: accepted   Author: Claude (product-owner session 13)
Owner sign-off: RECEIVED (parallel session, 2026-08-09/10) — plan acks D3 +
D11 recorded (6a4f17a); owner granted full execution autonomy ("stop
asking me for permission"), stop-points only for BLOCKED/load-bearing
calls and the GPU-checkpoint phases (memory: kernel-demo-full-autonomy).
Related: PDR-0029 (proof-of-concept purpose — stands), PDR-0028 (spec
provenance), roadmap.md

## Context

PDR-0029 placed the kernel demo in Next as a shaped bet "awaiting
sequencing against the burn-down and Phase A." Since then, in the owner's
parallel session: the implementation plan went through four review rounds
to rev 3.3 panel-green (86f25d8), execution mode was set to
subagent-driven, owner acks were recorded, and tracker task
**simic-4a44ed57c9** (P1, "Implement kernel demo per locked spec rev 6")
was claimed in_progress by claude-main. No code exists yet
(`experiments/` not created).

## The call

Recognize the horizon change as decided: the kernel demo is a **Now**
bet. This PDR is reconciliation, not a new sequencing decision — the
owner made the call by authorizing execution; the roadmap is updated to
match reality (Updated stamp cites this PDR). PDR-0029's reversal
trigger ("displaces burn-down/Phase A for more than one
session-equivalent *without owner direction*") did **not** trip: owner
direction is exactly what occurred.

## Rationale

The workspace must record intent that matches tracker reality; leaving
the demo in Next while a claimed P1 implementation task runs would make
the next session's RESUME false.

## Reversal trigger

Carried from PDR-0029, restated for the Now band: if demo execution
stalls BLOCKED for more than one session-equivalent awaiting owner input,
or if burn-down pace makes 2026-08-31 unreachable while demo work is the
displacing factor, the sequencing question returns to DECIDE with the
owner. The demo remains never-citable as §28 evidence.
