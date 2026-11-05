"""Tests for fixes identified in post-run quality audit of run d482cecc."""
from pathlib import Path
from unittest.mock import MagicMock, patch
import numpy as np
import pytest
from PIL import Image

from yomu.ocr.ocr_balloon import (
    group_has_name_only_shape,
    _render_on_clean_rescue,
    _legible_source_residual,
    PROPER_NAME_ONLY_REASON,
)
from yomu.ui.ui_bridge import UiBridge


def test_group_has_name_only_shape_follows_the_shape_contract():
    # Deliberate contract (test_proper_name_routing): the shape test alone can
    # separate a fantasy name from a common word ("WAIT!"), and does not
    # pretend to — chapter consensus and provider refusal decide those.
    for word in ("WAIT!", "ROCK?"):
        group = MagicMock()
        group.classification = "speech"
        group.text = word
        assert group_has_name_only_shape(group) is True, f"{word}: shape alone claims nothing"

    # Real character names not in English dictionary can qualify
    for name in ("Nennya", "Ihwa"):
        group = MagicMock()
        group.classification = "speech"
        group.text = name
        assert group_has_name_only_shape(group) is True, f"Expected {name} to qualify as name candidate"


def test_render_on_clean_rescue_preserves_prior_drawn_pixels():
    # Simulate page where prior group drew blue text onto before_group.
    # clean_after has white background in the overlapping pad area.
    # _render_on_clean_rescue must NOT wipe out the prior group's drawn text.
    h, w = 100, 100
    clean_before = np.full((h, w, 3), 255, dtype=np.uint8)  # blank white
    before_group = clean_before.copy()
    # Prior group drew blue text at (10..30, 10..30)
    before_group[10:30, 10:30] = [255, 0, 0]  # BGR blue

    clean_after = clean_before.copy()  # clean pass inpainted to white
    clean_mask = np.zeros((h, w), dtype=np.uint8)
    clean_mask[20:50, 20:50] = 255  # overlaps 20..30, 20..30 with prior group

    group = MagicMock()
    group.translation_candidate = "TESTE"
    group.translation = "TESTE"
    group.translation_valid = True
    group.structure_protect_mask = None
    group.draw_box = (25, 25, 20, 20)
    group.translation_box = (25, 25, 20, 20)
    group.target_box = (25, 25, 20, 20)
    group.bounding_box = (25, 25, 20, 20)
    group.text = "TEST"
    group.ocr_lang = "en"
    group.cleanup_lines = []

    with patch("yomu.ocr.ocr_balloon._draw_group_translation", side_effect=lambda canvas, g, *a, **k: canvas):
        with patch("yomu.ocr.ocr_balloon._enforce_visual_bounds", side_effect=lambda bg, ren, al, **k: (ren, {"visual_validation_passed": True})):
            with patch("yomu.ocr.ocr_balloon._legible_source_residual", return_value={"status": "not_legible"}):
                rendered, allowed = _render_on_clean_rescue(
                    before_group, clean_before, clean_after, clean_before, group, clean_mask, "font.ttf"
                )
                assert rendered is not None
                # Check that prior blue text was NOT wiped out in the overlap region
                assert np.array_equal(rendered[15, 15], [255, 0, 0])
                assert np.array_equal(rendered[25, 25], [255, 0, 0])


def test_legible_source_residual_excludes_target_tokens():
    # When target translation contains cognates/proper nouns matching source (e.g. DAEMON, LASER),
    # _legible_source_residual must exclude target tokens and not falsely claim source text is uncleaned.
    group = MagicMock()
    group.text = "DAEMON LASERBLAST"
    group.translation = "RAIO DE LASER DO DAEMON"
    group.ocr_lang = "en"

    # Simulate OCR reading the translated text from the image
    line_daemon = MagicMock(text="DAEMON", confidence=0.9, box=(10, 10, 50, 20))
    line_laser = MagicMock(text="LASER", confidence=0.9, box=(65, 10, 45, 20))
    line_raio = MagicMock(text="RAIO", confidence=0.9, box=(10, 35, 40, 20))

    with patch("yomu.ocr.ocr_balloon.config.CLEAN_RESIDUAL_OCR_CHECK", True):
        with patch("yomu.ocr.ocr_balloon._RESIDUAL_OCR_ENGINES", ["mock_engine"]):
            with patch("yomu.ocr.ocr_balloon._cleanup_lines_for_group", return_value=[MagicMock(box=(10, 10, 100, 50))]):
                with patch("yomu.ocr.ocr_balloon._reocr_crop_candidates", return_value=[("engine", "mock", 0.9, [line_daemon, line_laser, line_raio])]):
                    img = np.zeros((100, 200, 3), dtype=np.uint8)
                    res = _legible_source_residual(img, group)
                    # Since DAEMON and LASER are part of the target translation, they must not be flagged as uncleaned source residual
                    assert res.get("status") == "not_legible"
                    assert "DAEMON" not in res.get("legible_source_tokens", [])
                    assert "LASER" not in res.get("legible_source_tokens", [])


def test_open_artifact_path_uses_explorer_on_windows_dir(tmp_path):
    bridge = UiBridge()
    bridge.output_root = tmp_path
    folder = tmp_path / "test_folder"
    folder.mkdir()

    with patch("yomu.ui.ui_bridge.os.name", "nt"):
        with patch("yomu.ui.ui_bridge.subprocess.Popen") as mock_popen:
            with patch.object(bridge, "_focus_explorer_window") as mock_focus:
                bridge._open_artifact_path(str(folder))
                mock_popen.assert_called_once_with(["explorer.exe", str(folder.resolve())])
                mock_focus.assert_called_once_with(folder.name)
