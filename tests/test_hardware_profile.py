import json
import unittest
from unittest import mock

from komyst.runtime import hardware_profile as hp


def d(ram, vram, free=None):
    return {"ram_total_gb": ram, "ram_free_gb": free, "gpu_vram_gb": vram}


class SelectProfileTests(unittest.TestCase):
    def test_detection_table(self):
        cases = [
            (d(8, 8), "leve"), (d(16, None), "leve"), (d(None, None), "leve"),
            (d(16, 2), "leve"), (d(12, 4), "equilibrado"), (d(16, 6), "equilibrado"),
            (d(32, 6), "equilibrado"), (d(24, 8), "qualidade"), (d(64, 24), "qualidade"),
            (d(11.9, 24), "leve"), (d(None, 24), "leve"),
            (d(31.4, 7.98), "qualidade"), (d(16, 3.99), "equilibrado"),  # real 8 GB / 4 GB cards
        ]
        for detected, expected in cases:
            with self.subTest(detected=detected):
                self.assertEqual(hp.select_profile(detected, "auto"), expected)

    def test_manual_override_wins(self):
        self.assertEqual(hp.select_profile(d(64, 24), "leve"), "leve")
        self.assertEqual(hp.select_profile(d(4, None), " Qualidade "), "qualidade")

    def test_invalid_override_is_auto(self):
        self.assertEqual(hp.select_profile(d(64, 24), "turbo"), "qualidade")


class ResolveTests(unittest.TestCase):
    def test_explicit_env_beats_profile(self):
        env = {"PIPELINE_PAGE_WORKERS": "4", "CLEAN_COMPARE_FILLS": "1"}
        s = hp.resolve(env, d(8, None))
        self.assertEqual(s["profile"], "leve")
        self.assertNotIn("PIPELINE_PAGE_WORKERS", s["applied"])
        self.assertEqual(s["overridden_by_env"]["PIPELINE_PAGE_WORKERS"], "4")
        self.assertEqual(s["applied"]["OCR_RESIDUAL_SWEEP_MODE"], "off")

    def test_never_enables_flux_and_qualidade_keeps_auto_workers(self):
        s = hp.resolve({}, d(64, 24))
        self.assertNotIn("GENERATIVE_INPAINT_ENABLED", s["applied"])
        self.assertNotIn("PIPELINE_PAGE_WORKERS", s["applied"])
        self.assertEqual(hp.resolve({}, d(16, 6))["applied"]["PIPELINE_PAGE_WORKERS"], "2")

    def test_manual_profile_skips_detection(self):
        with mock.patch.object(hp, "detect", side_effect=AssertionError):
            s = hp.resolve({"HARDWARE_PROFILE": "equilibrado"})
        self.assertEqual(s["profile"], "equilibrado")
        self.assertIn("manual", s["reason"])

    def test_detect_degrades_without_psutil_or_gpu(self):
        with mock.patch.dict("sys.modules", {"psutil": None}), \
                mock.patch.object(hp.subprocess, "run", side_effect=OSError), \
                mock.patch("komyst.runtime.resource_monitor.detect_gpu_basic", side_effect=RuntimeError):
            detected = hp.detect()
        self.assertEqual(hp.select_profile(detected), "leve")

    def test_apply_writes_env_once_and_state_round_trips(self):
        env = {"HARDWARE_PROFILE": "leve", "CLEAN_COMPARE_FILLS": "1"}
        s = hp.apply_to_environ(env)
        self.assertEqual(env["PIPELINE_PAGE_WORKERS"], "1")
        self.assertEqual(env["CLEAN_COMPARE_FILLS"], "1")
        self.assertEqual(json.loads(env[hp.STATE_ENV])["profile"], "leve")
        self.assertEqual(hp.apply_to_environ(env), s)

    def test_hermetic_env_is_untouched_when_auto(self):
        env = {"KOMYST_HERMETIC_TEST_ENV": "1"}
        self.assertEqual(hp.apply_to_environ(env)["profile"], "none")
        self.assertEqual(set(env), {"KOMYST_HERMETIC_TEST_ENV"})


if __name__ == "__main__":
    unittest.main()


class StaleProfileStateTests(unittest.TestCase):
    """A profile state inherited from a parent must not outlive a changed HARDWARE_PROFILE."""

    DETECTED = {"ram_total_gb": 32, "ram_free_gb": 16, "gpu_vram_gb": 8}

    def test_changed_override_replaces_the_inherited_state_and_its_values(self):
        env = {}
        with mock.patch.object(hp, "detect", return_value=self.DETECTED):
            first = hp.apply_to_environ(env)  # auto -> qualidade
            self.assertEqual(first["profile"], "qualidade")
            env["HARDWARE_PROFILE"] = "leve"
            second = hp.apply_to_environ(env)
        self.assertEqual(second["profile"], "leve")
        self.assertEqual(env["PIPELINE_PAGE_WORKERS"], "1")
        self.assertEqual(env["OCR_RESIDUAL_SWEEP_MODE"], "off")
        self.assertEqual(second["overridden_by_env"], {})

    def test_user_value_set_before_the_first_profile_still_wins(self):
        env = {"PIPELINE_PAGE_WORKERS": "3", "HARDWARE_PROFILE": "leve"}
        with mock.patch.object(hp, "detect", return_value=self.DETECTED):
            state = hp.apply_to_environ(env)
        self.assertEqual(env["PIPELINE_PAGE_WORKERS"], "3")
        self.assertEqual(state["overridden_by_env"], {"PIPELINE_PAGE_WORKERS": "3"})

    def test_unchanged_state_is_reused(self):
        env = {}
        with mock.patch.object(hp, "detect", return_value=self.DETECTED) as detect:
            hp.apply_to_environ(env)
            hp.apply_to_environ(env)
        self.assertEqual(detect.call_count, 1)
