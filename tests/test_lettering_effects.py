"""Owned caption glows: spatial colour proof, protected art and negative fills."""
import test_support._test_bootstrap as _test_bootstrap  # noqa: F401

import hashlib
from types import SimpleNamespace

import cv2
import numpy as np

from komyst.clean.ownership import lettering_effects as le
from komyst.ocr import ocr_balloon as ob


def scene():
    h, w = 320, 640
    yy, xx = np.mgrid[:h, :w]
    background = np.stack((40+xx*.12, 6+yy*.05, 25+xx*.07), axis=2).astype(np.uint8)
    core = np.zeros((h, w), np.uint8)
    cv2.putText(core, "LASER BLAST", (60, 168), cv2.FONT_HERSHEY_SIMPLEX, 1.8, 255, 3, cv2.LINE_8)
    glow = np.clip(cv2.GaussianBlur(core.astype(np.float32), (0, 0), 8)*5/255, 0, 1)
    source = np.clip(background*(1-glow[:, :, None])+np.array([235, 55, 155])*glow[:, :, None], 0, 255).astype(np.uint8)
    source[core > 0] = 0
    cv2.line(source, (20, 35), (610, 265), (255, 255, 255), 2)
    cv2.line(background, (20, 35), (610, 265), (255, 255, 255), 2)
    core[np.all(source >= 225, axis=2)] = 0
    layers = le.build_effect_layers(source, core, [(57, 124, 390, 49)])
    return source, background, core, layers


def test_uniform_coloured_background_does_not_invent_a_glow():
    source, _, core, _ = scene()
    source[:] = (120, 25, 80)
    source[core > 0] = 0
    assert le.build_effect_layers(source, core, [(57, 124, 390, 49)]) is None


def test_compositor_never_changes_protected_or_unauthorized_pixels():
    source, background, _, layers = scene()
    assert layers is not None
    candidate = le.composite_effect(source, background, layers)
    np.testing.assert_array_equal(candidate[layers.authorized == 0], source[layers.authorized == 0])
    np.testing.assert_array_equal(candidate[layers.protected > 0], source[layers.protected > 0])
    assert np.any(candidate != source)


def test_neighboring_text_is_not_owned_by_the_effect():
    source, _, core, layers = scene()
    assert layers is not None
    assert le.build_effect_layers(source, core, [(57, 124, 390, 49)],
                                  neighbor_boxes=[(150, 130, 35, 30)]) is None


def test_spatial_boundary_rejects_flat_black_and_global_median_fill():
    source, background, _, layers = scene()
    assert layers is not None
    # Strong spatial variation matters here: a near-uniform surface can
    # legitimately be reconstructed with its median colour.
    xx = np.indices(source.shape[:2])[1]
    gradient = np.stack((xx*.23, xx*.18, xx*.20), axis=2)
    source = np.clip(source.astype(float)+gradient, 0, 255).astype(np.uint8)
    background = np.clip(background.astype(float)+gradient, 0, 255).astype(np.uint8)
    good = le.composite_effect(source, background, layers)
    result = le.paired_boundary_color(source, good, layers.authorized,
                                     protected_mask=layers.protected)
    assert result["measured"] and result["passed"], result
    for color in ((0, 0, 0), np.median(source[layers.authorized == 0], axis=0)):
        bad = source.copy()
        bad[layers.authorized > 0] = color
        result = le.paired_boundary_color(source, bad, layers.authorized,
                                         protected_mask=layers.protected)
        assert result["measured"] and not result["passed"], result


def test_sparse_boundary_fails_closed():
    image = np.zeros((20, 20, 3), np.uint8)
    mask = np.zeros((20, 20), np.uint8)
    mask[8, 8] = 255
    assert le.paired_boundary_color(image, image, mask)["passed"] is False


def test_mutating_source_or_mask_invalidates_effect_authority():
    source, _, _, layers = scene()
    assert layers is not None
    group = SimpleNamespace(_caption_effect_layers=layers,
        source_completeness={"status": "pass"},
        _caption_effect_source_hash=hashlib.sha256(source.tobytes()).hexdigest())
    assert ob._active_caption_effect_layers(source, group, layers.authorized) is layers
    changed = source.copy()
    changed[0, 0] ^= 1
    assert ob._active_caption_effect_layers(changed, group, layers.authorized) is None
    mask = layers.authorized.copy()
    mask[0, 0] ^= 255
    assert ob._active_caption_effect_layers(source, group, mask) is None


def test_changing_a_protected_art_pixel_is_rejected():
    source, background, _, layers = scene()
    assert layers is not None
    group = SimpleNamespace(_caption_effect_layers=layers,
        source_completeness={"status": "pass"},
        _caption_effect_source_hash=hashlib.sha256(source.tobytes()).hexdigest())
    candidate = le.composite_effect(source, background, layers)
    ys, xs = np.where((layers.protected > 0) & (layers.effect > 0))
    candidate[ys[0], xs[0]] = 0
    metrics = {}
    assert ob._reconstruction_gate_failure(source, candidate, group, layers.authorized,
                                          "speed_lines", "caption_effect", metrics) == "protected_effect_art_changed"


