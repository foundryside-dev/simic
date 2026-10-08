"""Bounded engineering acceptance, not evidence of growth superiority."""

import copy
import dataclasses
import json

import pytest
import torch

from experiments import bounded_comparison as runner
from experiments import bounded_data
from experiments.bounded_data import RunSpec, smoke_split, tensor_hash
from experiments.kernel_demo import (
    CommonFuture,
    DataBundle,
    EpisodeCtx,
    Slot,
    Stage,
    build_host,
    build_optimizer,
    derive,
    make_generator,
    normalize_u8,
    state_hash,
    train_one_epoch,
)


@pytest.mark.parametrize(
    "changes",
    [
        {"epochs": 6},
        {"graft_epoch": -1},
        {"graft_epoch": 7},
        {"train_size": 33},
        {"batch_size": 0},
        {"dev_size": 0},
        {"outer_size": 10001},
        {"train_size": True},
        {"threads": True},
        {"lr": float("nan")},
        {"tau": float("inf")},
        {"seed": -1},
        {"stage_k": 0},
        {"data": "network"},
    ],
)
def test_spec_refuses_incomplete_lifecycle_or_invalid_inputs(changes):
    with pytest.raises(ValueError):
        dataclasses.replace(RunSpec(), **changes).validate()


def test_smoke_is_learnable_independent_and_reproducible():
    spec = RunSpec()
    fit, dev, outer = (smoke_split(spec, split) for split in ("fit", "dev", "outer"))
    assert tensor_hash(*fit) == tensor_hash(*smoke_split(spec, "fit"))
    assert len({tensor_hash(*pair) for pair in (fit, dev, outer)}) == 3
    # Labels describe image content, rather than unrelated random labels.
    for x, y in (fit, dev, outer):
        assert x[y == 0, 0].float().mean() > x[y == 0, 1].float().mean() + 100
        assert x[y == 1, 1].float().mean() > x[y == 1, 0].float().mean() + 100


def test_scoring_is_sample_weighted_and_preserves_state_rng_and_modes():
    torch.set_num_threads(1)
    spec = RunSpec(dev_size=65)
    x, y = smoke_split(spec, "dev")
    host, slot = build_host("mild", 2), runner.ScaleAwareSlot(RunSpec())
    host.attach_stat_hooks()
    host.stage1[1].eval()  # Nonuniform submodule modes must survive.
    modes = [m.training for m in host.modules()]
    before, rng, stats = state_hash(host), torch.get_rng_state().clone(), copy.deepcopy(host.stage_stats)
    a = runner.score(host, slot, x, y, 32)
    b = runner.score(host, slot, x, y, 65)
    assert a["ce"] == pytest.approx(b["ce"], abs=1e-6)
    assert a["accuracy"] == b["accuracy"]
    assert a["examples"] == 65
    assert state_hash(host) == before and torch.equal(rng, torch.get_rng_state())
    assert modes == [m.training for m in host.modules()]
    assert host.stage_stats == stats


def test_birth_preserves_momentum_and_pairs_body_initialization():
    spec = RunSpec(epochs=7)
    runner.configure(spec)
    tx, ty = smoke_split(spec, "fit")
    dx, _ = smoke_split(spec, "dev")
    host = build_host("mild", derive(spec.seed, "host-init"))
    slot, opt = runner.ScaleAwareSlot(RunSpec()), build_optimizer(host, spec.kernel_config())
    future = CommonFuture.draw(derive(spec.seed, "common-future"), len(ty), spec.epochs, spec.kernel_config())
    runner.train_epoch(host, slot, opt, spec, future, tx, ty, 0)
    assert any("momentum_buffer" in value for value in opt.state.values())
    before = runner.optimizer_host_hash(opt)
    scheduled = runner.attach_seed(host, slot, opt, spec, dx, static=False)
    assert runner.optimizer_host_hash(opt) == before
    fresh = build_host("mild", derive(spec.seed, "host-init"))
    static_slot = runner.ScaleAwareSlot(RunSpec())
    static = runner.attach_seed(fresh, static_slot, build_optimizer(fresh, spec.kernel_config()), spec, dx, static=True)
    assert scheduled["body_init_sha256"] == static["body_init_sha256"]
    assert static["gain_at_birth"] != scheduled["gain_at_birth"]
    assert static_slot.alpha == static_slot.beta == 1 and static_slot.stage is Stage.FOSSILIZED
    with pytest.raises(RuntimeError, match="one lifetime"):
        runner.attach_seed(host, slot, opt, spec, dx, static=False)


