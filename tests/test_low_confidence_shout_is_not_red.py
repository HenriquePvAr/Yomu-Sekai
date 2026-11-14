"""Without a confident read of the source pixels, a shout is not given an invented colour.

A black "!!" shout in a white balloon re-rendered red with a glow whenever the lettering read was weak
(for example on the page-revision path, whose box is the whole balloon). Synthetic pixels only.
"""
import numpy as np

from komyst.ocr import ocr_balloon as ob
from komyst.ocr.ocr_balloon import OCRLine, TextGroup


def _group(box, text="YOU THERE!!"):
    x, y, w, h = box
    polygon = np.array([[x, y], [x + w, y], [x + w, y + h], [x, y + h]], dtype=np.int32)
    line = OCRLine(text=text, confidence=0.95, polygon=polygon, box=box, raw_text=text,
                   engine="rapidocr", page=1)
    return TextGroup(group_id="T001", lines=[line], text=text, classification="narration",
                     inside_balloon_like_region=True, source_engine="rapidocr")


def test_low_confidence_emphatic_caption_on_white_is_dark_ink_without_glow():
    image = np.full((300, 900, 3), 255, np.uint8)  # no lettering pixels at all: a zero-confidence read
    box = (20, 100, 860, 80)
    profile = ob.typography_profile_for_region(image, _group(box), box)
    assert profile["visual_class"] != "dramatic_red_display"
    assert max(profile["fill_color"]) <= 60
    assert not profile.get("glow_color") and not profile.get("glow_strength")
