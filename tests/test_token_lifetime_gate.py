"""A token too close to expiry is refused before a job exists.

It used to be refused only when sealing, after the job was already queued; the
worker then ran the chapter without a credential and failed at translation.
"""
import test_support._test_bootstrap as _test_bootstrap  # noqa: F401

import base64
import json
import time
import unittest

from yomu.auth.secure_auth_context import AuthContextError, require_token_lifetime
from yomu.ui.ui_bridge import UiBridge


def _jwt(exp):
    part = lambda obj: base64.urlsafe_b64encode(json.dumps(obj).encode()).rstrip(b"=").decode()
    return f"{part({'alg': 'HS256'})}.{part({'exp': exp, 'sub': 'u'})}.c2ln"


class TokenLifetimeGateTests(unittest.TestCase):
    def test_token_near_expiry_needs_refresh(self):
        with self.assertRaises(AuthContextError) as raised:
            require_token_lifetime(_jwt(time.time() + 300))
        self.assertEqual(raised.exception.args[0], "auth_refresh_required")

    def test_fresh_token_passes(self):
        self.assertGreater(require_token_lifetime(_jwt(time.time() + 3600)), time.time())

    def test_start_gate_refuses_before_any_job(self):
        bridge = UiBridge.__new__(UiBridge)
        with self.assertRaisesRegex(ValueError, "auth_refresh_required"):
            bridge._authorize_translation_start(principal=None, license_access_token=_jwt(time.time() + 120))


if __name__ == "__main__":
    unittest.main()
