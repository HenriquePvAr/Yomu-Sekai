from types import SimpleNamespace

import numpy as np

from yomu.clean.inpainting.flux_edit import manga_reconstruction_prompt


def test_reference_edit_uses_aligned_reference_without_native_mask(tmp_path, monkeypatch):
    import cv2
    from yomu.clean.inpainting import flux_edit as fe

    image = np.full((35, 67, 3), 47, np.uint8)
    metrics = {}

    def run(command, **kwargs):
        assert "--mask" not in command
        import os
        import subprocess
        assert kwargs["stdin"] == subprocess.DEVNULL
        if os.name == "nt":
            assert kwargs["creationflags"] & subprocess.CREATE_NO_WINDOW
            assert kwargs["startupinfo"].dwFlags & subprocess.STARTF_USESHOWWINDOW
        source = cv2.imread(command[command.index("-r")+1])
        assert source.shape == (64, 96, 3)
        cv2.imwrite(command[command.index("-o")+1], np.full_like(source, 99))
        return SimpleNamespace(returncode=0)

    monkeypatch.setattr(fe.subprocess, "run", run)
    result = fe._run_reference_edit(image, tmp_path, "erase text", 4, 30, metrics)
    assert result.shape == image.shape and np.all(result == 99)
    assert metrics["reason"] == "ok"


def test_reference_edit_refuses_changed_geometry(tmp_path, monkeypatch):
    import cv2
    from yomu.clean.inpainting import flux_edit as fe

    def run(command, **kwargs):
        cv2.imwrite(command[command.index("-o")+1], np.zeros((32, 32, 3), np.uint8))
        return SimpleNamespace(returncode=0)

    monkeypatch.setattr(fe.subprocess, "run", run)
    metrics = {}
    assert fe._run_reference_edit(np.zeros((35, 67, 3), np.uint8), tmp_path,
                                  "erase text", 4, 30, metrics) is None
    assert metrics["reason"] == "generative_output_geometry_mismatch"


def test_process_failure_persists_final_stderr_lines_and_telemetry_path(tmp_path, monkeypatch):
    import subprocess
    from types import SimpleNamespace
    from yomu.clean.inpainting import flux_edit as fe

    def run(_command, **kwargs):
        kwargs["stderr"].write("\n".join(f"diagnostic-{i}" for i in range(45)).encode())
        return SimpleNamespace(returncode=1)

    monkeypatch.setattr(fe.subprocess, "run", run)
    image = np.full((32, 32, 3), 20, np.uint8)
    log_path = tmp_path / "errors" / "flux_023_REGION_001.log"
    telemetry = {}
    assert fe._run_reference_edit(
        image, tmp_path, "restore", 4, 30, telemetry, diagnostic_path=log_path,
    ) is None
    lines = log_path.read_text(encoding="utf8").splitlines()
    assert lines == [f"diagnostic-{i}" for i in range(5, 45)]
    assert telemetry["reason"] == "generative_output_missing"
    assert telemetry["process_failure_category"] == "output_or_process_failure"
    assert telemetry["diagnostic_log_path"] == str(log_path)


def test_general_adapter_preserves_every_pixel_outside_mask(monkeypatch):
    from yomu.clean.inpainting import flux_edit as fe
    image = np.full((300, 300, 3), 28, np.uint8)
    mask = np.zeros((300, 300), np.uint8)
    mask[100:120, 130:155] = 255
    observed = []

    def edit(crop, **kwargs):
        observed.append(crop.shape)
        return np.full_like(crop, 123)

    monkeypatch.setattr(fe, "flux_reference_edit", edit)
    result = fe.flux_edit_inpaint(image, mask)
    assert observed == [(148, 153, 3)]
    np.testing.assert_array_equal(result[mask == 0], image[mask == 0])
    assert np.all(result[mask > 0] == 123)