def test_sfx_never_uses_caption_glow_repair(monkeypatch):
    monkeypatch.setattr(ob.config, "GENERATIVE_CAPTION_REPAIR_ENABLED", True)
    image = np.zeros((80, 100, 3), np.uint8)
    group = ob.TextGroup("sound", classification="sfx", text="CRACKLE")
    _, mask, metrics = ob._caption_effect_cleanup(image, image, group)
    assert not mask.any() and not metrics["mask_valid"]
    assert "caption_effect" not in ob._cleanup_strategies(group)


def test_caption_flux_retries_output_failure_once_then_accepts_success(tmp_path, monkeypatch):
    from types import SimpleNamespace
    from komyst.clean.inpainting import flux_edit as fe

    for name in ("sd-cli.exe", "flux-2-klein-4b-Q4_0.gguf", "flux2-vae.safetensors", "qwen3-4b-q4_k_m.gguf"):
        (tmp_path / name).touch()
    monkeypatch.setattr(fe, "_model_dir", lambda: tmp_path)
    monkeypatch.setattr(fe.settings, "GENERATIVE_CAPTION_REPAIR_ENABLED", True)
    fe._EDIT_CACHE.clear()
    calls = []

    def run(command, **kwargs):
        calls.append(1)
        if len(calls) == 1:
            kwargs["stderr"].write(b"simulated process failure\n")
            return SimpleNamespace(returncode=1)
        import cv2
        source = cv2.imread(command[command.index("-r") + 1])
        cv2.imwrite(command[command.index("-o") + 1], np.full_like(source, 90))
        return SimpleNamespace(returncode=0)

    monkeypatch.setattr(fe.subprocess, "run", run)
    source = np.full((100, 100, 3), 20, np.uint8)
    authorized = np.zeros((100, 100), np.uint8)
    authorized[10:42, 10:42] = 255
    layers = SimpleNamespace(
        profile={"halo_hue": 145}, crop_box=(10, 10, 32, 32),
        protected=np.zeros_like(authorized), authorized=authorized,
    )
    line = SimpleNamespace(text="ABCDEFGH", box=(20, 20, 32, 49), confidence=.99,
                           metadata={"ocr_line_id": "line-1"})
    group = SimpleNamespace(
        region_id="REGION_001", group_id="BALAO_1", lines=[line], text="ABCDEFGH",
        box=(20, 20, 32, 49), classification="narration", background_metrics={},
    )
    monkeypatch.setattr(ob, "_cleanup_lines_for_group", lambda _group: [line])
    monkeypatch.setattr(ob.source_completeness, "check_live_group", lambda *a, **k: {"status": "pass"})
    monkeypatch.setattr(ob, "_classify_background_region", lambda *a: ("speed_lines", {}))
    monkeypatch.setattr(ob, "extract_glyph_style_profile", lambda *a: {"confidence": .95, "family_class": "sans"})
    def glyph_mask(_image, _box, *, padding, dark_core):
        mask = np.zeros((49 + padding * 2, 32 + padding * 2), np.uint8)
        for i in range(8):
            mask[padding:padding + 26, padding + 1 + i * 6:padding + 3 + i * 6] = 255
        return mask, {}
    monkeypatch.setattr(ob, "_glyph_ink_mask", glyph_mask)
    monkeypatch.setattr(ob, "_expanded_box", lambda _box, _shape, padding: (10, 10, 32 + 2*padding, 49 + 2*padding))
    monkeypatch.setattr(le, "build_effect_layers", lambda *a, **k: layers)
    def composite(_original, generated, _layers):
        result = source.copy()
        result[authorized > 0] = generated[10:42, 10:42][authorized[10:42, 10:42] > 0]
        return result
    monkeypatch.setattr(le, "composite_effect", composite)
    monkeypatch.setattr(ob, "_reconstruction_gate_failure", lambda *a, **k: None)
    monkeypatch.setattr(ob, "_inpaint_change_metrics", lambda *a, **k: {
        "changed_pixels_outside_mask": 0, "changed_pixels_in_mask": int(authorized.sum()),
    })
    monkeypatch.setattr(ob, "_legible_source_residual", lambda *a, **k: {"status": "not_legible"})
    with ob.flux_failure_diagnostic_context(tmp_path / "errors", 23):
        cleaned, mask, metrics = ob._caption_effect_cleanup(source.copy(), source, group)
    assert metrics["mask_valid"] and metrics["reason"] == "ok", metrics
    assert mask.any() and np.any(cleaned != source)
    assert len(calls) == 2
    assert [item.get("reason") for item in metrics["generative_telemetry"]["attempts"]] == [
        "generative_output_missing", "ok",
    ]
    assert metrics["generative_telemetry"]["attempts"][0]["diagnostic_log_path"].endswith(
        "errors\\flux_023_REGION_001.log")
    fe._EDIT_CACHE.clear()


