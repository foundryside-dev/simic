from experiments.kernel_demo import Config, run_selftest

GPU_ONLY_STEPS = ("determinism_probe", "det_mode_cost")


def test_selftest_runs_clean_cpu():
    res = run_selftest(Config(), "cpu")
    assert res["ok"]
    steps = res["steps"]
    assert isinstance(steps, dict)
    for name in GPU_ONLY_STEPS:
        assert steps[name]["status"] == "skipped", name  # skipped, not failed
    for name, step in steps.items():
        assert step["status"] in ("pass", "skipped"), (name, step)
