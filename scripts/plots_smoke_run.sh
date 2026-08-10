#!/usr/bin/env bash
# Short end-to-end run for eyeballing the plotting sidecar's output.
#
# SCRATCH ROOT ONLY. `eval` is one-shot (kernel_demo.py: "eval refused:
# eval_results.json exists"), so this must never point at runs/kernel_demo —
# a demo run against the real store would consume the pre-registered eval.
set -euo pipefail

STORE="${STORE:-runs/plots-smoke}"
SUBSET="${SUBSET:-2000}"   # CIFAR train subset — dev-speed, honored by preflight/eval only
LIMIT="${LIMIT:-8}"        # collection episodes (real run: n_collect=300)
DEV="${DEV:-cuda:0}"

if [ "$STORE" = "runs/kernel_demo" ]; then
  echo "refusing: $STORE is the real store and eval is one-shot" >&2
  exit 2
fi

step() { echo; echo "=== $* ==="; }

# NOTE on --subset: it shrinks the CIFAR slice, NOT the episode counts, and
# `eval` has no episode lever at all (n_eval is frozen). At SUBSET=2000 the
# 2026-08-10 run reached preflight and was REFUSED at freeze — gates 1-5 fail
# because the planted signal does not separate on 4% of the train split
# (winner probe 0.20 against a 0.60 majority). That is the gates working. Do
# not lower a threshold to get past it; raise the subset, or accept that a
# gate-passing run is the real experiment (filigree simic-7c42fc9c0b).

step "A/B selftest"
uv run python -m experiments.kernel_demo selftest --store "$STORE" --device "$DEV"

step "C preflight (--freeze, subset=$SUBSET)"
uv run python -m experiments.kernel_demo preflight --freeze --subset "$SUBSET" --store "$STORE" --device "$DEV" --workers 2

step "D collect (limit=$LIMIT)"
uv run python -m experiments.kernel_demo collect --limit "$LIMIT" --store "$STORE" --devices "$DEV" --workers 2

step "E train"
uv run python -m experiments.kernel_demo train --store "$STORE" --device "$DEV"

step "F eval (subset=$SUBSET)"
uv run python -m experiments.kernel_demo eval --subset "$SUBSET" --store "$STORE" --device "$DEV"

step "plots"
uv run python -m experiments.kernel_demo_plots \
  --store "$STORE" \
  --results "$STORE/eval_results.json" \
  --namespace eval \
  --out "$STORE/plots"

echo
echo "store:  $STORE"
echo "plots:  $STORE/plots"
