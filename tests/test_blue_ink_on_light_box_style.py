"""Dark blue ink in a light narration box is plain lettering, not a glowing 'system' caption.

Real output showed a navy, regular-weight comic font rendered as heavy blue condensed type with a thick
outline and a halo, because every blue-ink caption was mapped to the luminous 'mystic blue' preset.
Synthetic pixels only.
"""
import numpy as np
import cv2
from PIL import Image, ImageDraw, ImageFont

from komyst.ocr import ocr_balloon as ob
from komyst.ocr.ocr_balloon import TextGroup, OCRLine


def _font(size):
    for name in ("arialbd.ttf", "arial.ttf", "DejaVuSans-Bold.ttf", "DejaVuSans.ttf"):
        try:
            return ImageFont.truetype(name, size)
        except OSError:
            continue
    return ImageFont.load_default()


def _page(background, ink, text="WHILE ABCDEFG HIJKLM", size=34):
    image = Image.new("RGB", (420, 260), background)
    draw = ImageDraw.Draw(image)
    font = _font(size)
    for index, line in enumerate(text.split(" ", 1)):
        draw.text((40, 60 + index * 60), line, font=font, fill=ink)
    return cv2.cvtColor(np.array(image), cv2.COLOR_RGB2BGR)


def _group(text="WHILE ABCDEFG HIJKLM"):
    polygon = np.array([[40, 60], [380, 60], [380, 170], [40, 170]], dtype=np.int32)
    line = OCRLine(text=text, confidence=0.95, polygon=polygon, box=(40, 60, 340, 110),
                   raw_text=text, engine="rapidocr", page=1)
    group = TextGroup(group_id="T001", lines=[line], text=text, classification="narration",
                      inside_balloon_like_region=True, source_engine="rapidocr")
    group.detected_proper_names = []
    return group


BOX = (30, 50, 360, 130)


def test_navy_ink_on_a_light_blue_box_is_not_the_luminous_preset():
    image = _page(background=(218, 242, 246), ink=(48, 63, 93))  # light blue box, navy ink
    profile = ob.typography_profile_for_region(image, _group(), BOX)
    assert profile["visual_class"] != "mystic_blue_system"
    assert not profile.get("glow_color") and not profile.get("glow_strength")
    assert int(profile["stroke_width"]) <= 1
    assert profile["font_class"] != "condensed_display"


def test_luminous_blue_lettering_on_a_dark_background_keeps_the_preset():
    image = _page(background=(8, 14, 30), ink=(120, 190, 255))
    profile = ob.typography_profile_for_region(image, _group(), BOX)
    assert profile["visual_class"] == "mystic_blue_system"
