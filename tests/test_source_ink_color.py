import test_support._test_bootstrap as _test_bootstrap  # noqa: F401
from test_support.offline_test_guard import install_offline_network_guard

install_offline_network_guard()

import unittest
from pathlib import Path
from types import SimpleNamespace

import cv2
import numpy as np
from PIL import Image, ImageDraw, ImageFont

import komyst.ocr.ocr_balloon as ob

FONT = Path(__file__).resolve().parents[1] / "assets" / "fonts" / "comicrelief-bold.ttf"


def _neon_white_on_black():
    """White lettering with a strong purple glow on a black backdrop."""
    im = Image.new("L", (620, 200), 0)
    draw = ImageDraw.Draw(im)
    font = ImageFont.truetype(str(FONT), 52)
    draw.text((20, 20), "WHAT ARE SHARDS AND", font=font, fill=255)
    draw.text((60, 100), "WHERE DID THEY COME", font=font, fill=255)
    core = np.array(im).astype(np.float32) / 255
    glow = cv2.GaussianBlur(core, (0, 0), 12)
    halo = np.clip(glow * 1.6, 0, 1)[..., None] * np.array([255, 60, 190], np.float32)
    return np.maximum(halo, core[..., None] * 255).astype(np.uint8)


class SourceInkColorTests(unittest.TestCase):
    def test_white_text_with_coloured_glow_on_black_is_white_ink(self):
        lines = [SimpleNamespace(box=(20, 25, 560, 60), text="WHAT ARE SHARDS AND", confidence=0.99),
                 SimpleNamespace(box=(60, 105, 520, 60), text="WHERE DID THEY COME", confidence=0.99)]
        box = (20, 25, 560, 140)
        group = SimpleNamespace(box=box, lines=lines, classification="narration", text="x")
        profile = ob.extract_original_lettering_profile(_neon_white_on_black(), group, box)
        self.assertEqual(profile.get("color_family"), "white")
        self.assertGreaterEqual(min(profile["dominant_bgr"]), 200)


if __name__ == "__main__":
    unittest.main()
