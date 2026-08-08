# PDR-0018 — Static-content review executed, implemented and merged; deploy now gated

Date: 2026-08-09   Status: accepted   Author: Claude (product-owner session)
Owner sign-off: not required — every outward-facing step was owner-directed
in-session ("review the static content including the wiki" → "implement
those changes" → "create a PR and merge it back to main remotely").
Related: ADR-0007, PDR-0014, PDR-0017, PR #2 (merge 6df7e7a), commits
6435f07, 7a92b61, b847980, 02564bb, d60e743

## Context

The owner requested a full design review of the static content (marketing
site + design-docs wiki), then implementation of the findings, then PR and
merge. Two independent review streams (site, wiki) produced 40+ findings
(1 Critical, 15 Major); implementation ran under a per-stream adversarial
review gate with browser verification and fix loops. The wiki gate caught
two shipped-broken Criticals the implementer's non-browser checks missed
(all 20 compiled diagrams 404ing; math dead after instant navigation) —
both fixed and browser-verified before merge.

## The call

Ship the full batch to main as one owner-directed merge, and make the
quality regime durable rather than one-shot: the deploy is now gated by
`html-validate@11` plus `tools/ci/linkcheck.py` (every internal link and
fragment of the assembled artifact), and the wiki build by
`tools/wiki/check_links.py` (every src/href/srcset in the built HTML — the
raw-HTML class `--strict` cannot see) and a diagram-palette check. Two
public-copy decisions ride along: the landing page no longer claims the
design is "complete" (now "locked … under active design review", dated),
and both surfaces are zero-third-party at runtime (wiki MathJax switched
to its SVG build so `material/privacy` vendors everything).

Accepted deferrals, recorded not dropped: border non-text contrast (needs
a palette decision); the generated design-system manifest divergence (re-
sync checklist in the skill readme); three minor linkcheck residues (all
fail-closed, listed in the review reports).

## Rationale

The site's strongest asset is that a hostile reader cannot fault its
honesty; "complete" was the one sentence that undercut it. The gates exist
because both Criticals were exactly the class local verification missed —
converting silent breakage into blocked deploys is the same fail-loud
discipline the HLD demands of the training system (ADR-0006 lineage).
Gate failure modes are confined to blocking a deploy, never shipping
broken content.

## Reversal trigger

If the deploy gates falsely block two clean deploys (failures traced to
gate strictness rather than genuine breakage), re-evaluate gate scope in a
superseding PDR. First live signal to watch: the first post-merge Pages
deploy — which also carries the dependabot pymdown-extensions 10.21→11.0.1
bump (PR #1, merged after PR #2, untested against the new staging code).