def test_caption_enable_does_not_enable_general_sfx_reconstruction(tmp_path, monkeypatch):
    from yomu.clean.inpainting import flux_edit as fe
    for name in ("sd-cli.exe", "flux-2-klein-4b-Q4_0.gguf", "flux2-vae.safetensors", "qwen3-4b-q4_k_m.gguf"):
        (tmp_path/name).touch()
    monkeypatch.setattr(fe, "_model_dir", lambda: tmp_path)
    monkeypatch.setattr(fe.settings, "GENERATIVE_CAPTION_REPAIR_ENABLED", True)
    monkeypatch.setattr(fe.settings, "GENERATIVE_INPAINT_ENABLED", False)
    assert fe.available(purpose="caption_effect")
    assert not fe.available() and not fe.available(purpose="unknown")


def test_native_edit_uses_shared_ocr_lama_gpu_lock_and_returns_owned_cache(tmp_path, monkeypatch):
    from yomu.clean.inpainting import flux_edit as fe
    from yomu.core.gpu import DIRECTML_LOCK
    for name in ("sd-cli.exe", "flux-2-klein-4b-Q4_0.gguf", "flux2-vae.safetensors", "qwen3-4b-q4_k_m.gguf"):
        (tmp_path/name).touch()
    monkeypatch.setattr(fe, "_model_dir", lambda: tmp_path)
    monkeypatch.setattr(fe, "available", lambda **kwargs: True)
    fe._EDIT_CACHE.clear()
    calls = []

    def run(source, *args, **kwargs):
        assert DIRECTML_LOCK.locked()
        assert not DIRECTML_LOCK.acquire(blocking=False)
        calls.append(1)
        return source.copy()

    monkeypatch.setattr(fe, "_run_reference_edit", run)
    source = np.full((32,32,3), 70, np.uint8)
    first = fe.flux_reference_edit(source)
    first[:] = 0
    cached = fe.flux_reference_edit(source)
    assert len(calls) == 1 and np.all(cached == 70)
    source[0,0] = 80
    fe.flux_reference_edit(source)
    assert len(calls) == 2 and not DIRECTML_LOCK.locked()
    fe._EDIT_CACHE.clear()


def test_flux_prompt_uses_region_surface_and_never_source_text():
    group = SimpleNamespace(
        background_type="textured_art",
        text="CLINK — CONFIDENTIAL SOURCE TEXT",
    )

    prompt = manga_reconstruction_prompt(group)

    assert "screentone" in prompt
    assert "unmasked pixel" in prompt
    assert "Do not add lettering" in prompt
    assert group.text not in prompt


def test_flux_prompt_falls_back_to_surrounding_manga_art():
    prompt = manga_reconstruction_prompt(SimpleNamespace(background_type="unknown"))

    assert "surrounding manga artwork" in prompt
    assert "Do not add lettering" in prompt


def test_generative_second_chance_uses_protected_mask_and_context_prompt(monkeypatch):
    import yomu.ocr.ocr_balloon as ob
    from yomu.clean.inpainting import flux_edit

    image = np.zeros((12, 12, 3), dtype=np.uint8)
    cleanup = np.zeros((12, 12), dtype=np.uint8)
    cleanup[4:7, 4:7] = 255
    grown = cleanup.copy()
    grown[3:8, 3:8] = 255
    observed = {}

    class Group:
        background_type = "screentone"

    def run_flux(_image, mask, *, prompt):
        observed["mask"] = mask.copy()
        observed["prompt"] = prompt
        return image.copy()

    monkeypatch.setattr(ob, "_grown_fill_mask", lambda group, mask: grown)
    monkeypatch.setattr(ob, "_advanced_art_reconstruction_metrics", lambda *args: {})
    monkeypatch.setattr(flux_edit, "available", lambda: True)
    monkeypatch.setattr(flux_edit, "flux_edit_inpaint", run_flux)

    result = ob._generative_second_chance(image, cleanup, image, Group(), {})

    assert result is not None
    assert np.array_equal(observed["mask"], grown)
    assert "screentone" in observed["prompt"]
    assert "Do not add lettering" in observed["prompt"]
