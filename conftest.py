"""Pytest collection is offline and runtime-isolated before test modules are imported."""

import os

import pytest

from test_support.hermetic_runtime import install_runtime_isolation_guard
from test_support.offline_test_guard import install_offline_network_guard


os.environ.setdefault("TRADUTOR_IA_HERMETIC_TEST_ENV", "1")
# The learned texture fill would load the developer's local 200 MB model and make
# results depend on the machine; tests that need it inject a fake inpainter.
os.environ.setdefault("CLEAN_LEARNED_TEXTURE_FILL", "0")
# Same for the residual re-read: it would run the real OCR models inside unit tests.
os.environ.setdefault("CLEAN_RESIDUAL_OCR_CHECK", "0")
# The masked-page rediscovery runs a second full-page OCR; unit tests stay offline/fast.
os.environ.setdefault("OCR_MASKED_REDISCOVERY", "0")
# The learned last resort would load the local model too.
os.environ.setdefault("CLEAN_LEARNED_LAST_RESORT", "0")
# The suite was written against the former default (sound effects preserved);
# the translated-SFX path has its own tests.
os.environ.setdefault("TRANSLATE_SFX", "0")
# Results must not depend on the machine's GPU; DirectML has its own tests.
os.environ.setdefault("GPU_INFERENCE", "off")
install_offline_network_guard()
install_runtime_isolation_guard()


@pytest.fixture(autouse=True)
def _restore_process_environment():
    """Fail closed against cross-test os.environ contamination.

    A test that mutates os.environ and skips its own restore (e.g. a fragile
    setUp/tearDown, or a CLI path that loads the real .env.local and leaks
    BETA_LICENSE_PROVIDER) used to poison every later test, making the whole
    suite order-dependent.  Snapshot the process environment around each test and
    restore it exactly, so leaks stay local to the test that caused them.  Only
    env vars are touched — never test data or setUpClass-seeded state.
    """
    snapshot = dict(os.environ)
    try:
        yield
    finally:
        if os.environ != snapshot:
            os.environ.clear()
            os.environ.update(snapshot)
