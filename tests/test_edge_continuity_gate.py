"""Edge-continuity fidelity gate: large SFX over complex art routes to LaMA."""
from types import SimpleNamespace

import cv2
import numpy as np
from unittest import mock

from yomu.config import settings as config
from yomu.ocr.ocr_balloon import (
    _edge_continuity_fidelity_findings,
    _advanced_art_fallback_eligible,
)


def _page_with_texture(texture: str, size=(600, 600)) -> np.ndarray:
    page = np.full((*size, 3), 235, np.uint8)
    if texture == "grid":
        page[::8, :, :] = 60
        page[:, ::8, :] = 60
    elif texture == "screentone":
        cv2.circle(page, (300, 300), 260, 160, -1)
        for y in range(40, 560, 6):
            page[y : y + 1, 40:560] = 90
    return page


def _group(background_type="sfx_area", classification="sfx", **extra):
    attrs = {
        "background_type": background_type,
        "classification": classification,
        "source_completeness": {"status": "pass"},
    }
    attrs.update(extra)
    return SimpleNamespace(**attrs)


def test_dense_ring_over_large_mask_fires():
    page = _page_with_texture("grid")
    mask = np.zeros(page.shape[:2], np.uint8)
    mask[150:450, 150:450] = 255  # filled interior (flat -> smear)
    finding = _edge_continuity_fidelity_findings(page, page, mask, _group())
    assert finding["art_fidelity_uncertain"] is True
    assert finding["edge_continuity"]["ring_edge_density"] > 0.02


def test_flat_background_stays_quiet():
    page = _page_with_texture("flat")
    mask = np.zeros(page.shape[:2], np.uint8)
    mask[150:450, 150:450] = 255
    finding = _edge_continuity_fidelity_findings(page, page, mask, _group())
    assert finding["art_fidelity_uncertain"] is False


def test_balloon_background_never_considered():
    page = _page_with_texture("grid")
    mask = np.zeros(page.shape[:2], np.uint8)
    mask[150:450, 150:450] = 255
    finding = _edge_continuity_fidelity_findings(page, page, mask, _group(background_type="white_balloon"))
    assert finding["art_fidelity_uncertain"] is False


def test_small_mask_never_fires():
    page = _page_with_texture("grid")
    mask = np.zeros(page.shape[:2], np.uint8)
    mask[250:270, 250:270] = 255  # 400 px, below the mask floor
    finding = _edge_continuity_fidelity_findings(page, page, mask, _group())
    assert finding["art_fidelity_uncertain"] is False


def test_sfx_eligibility_requires_fidelity_evidence():
    group = _group()
    with mock.patch.object(config, "ADVANCED_ART_INPAINTING", True), \
            mock.patch.object(config, "ADVANCED_ART_INPAINT_MAX_ATTEMPTS_PER_REGION", 1):
        # Blanket exclusion stands without the measured flag.
        assert _advanced_art_fallback_eligible(group, {}) is False
        # With the edge-continuity evidence the region may reach LaMA.
        assert _advanced_art_fallback_eligible(
            group, {"art_fidelity_uncertain": True, "background_type": "sfx_area"}
        ) is True
        # Logo keeps the hard exclusion.
        logo = _group(classification="logo")
        assert _advanced_art_fallback_eligible(
            logo, {"art_fidelity_uncertain": True, "background_type": "sfx_area"}
        ) is False


def test_fidelity_evidence_relaxes_review_gates_but_not_reject():
    metrics = {"art_fidelity_uncertain": True, "background_type": "sfx_area"}
    with mock.patch.object(config, "ADVANCED_ART_INPAINTING", True), \
            mock.patch.object(config, "ADVANCED_ART_INPAINT_MAX_ATTEMPTS_PER_REGION", 1):
        # Review translation state / review completeness: the measured art
        # destruction justifies the attempt; the LaMA output still faces every
        # downstream validator, and failure lands in review (fail-closed).
        review_state = _group(translation_final_state="manual_review")
        assert _advanced_art_fallback_eligible(review_state, metrics) is True
        review_completeness = _group(source_completeness={"status": "review"})
        assert _advanced_art_fallback_eligible(review_completeness, metrics) is True
        # A hard reject or failed completeness stays out either way.
        rejected = _group(translation_final_state="rejected")
        assert _advanced_art_fallback_eligible(rejected, metrics) is False
        failed = _group(source_completeness={"status": "fail"})
        assert _advanced_art_fallback_eligible(failed, metrics) is False
        # Without the evidence the old strict gates still apply.
        plain = _group(translation_final_state="manual_review")
        assert _advanced_art_fallback_eligible(plain, {}) is False