def test_no_growth_matches_legacy_production_host_and_optimizer_exactly():
    spec = RunSpec(epochs=7)
    runner.configure(spec)
    tx, ty = smoke_split(spec, "fit")
    dx, dy = smoke_split(spec, "dev")
    future = CommonFuture.draw(derive(spec.seed, "common-future"), len(ty), spec.epochs, spec.kernel_config())
    hosts = [build_host("mild", derive(spec.seed, "host-init")) for _ in range(2)]
    legacy_slot, bounded_slot = Slot(), runner.ScaleAwareSlot(spec)  # legacy kernel slot vs the bounded runner's slot
    opts = [build_optimizer(host, spec.kernel_config()) for host in hosts]
    hosts[0].attach_stat_hooks()
    legacy = EpisodeCtx(
        spec.kernel_config(),
        DataBundle(tx, ty, dx, dy, torch.empty(0), torch.empty(0)),
        "cpu",
        spec.seed,
        "mild",
        future,
        hosts[0],
        opts[0],
        legacy_slot,
        [],
        [],
        None,
        False,
    )
    train_one_epoch(legacy, 0)
    runner.train_epoch(hosts[1], bounded_slot, opts[1], spec, future, tx, ty, 0)
    assert state_hash(hosts[0]) == state_hash(hosts[1])
    assert runner.optimizer_host_hash(opts[0]) == runner.optimizer_host_hash(opts[1])


@pytest.mark.parametrize("stage,alpha,beta", [(Stage.TRAINING, 0.0, 0.0), (Stage.BLENDING, 0.5, 0.0), (Stage.FOSSILIZED, 1.0, 1.0)])
def test_ce_alone_updates_seed_body_and_gain(stage, alpha, beta):
    spec = RunSpec(epochs=7)
    runner.configure(spec)
    tx, ty = smoke_split(spec, "fit")
    dx, _ = smoke_split(spec, "dev")
    host, slot = build_host("mild", derive(spec.seed, "host-init")), runner.ScaleAwareSlot(RunSpec())
    opt = build_optimizer(host, spec.kernel_config())
    runner.attach_seed(host, slot, opt, spec, dx, static=False)
    slot.stage, slot.alpha, slot.beta = stage, alpha, beta
    assert slot.seed is not None
    body_before = runner.parameter_hash(slot.seed, body_only=True)
    gain_before = float(slot.seed.gain.detach())
    # Deliberately omit trust-region regularization: evidence is task-loss credit.
    ce = torch.nn.functional.cross_entropy(host(normalize_u8(tx[:32]), slot), ty[:32])
    opt.zero_grad(set_to_none=True)
    ce.backward()  # type: ignore[no-untyped-call]
    assert runner.grad_norm(p for n, p in slot.seed.named_parameters() if n != "gain") > 0
    assert runner.grad_norm([slot.seed.gain]) > 0
    opt.step()
    assert runner.parameter_hash(slot.seed, body_only=True) != body_before
    assert float(slot.seed.gain.detach()) != gain_before


