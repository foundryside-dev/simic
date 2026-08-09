# PDR-0023 — Dependabot cryptography alert: wait for upstream, never override the cap

Date: 2026-08-09   Status: accepted   Author: Claude (product-owner session 11)
Owner sign-off: bump approved 2026-08-09 ("1-3 all approved"); the bump
proved unsatisfiable, deferral recorded same session. The optional
alert-dismissal remains owner-gated (external state change).
Related: GitHub Dependabot alert #1, simic-b67434134e

## Context

Dependabot alert #1 (high): cryptography ≥44,<50 exposes a PKCS#7
Bleichenbacher oracle; patched in 50.0.0. uv.lock resolves 49.0.0 via
mlflow → google-auth. The owner approved a bump, but mlflow 3.15.1 — the
latest release — declares `cryptography>=43,<50`, making every resolution
to 50.0.0 unsatisfiable.

## The call

Wait for upstream; do not force `tool.uv.override-dependencies`. The
blockage and the exact unblock procedure are tracked as simic-b67434134e
(bump on the first mlflow release that lifts the cap; verify the alert
auto-resolves). The alert itself stays open unless the owner chooses to
dismiss it in the GitHub UI as "vulnerable code not in use".

## Rationale

Overriding a dependency's declared upper bound blind is the shim class this
project bans (No Legacy Code carryover): it trades a visible warning for an
invisible compatibility risk. Practical exposure is ~nil — a pre-code repo,
nothing decrypts PKCS#7, mlflow is a declared future dependency with no
executed path — so the honest posture is a tracked wait, not a forced pin.

## Reversal trigger

Escalate and revisit immediately if (a) any code path that parses PKCS#7 /
CMS content lands in the repo before the bump, or (b) the alert's scope
widens beyond EnvelopedData decryption. Otherwise simic-b67434134e executes
mechanically on the first permitting mlflow release.
