# Current State — Simic        Checkpoint: 2026-10-08 (session 17)

## Who owns this now
Claude, since 2026-10-08 (PDR-0040). John's words: *"you're taking over the
project, merge it into main, and update all your findings - you have carriage
to bring simic to green."* The authority grant in `vision.md` has a dated line
for this handover. Everything on the escalate list stays reserved to John:
- vision changes;
- tags, releases and publication;
- GPU or paid campaigns;
- opening outer/test data;
- deleting run data.

## The bet right now
**One Now bet: the bounded structural comparison** (ADR-0018, PDR-0043). One
fixed host, the `conv_light` seed, three arms: no growth, static extra capacity
from step zero, and a scheduled graft. Training and outer evaluation run as
separate commands. The question: does the structural intervention earn its
cost against *both* controls, before any controller exists?

**First real reading (2026-10-08, PDR-0041):** CPU pilot, one paired seed,
1,024 fit / 256 dev CIFAR-10, ten epochs, 59 s.
- All three arms reduced development CE: no growth 2.306→1.691, static
  →1.605, scheduled →1.722.
- One seed cannot separate them. Arm differences are ≤0.12 CE, while a single
  epoch swings by up to 0.47 within one arm.
- The pairing machinery is verified: the scheduled and no-growth host hashes
  match exactly through the end of the invisible STE epoch.
- Write-up: `docs/results/2026-10-08-bounded-cpu-pilot.md`.

Two readings so far (the synthetic fixture and this pilot) both rank static
capacity first. **Neither is evidence**, but ADR-0018's reopen trigger is
"static control wins at the declared cost". The next screen has to be able to
read that trigger.

## Green status (the PDR-0040 guardrail)
- **`main` carries all accepted work:** yes, after this session's merge PR. The
  ten commits from 2026-08-11 to 2026-10-04 (PDR-0039, ADR-0016/0017/0018, the
  concept panel, the related-work map, the bounded comparison) had never
  reached `main`.
- **Full `tests/` suite:** 205 passed, 3 skipped in 7 min on the pre-removal
  code. The 3 skips were the Wardline scanner witnesses, since deleted. The
  post-removal run is recorded in the merge PR. This is the first full pass
  recorded since the reboot: Codex's 2026-10-04 broad run was interrupted. The
  two collect tests take ~3 min of the 7.
- **No tool points at a missing binary:** yes. Legis, Wardline and Warpline
  were removed from `.mcp.json`, the SessionStart hooks, the skills, `weft.toml`
  and `AGENTS.md`. The bounded comparison no longer depends on `weft-markers`
  (PDR-0042).
- **This file describes reality:** as of this checkpoint.

## DECISION QUEUE

**For John (owner-gated):**
- **Q1 — Outer evaluation** of any bounded run. This is the one-shot terminal
  score, and it stays owner-gated. Nothing has asked for it yet: the pilot was
  development-only, and the next screen should be too.

**For Claude (within the grant), in order:**
1. **Propose the multi-seed development screen** (`simic-7486bc6929`). Record
   the proposal as a PDR before running, with:
   - seed count;
   - endpoint, preferably the paired CE difference over the last k epochs,
     given the single-epoch noise;
   - budget: ~1 CPU-min per seed, so 16 seeds is ~16 min serial or ~2 min
     parallel on nyx;
   - the pre-committed reading against ADR-0018's reopen trigger.

   Design it with the counterfactual-statistics skill. The grant's run
   authorization covers running it once recorded.
2. **The ready queue was re-triaged this session.** 35 pre-reboot HLD and
   kernel-demo items now depend on the evidence gate `simic-6f4f111ec8`
   ("the bounded screen reports"). They are paused, not closed, so `filigree
   ready` shows only real next work. To unpark an item early, remove its
   dependency and record why.
3. **When Wardline returns:** `simic-2035316005` (re-mark the bounded seams;
   reference `c40972d`).

## Parked, with re-entry conditions
- **Design hardening and Phase A.** 31 open / 23 closed `hld-review` items,
  unchanged since 2026-08-10. The fired 2026-09-30 date was un-dated, not
  moved (PDR-0043). Re-entry: the bounded screen reports.
- **Kernel demo campaign** (`simic-7c42fc9c0b`, Task 19B/19C
  `simic-e3ad55344f` / `simic-0fd4fcb933`, PR #13's rev 6.2). Preflight failed
  gates 1–5 in August and never froze. Re-entry: its own DECIDE.
- **ADR-0002 regime** (`simic-357c92664c`). Plainweave seeding wants John
  present. Rides with Phase A.

## Session 17 did
- Resumed from a four-day stall. Codex had built and reviewed the bounded
  reboot on 2026-10-04 but withheld the approved pilot over an unenforceable
  64 MiB OS quota. John lifted the cap; the pilot ran (PDR-0041).
- Retired the three unavailable Weft tools and removed the `weft-markers`
  runtime pin. That pin re-hashed a file inside the Wardline checkout at every
  run, so the Wardline rebuild would have broken the experiment (PDR-0042).
- Re-based the roadmap (PDR-0043); recorded the handover (PDR-0040).
- Updated AGENTS.md, README, CHANGELOG, `metrics.md`, `vision.md` and the
  bounded-comparison guide. AGENTS.md's esper paths now point at
  `/mnt/data/archive/`.
- Tracker:
  - `simic-dda0d0188c` reclaimed from `codex-astra`;
  - 35 paused items gated behind `simic-6f4f111ec8`;
  - `simic-e2f56cfbae` closed with John's words;
  - `simic-7486bc6929` (screen proposal) and `simic-2035316005` (re-mark
    seams) opened.

## Local-only state worth knowing
- Pilot checkpoints: `runs/bounded-pilot-2026-10-08/*.pt` (gitignored;
  checksums in the archived `complete.json`).
- Training-only CIFAR view: `runs/cifar-fit-only/`, which holds symlinks to the
  five training batches and the metadata, and no `test_batch`. Reuse it for
  every development run so outer data stays physically absent.
- `.weft/{legis,wardline,warpline}/` and `.wardline/`: ignored local state from
  the retired tools. Left in place, because deleting what may be an audit trail
  is owner-reserved.
- Codex's October 4 reports and preservation archive:
  `/home/john/Documents/Codex/2026-10-04/task-7/`.
