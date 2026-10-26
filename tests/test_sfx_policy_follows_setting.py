"""Translated sound effects are the configured behaviour, not a policy violation.

Every chapter failed with translation_policy_violation once TRANSLATE_SFX became
the default, because the gate still treated "SFX translation enabled" as the fault.
"""
import test_support._test_bootstrap as _test_bootstrap  # noqa: F401

import unittest

from yomu.ui import ui_helpers


class SfxPolicyGateTests(unittest.TestCase):
    def _reasons(self, **quality):
        return ui_helpers.classify_quality_validation(quality).get("reason_codes") or []

    def test_enabled_sfx_translation_is_not_a_violation(self):
        reasons = self._reasons(translate_sfx_disabled=False, sfx_policy_valid=True)
        self.assertNotIn("translation_policy_violation", reasons)

    def test_a_real_policy_breach_still_fails(self):
        reasons = self._reasons(translate_sfx_disabled=True, sfx_policy_valid=False)
        self.assertIn("translation_policy_violation", reasons)


if __name__ == "__main__":
    unittest.main()