def test_prefix_gradient_isolation_and_recoupling():
    spec = RunSpec()
    runner.configure(spec)
    dx, _ = smoke_split(spec, "dev")
    host, slot = build_host("mild", 1), runner.ScaleAwareSlot(RunSpec())
    runner.attach_seed(host, slot, build_optimizer(host, spec.kernel_config()), spec, dx, static=False)
    for stage, alpha, beta in [(Stage.TRAINING, 0.0, 0.0), (Stage.BLENDING, 0.5, 0.0), (Stage.FOSSILIZED, 1.0, 1.0)]:
        slot.stage, slot.alpha, slot.beta = stage, alpha, beta
        h = torch.ones(2, 64, 8, 8, requires_grad=True)
        weighted = torch.arange(h.numel()).reshape_as(h).float() / h.numel()
        (slot(h) * weighted).sum().backward()
        assert h.grad is not None
        if beta == 0:
            assert torch.equal(h.grad, weighted)
        else:
            assert not torch.equal(h.grad, weighted)


def test_full_state_identity_sees_seed_momentum_and_lifecycle():
    spec = RunSpec(epochs=7)
    runner.configure(spec)
    dx, _ = smoke_split(spec, "dev")
    host, slot = build_host("mild", 1), runner.ScaleAwareSlot(RunSpec())
    opt = build_optimizer(host, spec.kernel_config())
    runner.attach_seed(host, slot, opt, spec, dx, static=False)
    assert slot.seed is not None
    before = runner.training_state_hash(host, slot, opt)
    slot._blend_step += 1
    assert runner.training_state_hash(host, slot, opt) != before
    slot._blend_step -= 1
    assert runner.training_state_hash(host, slot, opt) == before
    opt.state[slot.seed.gain]["momentum_buffer"] = torch.ones_like(slot.seed.gain)
    assert runner.training_state_hash(host, slot, opt) != before


@pytest.fixture(scope="module")
def completed_run(tmp_path_factory):
    root = tmp_path_factory.mktemp("bounded") / "run"
    runner.train(RunSpec(epochs=7), root)
    return root


def test_training_evidence_and_real_gradient_parameter_learning(completed_run):
    manifest, complete, spec = runner.verify_run(completed_run)
    assert not (completed_run / "outer_evaluation.json").exists()
    assert manifest["common_future_sha256"]
    summaries = complete["summaries"]
    assert summaries["no_growth"]["final_parameters"] == 142006
    for arm in runner.ARMS:
        assert summaries[arm]["host_parameters_changed"]
        assert summaries[arm]["development_ce_decreased"]
        assert summaries[arm]["gradient_norm_max"]["host"] > 0
        assert summaries[arm]["costs"]["host_train_examples"] == spec.train_size * spec.epochs
    for arm in ("static", "scheduled"):
        summary = summaries[arm]
        assert summary["final_parameters"] == 150903
        assert summary["seed_body_changed"] and summary["seed_gain_changed"]
        assert summary["gradient_norm_max"]["seed_body"] > 0 and summary["gradient_norm_max"]["seed_gain"] > 0
        assert summary["costs"]["calibration_examples"] == 32
        assert summary["costs"]["fully_coupled_optimizer_steps"] > 0
    records = [json.loads(line) for line in (completed_run / "training.jsonl").read_text().splitlines()]
    base = [r for r in records if r["arm"] == "no_growth" and r["kind"] == "epoch"]
    grown = [r for r in records if r["arm"] == "scheduled" and r["kind"] == "epoch"]
    # Dormancy and STE pretraining have exact host/no-growth parity.
    for epoch in range(spec.graft_epoch + spec.stage_k):
        assert base[epoch]["host_state_sha256"] == grown[epoch]["host_state_sha256"]
    assert grown[spec.graft_epoch]["seed_executed_train_examples"] == spec.train_size
    assert grown[spec.graft_epoch]["alpha_used_max"] == 0


def test_training_never_requests_outer_data(tmp_path, monkeypatch):
    calls = []
    actual = bounded_data.smoke_split

    def spy(spec, split):
        calls.append(split)
        assert split != "outer"
        return actual(spec, split)

    monkeypatch.setattr(bounded_data, "smoke_split", spy)
    runner.train(RunSpec(epochs=7, train_size=32, dev_size=32, batch_size=32), tmp_path / "run")
    assert calls == ["fit", "dev"]


