"""Font choice by raster: the face that redraws the source's own words most like the source wins."""
from pathlib import Path

import numpy as np
import pytest
from PIL import Image, ImageDraw, ImageFont

from komyst.clean.ownership import font_fidelity as ff
from komyst.ocr.ocr_balloon import OCRLine

BUNDLED = Path(ff.BUNDLED_FONTS_DIR)


def _system(name):
    for root in (Path("C:/Windows/Fonts"),):
        if (root / name).is_file():
            return str(root / name)
    return None


def _page(font_path, lines, size=46):
    font = ImageFont.truetype(font_path, size)
    image = Image.new("RGB", (900, 70 * len(lines) + 40), "white")
    draw = ImageDraw.Draw(image)
    ocr_lines = []
    for index, text in enumerate(lines):
        origin = (30, 20 + index * 70)
        left, top, right, bottom = draw.textbbox(origin, text, font=font)
        draw.text(origin, text, font=font, fill=(0, 0, 0))
        box = (left - 4, top - 4, right - left + 8, bottom - top + 8)
        x, y, w, h = box
        polygon = np.array([[x, y], [x + w, y], [x + w, y + h], [x, y + h]], dtype=np.int32)
        ocr_lines.append(OCRLine(text=text, confidence=0.95, polygon=polygon, box=box, raw_text=text,
                                 engine="rapidocr", page=1))
    return np.array(image)[:, :, ::-1].copy(), ocr_lines


LINES = ["LET'S SEE IF MY", "HEART STOPS BEATING"]


@pytest.mark.parametrize("source_font", ["comicrelief-regular.ttf", "georgia.ttf", "impact.ttf"])
def test_the_face_that_drew_the_source_is_recognised(source_font):
    paths = {"comicrelief-regular.ttf": str(BUNDLED / "comicrelief-regular.ttf"),
             "georgia.ttf": _system("georgia.ttf"), "impact.ttf": _system("impact.ttf"),
             "arialbd.ttf": _system("arialbd.ttf")}
    if not all(paths.values()):
        pytest.skip("reference system fonts not installed")
    image, lines = _page(paths[source_font], LINES)
    masks = ff.source_line_masks(image, lines, ink_bgr=(0, 0, 0))
    result = ff.match_font_by_raster(masks, list(paths.values()), draw_text="VAMOS VER SE MEU CORAÇÃO")
    assert Path(result["path"]).name == source_font
    assert result["score"] > result["runner_up_score"]


def test_a_face_that_cannot_draw_the_translation_is_excluded(tmp_path):
    image, lines = _page(str(BUNDLED / "comicrelief-regular.ttf"), LINES)
    masks = ff.source_line_masks(image, lines, ink_bgr=(0, 0, 0))
    result = ff.match_font_by_raster(masks, [str(BUNDLED / "comicrelief-regular.ttf")], draw_text="\u7c73")
    assert result is None


def test_renderer_choice_replaces_the_role_face_only_when_the_match_clearly_wins():
    from komyst.ocr import ocr_balloon as ob
    from komyst.ocr.ocr_balloon import TextGroup

    georgia = _system("georgia.ttf")
    if not georgia or not _system("bahnschrift.ttf"):
        pytest.skip("reference system fonts not installed")
    image, lines = _page(georgia, LINES)
    group = TextGroup(group_id="T", lines=lines, text=" ".join(LINES), classification="narration",
                      inside_balloon_like_region=True, source_engine="rapidocr")
    profile = {"original_lettering": {"dominant_bgr": (0, 0, 0)}}
    choice = ob._raster_font_choice(image, group, profile, "VAMOS VER SE MEU CORAÇÃO", None, "display")
    assert choice and Path(choice["path"]).name == "georgia.ttf"
    assert choice["score"] - choice["role_score"] >= ob._RASTER_MATCH_MIN_GAIN

    image, lines = _page(_system("bahnschrift.ttf"), LINES)
    group.lines = lines
    assert ob._raster_font_choice(image, group, profile, "VAMOS VER SE", None, "display") is None


def test_a_stacked_block_given_as_one_line_takes_no_part():
    image, lines = _page(str(BUNDLED / "comicrelief-regular.ttf"), LINES)
    x0 = min(l.box[0] for l in lines); y0 = min(l.box[1] for l in lines)
    x1 = max(l.box[0] + l.box[2] for l in lines); y1 = max(l.box[1] + l.box[3] for l in lines)
    block = OCRLine(text=" ".join(LINES), confidence=0.9,
                    polygon=np.array([[x0, y0], [x1, y0], [x1, y1], [x0, y1]], dtype=np.int32),
                    box=(x0, y0, x1 - x0, y1 - y0), raw_text="x", engine="rapidocr", page=1)
    assert ff.source_line_masks(image, [block], ink_bgr=(0, 0, 0)) == []
