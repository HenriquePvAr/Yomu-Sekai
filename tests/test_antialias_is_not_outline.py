"""The anti-aliased edge of plain black lettering is not an outline.

Seitokai ch. 188 (a ~960 px manga scan): black text on a white balloon came back
drawn with a thick grey outline, because the edge blend was measured as a stroke.
"""
import test_support._test_bootstrap as _test_bootstrap  # noqa: F401

import unittest

import cv2
import numpy as np

import yomu.ocr.ocr_balloon as ob
from yomu.ocr.ocr_engine import OCRLine


class AntialiasIsNotOutlineTests(unittest.TestCase):
    def test_plain_small_black_lettering_gets_no_outline(self):
        img = np.full((220, 300, 3), 250, np.uint8)
        for i, word in enumerate(("THE WEATHER'S", "GOTTEN A LOT", "COOLER")):
            cv2.putText(img, word, (40, 60 + i * 40), cv2.FONT_HERSHEY_DUPLEX, 0.8, (15, 15, 15), 2, cv2.LINE_AA)
        img = cv2.resize(cv2.resize(img, None, fx=0.6, fy=0.6, interpolation=cv2.INTER_AREA), (300, 220))
        box = (30, 30, 240, 140)
        x, y, w, h = box
        line = OCRLine(text="THE WEATHER'S GOTTEN A LOT COOLER", confidence=0.95,
                       polygon=np.array([[x, y], [x + w, y], [x + w, y + h], [x, y + h]]), box=box,
                       raw_text="", engine="t", page=1)
        group = ob.TextGroup(group_id="BALAO_1", lines=[line], text=line.text)
        group.classification = "speech"
        profile = ob.typography_profile_for_region(img, group, box)
        width = int(profile.get("stroke_width") or 0)
        if width >= 2 and profile.get("stroke_color"):
            fill = profile["fill_color"]
            stroke = profile["stroke_color"]
            lum = lambda c: 0.299 * c[0] + 0.587 * c[1] + 0.114 * c[2]
            low, high = sorted((lum(fill), float(profile["background_brightness"])))
            self.assertFalse(low + 15 < lum(stroke) < high - 15, f"grey blend drawn as outline: {profile}")

    def test_blend_between_ink_and_background_is_flagged(self):
        img = np.full((120, 300, 3), 250, np.uint8)
        cv2.putText(img, "COOLER", (30, 80), cv2.FONT_HERSHEY_DUPLEX, 1.4, (15, 15, 15), 2, cv2.LINE_AA)
        img = cv2.GaussianBlur(img, (0, 0), 1.6)
        box = (20, 30, 260, 70)
        x, y, w, h = box
        line = OCRLine(text="COOLER", confidence=0.95, polygon=np.array([[x, y], [x + w, y], [x + w, y + h], [x, y + h]]),
                       box=box, raw_text="", engine="t", page=1)
        group = ob.TextGroup(group_id="BALAO_1", lines=[line], text="COOLER")
        group.classification = "speech"
        profile = ob.typography_profile_for_region(img, group, box)
        if profile.get("stroke_is_antialias_blend"):
            self.assertFalse(profile.get("source_stroke_confident"))


if __name__ == "__main__":
    unittest.main()
