import test_support._test_bootstrap as _test_bootstrap  # noqa: F401
from test_support.offline_test_guard import install_offline_network_guard

install_offline_network_guard()

import unittest
from types import SimpleNamespace

import cv2
import numpy as np

import yomu.ocr.ocr_balloon as ob


def _glowing_text_on_black():
    core = np.zeros((120, 200, 3), np.uint8)
    cv2.rectangle(core, (60, 50), (140, 70), (255, 255, 255), -1)
    image = cv2.GaussianBlur(core, (0, 0), 3)  # soft halo around the lettering
    mask = np.zeros((120, 200), np.uint8)
    mask[50:71, 60:141] = 1  # the mask only hugs the bright core
    return image, mask


class LetteringResidueMaskTests(unittest.TestCase):
    def test_soft_halo_just_outside_the_mask_joins_the_fill(self):
        image, mask = _glowing_text_on_black()
        group = SimpleNamespace(box=(60, 50, 81, 21))
        grown = ob._mask_with_lettering_residue(group, image, mask)
        self.assertTrue(np.all(grown[mask > 0] == 1))
        self.assertGreater(int(grown.sum()), int(mask.sum()))

    def test_protected_structure_is_never_grown_into(self):
        image, mask = _glowing_text_on_black()
        protect = np.zeros_like(mask)
        protect[40:50, :] = 1
        group = SimpleNamespace(box=(60, 50, 81, 21), structure_protect_mask=protect)
        grown = ob._mask_with_lettering_residue(group, image, mask)
        self.assertEqual(int(grown[40:50, :].sum()), 0)

    def test_without_a_halo_the_mask_is_unchanged(self):
        image = np.zeros((120, 200, 3), np.uint8)
        cv2.rectangle(image, (60, 50), (140, 70), (255, 255, 255), -1)  # hard edge, no glow
        mask = np.zeros((120, 200), np.uint8)
        mask[50:71, 60:141] = 1
        grown = ob._mask_with_lettering_residue(SimpleNamespace(box=(60, 50, 81, 21)), image, mask)
        self.assertEqual(int(grown.sum()), int(mask.sum()))


class DarkBackdropResidueTests(unittest.TestCase):
    PROFILE = {"local_background_polarity": "light_text_on_dark_bg",
               "local_background_median_bgr": [0.0, 0.0, 0.0],
               "local_background_luminance_std": 5.0}

    def _scene(self):
        original = np.zeros((60, 100, 3), np.uint8)
        original[20:40, 20:80] = 255  # bright lettering under the mask
        mask = np.zeros((60, 100), np.uint8)
        mask[15:45, 15:85] = 1
        result = original.copy()
        result[mask > 0] = 0
        result[18:22, 30:70] = 40   # fill residue: above the backdrop, far below the contrast
        result[30:34, 30:40] = 200  # real bright content the fill produced: must stay
        return original, mask, result

    def test_residue_inside_the_mask_returns_to_the_backdrop(self):
        original, mask, result = self._scene()
        out = ob._flatten_dark_backdrop_residue(result.copy(), original, mask, dict(self.PROFILE))
        self.assertEqual(int(out[18:22, 30:70].max()), 0)
        self.assertEqual(int(out[30:34, 30:40].min()), 200)

    def test_pixels_outside_the_mask_are_never_touched(self):
        original, mask, result = self._scene()
        result[5:8, 5:30] = 40  # outside the mask
        out = ob._flatten_dark_backdrop_residue(result.copy(), original, mask, dict(self.PROFILE))
        self.assertTrue(np.array_equal(out[5:8, 5:30], result[5:8, 5:30]))

    def test_other_backdrops_and_polarities_are_left_alone(self):
        original, mask, result = self._scene()
        for override in ({"local_background_polarity": "dark_text_on_light_bg"},
                         {"local_background_median_bgr": [120.0, 120.0, 120.0]},
                         {"local_background_luminance_std": 30.0}):
            with self.subTest(override=override):
                profile = {**self.PROFILE, **override}
                out = ob._flatten_dark_backdrop_residue(result.copy(), original, mask, profile)
                self.assertTrue(np.array_equal(out, result))


if __name__ == "__main__":
    unittest.main()