def test_outer_independent_learning_and_overwrite_refusal(completed_run):
    result = runner.evaluate(completed_run)
    assert result["claim_scope"] == "engineering-smoke-only"
    assert result["superiority_established"] is False
    assert all(result["heldout_learning_acceptance"].values())
    assert all(score["examples"] == 128 for score in result["scores"].values())
    with pytest.raises(FileExistsError):
        runner.evaluate(completed_run)


@pytest.mark.parametrize("artifact", ["scheduled.pt", "training.jsonl", "manifest.json"])
def test_corruption_refused_before_outer_access(completed_run, tmp_path, monkeypatch, artifact):
    import shutil

    root = tmp_path / "copy"
    shutil.copytree(completed_run, root)
    (root / "outer_evaluation.json").unlink(missing_ok=True)
    with (root / artifact).open("ab") as fh:
        fh.write(b"corruption")

    def forbidden(*args):
        pytest.fail("outer data accessed before corruption refusal")

    monkeypatch.setattr(runner, "load_outer", forbidden)
    with pytest.raises(ValueError, match="checksum"):
        runner.evaluate(root)


def test_missing_completion_and_existing_output_refused(tmp_path):
    with pytest.raises(FileNotFoundError):
        runner.evaluate(tmp_path)
    with pytest.raises(FileExistsError):
        runner.train(RunSpec(), tmp_path)


@pytest.mark.parametrize("payload", ['{"a":1,"a":2}', '{"a":NaN}', '{"a":1e999}', "[]"])
def test_json_ingress_is_strict(tmp_path, payload):
    path = tmp_path / "corrupt.json"
    path.write_text(payload)
    with pytest.raises(ValueError):
        runner.read_json(path)


def test_manifest_boolean_schema_refused(completed_run, tmp_path):
    import shutil

    root = tmp_path / "copy"
    shutil.copytree(completed_run, root)
    manifest_path = root / "manifest.json"
    manifest = json.loads(manifest_path.read_text())
    manifest["schema_version"] = True
    manifest_path.write_text(json.dumps(manifest))
    completion = json.loads((root / "complete.json").read_text())
    completion["artifacts"]["manifest.json"] = bounded_data.file_hash(manifest_path)
    (root / "complete.json").write_text(json.dumps(completion))
    with pytest.raises(ValueError, match="schema"):
        runner.verify_run(root)


@pytest.mark.parametrize("field", ["gradient_norm_max", "training_state_sha256", "dev", "stage_used"])
def test_hash_sealed_missing_evidence_refused_before_outer(completed_run, tmp_path, monkeypatch, field):
    import shutil

    root = tmp_path / "copy"
    shutil.copytree(completed_run, root)
    (root / "outer_evaluation.json").unlink(missing_ok=True)
    path = root / "training.jsonl"
    records = [json.loads(line) for line in path.read_text().splitlines()]
    del records[1][field]
    path.write_text("".join(json.dumps(record) + "\n" for record in records))
    complete = json.loads((root / "complete.json").read_text())
    complete["artifacts"]["training.jsonl"] = bounded_data.file_hash(path)
    (root / "complete.json").write_text(json.dumps(complete))
    monkeypatch.setattr(runner, "load_outer", lambda *args: pytest.fail("outer accessed with missing evidence"))
    with pytest.raises(ValueError, match="required evidence"):
        runner.evaluate(root)


def test_missing_summary_cost_refused(completed_run, tmp_path):
    import shutil

    root = tmp_path / "copy"
    shutil.copytree(completed_run, root)
    path = root / "complete.json"
    complete = json.loads(path.read_text())
    del complete["summaries"]["scheduled"]["costs"]["seed_train_examples"]
    path.write_text(json.dumps(complete))
    with pytest.raises(ValueError, match="required evidence"):
        runner.verify_run(root)


def test_process_rng_pin_ignores_ambient_startup_state():
    spec = RunSpec()
    torch.set_rng_state(make_generator(1).get_state())
    runner.configure(spec)
    expected = torch.get_rng_state().clone()
    torch.set_rng_state(make_generator(999).get_state())
    runner.configure(spec)
    assert torch.equal(expected, torch.get_rng_state())
