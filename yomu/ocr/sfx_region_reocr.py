"""Last-chance SFX region re-OCR.

Page-level OCR garbles stylised sound lettering ("PElW" for "PEW", "ULANE" for
"CLANK") and the exact/fuzzy glossary lookup then has nothing to work with, so
the region ships in English or lands in review. A tight crop of the region
re-read natively often recovers what the page-level pass destroyed (measured on
the ep. 285 runs: 2 of 6 hopeless cases fixed by the RapidOCR crop alone, and
PaddleOCR recovered "CLANK" from "ULANE" where every RapidOCR scale failed).

Cost model (measured, RX 6600 class machine): RapidOCR crop read ~0.3-0.5 s;
PaddleOCR ~1.1-2.1 s per crop plus a one-time ~12 s model load (~0.7 GB RAM,
CPU-only -> zero VRAM) that ``prewarm_sfx_paddle`` hides in the download stage.
Full-page Paddle is NOT viable (3.3-4.6 s/page); this module is selective-only.
"""
from __future__ import annotations

import threading

import numpy as np

from yomu.config import settings as config

_SFX_REOCR_MIN_LETTERS = 3
_SFX_REOCR_MAX_LETTERS = 10
_SFX_REOCR_MAX_WORDS = 2
_SFX_REOCR_MAX_GROUPS_PER_PAGE = 8
_SFX_REOCR_SUSPECT_BACKGROUNDS = {"textured_art", "speed_lines", "sfx_area"}
# Tight on purpose: the lettering bbox is the signal. The generic fallback crop
# pads a lot (34+ px, up to 130 for quality reasons) and the surrounding art /
# speed lines measurably corrupt the re-read — on ep. 285 p15 Paddle read the
# exact "CLANK" from a tight crop but repeated the garbled "ULANE" from the
# padded one.
_SFX_REOCR_PAD = 12

_engine_lock = threading.Lock()
_rapid_engine = None
_paddle_engine = None
_paddle_unavailable = False


def _rapid_crop_reads(crop_bgr: np.ndarray) -> list[str]:
    global _rapid_engine
    with _engine_lock:
        if _rapid_engine is None:
            from rapidocr_onnxruntime import RapidOCR

            _rapid_engine = RapidOCR()
    try:
        result, _ = _rapid_engine(crop_bgr)
    except Exception:  # noqa: BLE001 - a failed read is just no evidence
        return []
    return [str(item[1]) for item in (result or [])]


def _paddle_crop_reads(crop_bgr: np.ndarray) -> list[str]:
    global _paddle_engine, _paddle_unavailable
    if _paddle_unavailable:
        return []
    with _engine_lock:
        if _paddle_engine is None:
            try:
                from paddleocr import PaddleOCR

                _paddle_engine = PaddleOCR(
                    use_doc_orientation_classify=False,
                    use_doc_unwarping=False,
                    use_textline_orientation=False,
                    lang="en",
                )
            except Exception:  # noqa: BLE001 - optional engine, fail-closed
                _paddle_unavailable = True
                return []
    try:
        results = _paddle_engine.predict(crop_bgr)
    except Exception:  # noqa: BLE001
        return []
    reads: list[str] = []
    for result in results:
        data = result if isinstance(result, dict) else getattr(result, "json", {})
        if isinstance(data, dict):
            reads.extend(str(text) for text in (data.get("rec_texts") or []))
    return reads


def prewarm_sfx_paddle() -> None:
    """Load Paddle models in the background so the first escalation has no latency."""
    if not getattr(config, "OCR_SFX_PADDLE_ESCALATION", False):
        return
    _paddle_crop_reads(np.zeros((32, 64, 3), dtype=np.uint8))


def _is_candidate(group) -> bool:
    if getattr(group, "ignored", False) or getattr(group, "fallback_used", False):
        return False
    text = str(getattr(group, "text", "") or "").strip()
    letters = "".join(char for char in text if char.isalpha())
    if not (_SFX_REOCR_MIN_LETTERS <= len(letters) <= _SFX_REOCR_MAX_LETTERS):
        return False
    if len([word for word in text.split() if any(char.isalpha() for char in word)]) > _SFX_REOCR_MAX_WORDS:
        return False
    from yomu.translation.sfx_glossary import translate_sfx_fuzzy

    if translate_sfx_fuzzy(text) is not None:
        return False  # the current read already yields a sound
    background = str(getattr(group, "background_type", "") or "")
    if background in _SFX_REOCR_SUSPECT_BACKGROUNDS:
        return True
    # Off the typical SFX backdrops, only spend reads on reads we already distrust.
    if str(getattr(group, "classification", "") or "") == "sfx":
        return True
    return float(getattr(group, "confidence", 1.0) or 1.0) < 0.85


def repair_sfx_region_reads(groups, original_bgr, page_index=None) -> list[dict]:
    """Re-read garbled short sound regions from a tight crop and adopt glossary hits.

    Runs after classification/metadata and before any translation decision, so a
    repaired ``group.text`` flows through the normal glossary/SFX paths. Only
    reads that the fuzzy glossary accepts (and that render into something other
    than the source echo) are adopted; everything else stays fail-closed.
    """
    if not (getattr(config, "OCR_SFX_REGION_REOCR", True) and config.TRANSLATE_SFX):
        return []
    from yomu.translation.sfx_glossary import translate_sfx_fuzzy

    repairs: list[dict] = []
    candidates = [group for group in groups if _is_candidate(group)][
        : _SFX_REOCR_MAX_GROUPS_PER_PAGE
    ]
    image_height, image_width = original_bgr.shape[:2]
    for group in candidates:
        box = getattr(group, "box", None)
        if not box:
            continue
        x, y, w, h = (int(value) for value in box[:4])
        x1 = max(0, x - _SFX_REOCR_PAD)
        y1 = max(0, y - _SFX_REOCR_PAD)
        x2 = min(image_width, x + w + _SFX_REOCR_PAD)
        y2 = min(image_height, y + h + _SFX_REOCR_PAD)
        crop = original_bgr[y1:y2, x1:x2]
        if crop.size == 0:
            continue
        engines = [("rapidocr", _rapid_crop_reads)]
        if getattr(config, "OCR_SFX_PADDLE_ESCALATION", False):
            engines.append(("paddle", _paddle_crop_reads))
        adopted = ""
        adopted_engine = ""
        for engine_name, reader in engines:
            for read in reader(crop):
                read = str(read or "").strip()
                rendered = translate_sfx_fuzzy(read)
                # The repair is real when the new READ differs from the garbled
                # original — even if the glossary renders it unchanged ("CLANG"
                # reads as "CLANG": Paddle reads the stylised lettering as the
                # pt-BR onomatopoeia itself, which is still a fix for "ULANE").
                if rendered and read.strip().casefold() != str(group.text or "").strip().casefold():
                    adopted, adopted_engine = read, engine_name
                    break
            if adopted:
                break
        if not adopted:
            continue
        old_text = str(getattr(group, "text", "") or "")
        group.text = adopted
        group.canonical_source_text = adopted
        group.sfx_reocr_repair = {
            "page": page_index,
            "from": old_text,
            "to": adopted,
            "engine": adopted_engine,
        }
        repairs.append(dict(group.sfx_reocr_repair))
    return repairs
