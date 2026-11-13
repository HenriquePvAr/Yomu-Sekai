"""F1.5: LaMa and FLUX report 'unavailable' on low RAM; the denial is counted."""
import numpy as np
import pytest

from komyst.clean.inpainting import advanced_art_inpainting as lama
from komyst.clean.inpainting import flux_edit
from komyst.config import settings
from komyst.runtime import memory_guard


@pytest.fixture(autouse=True)
def _fresh_counters():
    memory_guard.reset_counters()
    yield
    memory_guard.reset_counters()


def _ram(monkeypatch, mb):
    monkeypatch.setattr(memory_guard, "available_ram_mb", lambda: mb)


def test_allow_depends_on_free_ram_and_unknown_allows(monkeypatch):
    _ram(monkeypatch, 100)
    assert memory_guard.allow("lama", 1500) is False
    _ram(monkeypatch, 9000)
    assert memory_guard.allow("lama", 1500) is True
    _ram(monkeypatch, None)  # cannot measure: never block
    assert memory_guard.allow("flux", 6000) is True
    assert memory_guard.skipped_counters() == {"lama_skipped_low_memory": 1, "flux_skipped_low_memory": 0}


def _inpainter(tmp_path):
    model = tmp_path / "m.pt"
    model.write_bytes(b"x")
    return lama.AdvancedArtInpainter(model_path=model)


def _page():
    image = np.zeros((64, 64, 3), np.uint8)
    mask = np.zeros((64, 64), np.uint8)
    mask[10:20, 10:20] = 255
    return image, mask


def test_lama_low_memory_is_unavailable_and_counted(monkeypatch, tmp_path):
    _ram(monkeypatch, 10)
    with pytest.raises(lama.AdvancedInpaintUnavailable):
        _inpainter(tmp_path).reconstruct(*_page())
    assert memory_guard.skipped_counters()["lama_skipped_low_memory"] == 1


def test_lama_oversized_crop_is_unavailable(monkeypatch, tmp_path):
    _ram(monkeypatch, 99999)
    monkeypatch.setattr(settings, "LAMA_MAX_CROP_PIXELS", 100)
    inpainter = _inpainter(tmp_path)
    monkeypatch.setattr(inpainter, "load", lambda: object())
    with pytest.raises(lama.AdvancedInpaintUnavailable):
        inpainter.reconstruct(*_page())


def test_flux_available_follows_the_guard(monkeypatch, tmp_path):
    for name in ("sd-cli.exe", "flux-2-klein-4b-Q4_0.gguf", "flux2-vae.safetensors", "qwen3-4b-q4_k_m.gguf"):
        (tmp_path / name).write_bytes(b"x")
    monkeypatch.setattr(flux_edit, "_model_dir", lambda: tmp_path)
    monkeypatch.setattr(settings, "GENERATIVE_INPAINT_ENABLED", True, raising=False)
    _ram(monkeypatch, 100)
    assert flux_edit.available() is False
    assert memory_guard.skipped_counters()["flux_skipped_low_memory"] == 1
    _ram(monkeypatch, 99999)
    assert flux_edit.available() is True
