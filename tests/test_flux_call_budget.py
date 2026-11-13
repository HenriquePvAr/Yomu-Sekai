"""FLUX launches are capped per job and the sd-cli timeout is bounded by configuration."""
from unittest import mock

import numpy as np

from komyst.clean.inpainting import flux_edit


def _call(**kwargs):
    with mock.patch.object(flux_edit, "available", return_value=True), \
            mock.patch.object(flux_edit, "_run_reference_edit", return_value=None) as run:
        metrics = {}
        flux_edit.flux_reference_edit(
            np.zeros((8, 8, 3), np.uint8), prompt=str(np.random.rand()), telemetry=metrics, **kwargs)
    return run, metrics


def test_call_cap_stops_the_next_launch_and_reset_reopens_it():
    flux_edit.reset_call_budget()
    with mock.patch.object(flux_edit.settings, "GENERATIVE_INPAINT_MAX_CALLS_PER_JOB", 2), \
            mock.patch.object(flux_edit, "_model_dir", return_value=__import__("pathlib").Path(".")), \
            mock.patch("pathlib.Path.stat", return_value=mock.Mock(st_size=1, st_mtime_ns=1)), \
            mock.patch("pathlib.Path.resolve", side_effect=lambda: __import__("pathlib").Path(".")):
        launched = [_call()[0].call_count for _ in range(3)]
        assert launched == [1, 1, 0]
        assert _call()[1]["reason"] == "generative_call_cap_reached"
        flux_edit.reset_call_budget()
        assert _call()[0].call_count == 1
    flux_edit.reset_call_budget()


def test_timeout_is_bounded_by_the_configured_ceiling():
    flux_edit.reset_call_budget()
    with mock.patch.object(flux_edit.settings, "GENERATIVE_INPAINT_TIMEOUT_SECONDS", 120.0), \
            mock.patch.object(flux_edit, "_model_dir", return_value=__import__("pathlib").Path(".")), \
            mock.patch("pathlib.Path.stat", return_value=mock.Mock(st_size=1, st_mtime_ns=1)), \
            mock.patch("pathlib.Path.resolve", side_effect=lambda: __import__("pathlib").Path(".")):
        run, _ = _call(timeout_seconds=240.0)
        assert run.call_args.args[4] == 120.0
        run, _ = _call(timeout_seconds=30.0)
        assert run.call_args.args[4] == 30.0
    flux_edit.reset_call_budget()
