"""The cached art-continuation check must answer exactly like the original, component by component."""
import cv2
import numpy as np

from komyst.ocr import ocr_balloon as ob


def _scene(seed):
    rng = np.random.default_rng(seed)
    gray = np.full((260, 420), 235, np.uint8)
    for _ in range(14):  # letters
        x, y = int(rng.integers(40, 360)), int(rng.integers(90, 150))
        cv2.putText(gray, chr(int(rng.integers(65, 90))), (x, y), cv2.FONT_HERSHEY_SIMPLEX, 1.2, 20, 3)
    cv2.line(gray, (0, 30), (419, 200), 25, 3)  # an art line of the lettering's colour crossing the line
    cv2.line(gray, (60, 0), (90, 259), 25, 2)
    return gray


def test_cached_check_matches_the_original_for_every_component():
    for seed in range(4):
        gray = _scene(seed)
        x1, y1, w, h = 30, 70, 360, 100
        roi = gray[y1:y1 + h, x1:x1 + w]
        foreground = (roi <= 120).astype(np.uint8) * 255
        count, labels, stats, _ = cv2.connectedComponentsWithStats(foreground, 8)
        line_limit = np.zeros_like(gray)
        line_limit[y1 - 6:y1 + h + 6, x1 - 6:x1 + w + 6] = 255
        cache = {}
        for label in range(1, count):
            expected = ob._component_continues_beyond_line(gray, labels == label, (x1, y1), line_limit, 235.0, 200.0)
            got = ob._component_continues_beyond_line_cached(gray, labels, label, stats[label], (x1, y1),
                                                             line_limit, 235.0, 200.0, cache)
            assert got == expected, (seed, label)