def test_caption_flux_does_not_retry_device_memory_and_two_process_failures_are_reported(tmp_path, monkeypatch):
    from types import SimpleNamespace
    from komyst.clean.inpainting import flux_edit as fe

    for name in ("sd-cli.exe", "flux-2-klein-4b-Q4_0.gguf", "flux2-vae.safetensors", "qwen3-4b-q4_k_m.gguf"):
        (tmp_path / name).touch()
    monkeypatch.setattr(fe, "_model_dir", lambda: tmp_path)
    monkeypatch.setattr(fe.settings, "GENERATIVE_CAPTION_REPAIR_ENABLED", True)
    fe._EDIT_CACHE.clear()
    calls = []

    def run(_command, **kwargs):
        calls.append(1)
        kwargs["stderr"].write(b"out of memory\n")
        return SimpleNamespace(returncode=1)

    monkeypatch.setattr(fe.subprocess, "run", run)
    group = SimpleNamespace(region_id="REGION_002", group_id="BALAO_2")
    with ob.flux_failure_diagnostic_context(tmp_path / "errors", 23):
        result, memory_telemetry = ob._caption_effect_flux_edit(
            np.full((32, 32, 3), 20, np.uint8), prompt="restore", group=group,
        )
    assert result is None and len(calls) == 1
    assert memory_telemetry["process_failure_category"] == "device_memory"

    calls.clear()
    def process_failure(_command, **kwargs):
        calls.append(1)
        kwargs["stderr"].write(b"generic renderer failure\n")
        return SimpleNamespace(returncode=1)
    monkeypatch.setattr(fe.subprocess, "run", process_failure)
    with ob.flux_failure_diagnostic_context(tmp_path / "errors", 23):
        result, failure_telemetry = ob._caption_effect_flux_edit(
            np.full((32, 32, 3), 20, np.uint8), prompt="restore", group=group,
        )
    assert result is None and len(calls) == 2
    assert [item.get("reason") for item in failure_telemetry["attempts"]] == [
        "generative_output_missing", "generative_output_missing",
    ]
    assert failure_telemetry["reason"] == "generative_output_missing"
    fe._EDIT_CACHE.clear()


def test_caption_process_failure_keeps_existing_learned_fallback(monkeypatch):
    from types import SimpleNamespace

    source = np.full((24, 24, 3), 10, np.uint8)
    mask = np.zeros((24, 24), np.uint8)
    mask[8:16, 8:16] = 255
    group = SimpleNamespace(text="A STORY", classification="narration", background_type="speed_lines",
                            visual_attempts=[])
    learned_calls = []
    monkeypatch.setattr(ob, "_cleanup_strategies", lambda _group: ("caption_effect", "source_scoped"))
    def remove(_current, _original, _group, *, strategy):
        if strategy == "caption_effect":
            return source.copy(), None, {"mask_valid": False, "reason": "generative_output_missing"}
        return source.copy(), mask.copy(), {
            "mask_valid": False, "reason": "GLYPH_ART_BOUNDARY_UNCERTAIN",
        }
    monkeypatch.setattr(ob, "_remove_text_for_group", remove)
    monkeypatch.setattr(ob, "_uncovered_source_text_evidence", lambda *a: {"status": "verified"})
    monkeypatch.setattr(ob, "_source_removal_incomplete", lambda *a: False)
    monkeypatch.setattr(ob, "_legible_source_residual", lambda *a: {"status": "not_legible"})
    monkeypatch.setattr(ob, "_last_resort_allowed", lambda _group: True)
    def learned(_current, _original, _group, _mask):
        learned_calls.append(1)
        return {"cleaned": np.full_like(source, 30), "attempt": {"art_fidelity_uncertain": True}}
    monkeypatch.setattr(ob, "_learned_last_resort_clean", learned)

    cleaned, used_mask, strategy, accepted = ob._clean_source_for_clean_artifact(
        source.copy(), source, group,
    )
    assert accepted and strategy == "learned_last_resort"
    assert len(learned_calls) == 1 and np.all(cleaned == 30) and used_mask.any()


def test_cached_pixels_cannot_bypass_current_source_completeness(monkeypatch):
    from komyst.clean.inpainting import flux_edit
    from komyst.ocr.ocr_engine import OCRLine
    source = np.zeros((120, 180, 3), np.uint8)
    member = OCRLine(text="SOURCE", raw_text="SOURCE", confidence=.99,
        box=(20, 30, 130, 48), polygon=np.array([[20,30],[150,30],[150,78],[20,78]]),
        engine="synthetic", metadata={"ocr_line_id": "changed-source-id"})
    group = ob.TextGroup("caption", lines=[member], text="SOURCE", classification="narration")
    key = hashlib.sha256(source.tobytes()+repr([
        (member.text, tuple(member.box), member.confidence, member.metadata["ocr_line_id"])
    ]).encode()).hexdigest()
    group._caption_effect_result = {"source_key": key, "accepted": True}
    monkeypatch.setattr(flux_edit, "available", lambda **kwargs: True)
    monkeypatch.setattr(ob.source_completeness, "check_live_group",
                        lambda *args, **kwargs: {"status": "unavailable"})
    _, mask, metrics = ob._caption_effect_cleanup(source, source, group)
    assert not mask.any() and not metrics["mask_valid"]
    assert metrics["reason"] == "caption_effect_source_not_complete"
