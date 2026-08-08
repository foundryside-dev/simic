# PDR-0015 — Skill/plugin roster becomes project-local; global enablement retired

Date: 2026-08-08   Status: accepted   Author: Claude (product-owner session)
Owner sign-off: yes — owner directed ("we're stepping away from everything
installed globally now we have a massive skill library") and adjudicated
the adversarial-architects inclusion in-session.
Related: PDR-0011 (roster), .claude/settings.json (commit 98ea01e), commit
history of the exclusion list in-session

## Context

PDR-0011's roster lived partly in global (~/.claude) enablement. The
owner is retiring global plugin enablement; anything simic needs must be
project-local or it silently vanishes.

## The call

`.claude/settings.json` now self-describes all three non-official
marketplace sources and enables the full roster locally — 44 plugins:
PDR-0011's set plus the previously-global load-bearers (superpowers ×2,
commit/review tooling, skill-creator, claude-md-management, feature-dev,
lyra-ux-designer, lyra-site-designer, axiom-devops-engineering, and — by
explicit owner call — **axiom-system-architect**, whose architecture-critic
pairs adversarially with axiom-solution-architect). Deliberately excluded
(context cost, no simic surface): axiom-web-backend,
ordis-security-architect, axiom-mcp-engineering, playwright,
security-guidance, typescript-lsp.

## Rationale

A fresh checkout must reproduce the working toolchain with zero global
state — the same self-sufficiency rule the repo applies to everything
else. Exclusions were filtered on PDR-0011's own context-bloat trigger
rather than blanket-mirroring.

## Reversal trigger

PDR-0011's stands (disable any pack whose triggering measurably degrades
sessions). Additionally: re-add an excluded pack the first time a simic
task actually reaches for it (e.g. axiom-mcp-engineering when an Oona MCP
surface is designed).
