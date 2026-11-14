"""Dark lettering with a thick white outline must not be read as white ink.

On a light page the outline can outnumber the ink pixels; taking the majority colour as the ink inverted
the lettering and rendered it white on white (invisible). Synthetic pixels only.
"""
import cv2
import numpy as np
from PIL import Image, ImageDraw, ImageFont

from komyst.ocr import ocr_balloon as ob
from komyst.ocr.ocr_balloon import OCRLine, TextGroup


def _font(size):
    for name in ("arialbd.ttf", "DejaVuSans-Bold.ttf", "arial.ttf"):
        try:
            return ImageFont.truetype(name, size)
        except OSError:
            continue
    return ImageFont.load_default()


def _page(background, ink, outline, stroke=6):
    image = Image.new("RGB", (460, 200), background)
    draw = ImageDraw.Draw(image)
    draw.text((30, 40), "ABCDEFGH", font=_font(64), fill=ink, stroke_width=stroke, stroke_fill=outline)
    return cv2.cvtColor(np.array(image), cv2.COLOR_RGB2BGR)


def _group():
    polygon = np.array([[24, 34], [440, 34], [440, 130], [24, 130]], dtype=np.int32)
    line = OCRLine(text="ABCDEFGH", confidence=0.95, polygon=polygon, box=(24, 34, 416, 96),
                   raw_text="ABCDEFGH", engine="rapidocr", page=1)
    return TextGroup(group_id="T001", lines=[line], text="ABCDEFGH", classification="narration",
                     inside_balloon_like_region=False, source_engine="rapidocr")


BOX = (24, 34, 416, 96)


def test_dark_ink_with_a_thick_white_outline_on_a_light_page_stays_dark():
    image = _page(background=(226, 222, 218), ink=(18, 18, 18), outline=(255, 255, 255))
    profile = ob.extract_original_lettering_profile(image, _group(), BOX)
    assert profile["color_family"] == "black"
    assert max(profile["dominant_bgr"]) <= 80
    assert profile["stroke_present"] and min(profile["stroke_color"]) >= 185


def test_white_ink_with_a_dark_outline_stays_white():
    image = _page(background=(226, 222, 218), ink=(255, 255, 255), outline=(18, 18, 18))
    profile = ob.extract_original_lettering_profile(image, _group(), BOX)
    assert profile["color_family"] == "white"
    assert min(profile["dominant_bgr"]) >= 185
