"""Fixes measured on the boundary-candidate pages: smooth translucent boxes, lexical
words vs SFX, unread continuation rows, re-OCR crop margin, protected straight art."""
import cv2
import numpy as np

import yomu.ocr.ocr_balloon as ob
from yomu.ocr.ocr_engine import OCRLine
from yomu.review import region_taxonomy


def _line(text, box, line_id="L1", confidence=0.97):
    x, y, w, h = box
    poly = np.array([[x, y], [x + w, y], [x + w, y + h], [x, y + h]], np.int32)
    return OCRLine(text, confidence, poly, box, text, engine="synthetic",
                   metadata={"ocr_line_id": line_id})


def _group(text, box, classification="narration"):
    return ob.TextGroup(group_id="g", lines=[_line(text, box)], text=text,
                        classification=classification)


def _text_box(image, text, origin, scale, thickness):
    (w, h), base = cv2.getTextSize(text, cv2.FONT_HERSHEY_SIMPLEX, scale, thickness)
    cv2.putText(image, text, origin, cv2.FONT_HERSHEY_SIMPLEX, scale, (10, 10, 10), thickness, cv2.LINE_AA)
    return (origin[0] - 2, origin[1] - h - 2, w + 4, h + base + 4)


def test_edge_free_translucent_box_is_smooth_not_textured():
    # Faint art seen through a white box: low-frequency, non-planar, no edges.
    y, x = np.mgrid[0:200, 0:400]
    level = 232 + 9 * np.sin(x / 45.0) * np.cos(y / 38.0)
    image = np.repeat(np.clip(level, 0, 255)[..., None], 3, axis=2).astype(np.uint8)
    box = _text_box(image, "WERE OVERWHELMED.", (60, 110), 1.0, 2)
    group = _group("WERE OVERWHELMED.", box)
    ob._remove_text_for_group(image.copy(), image, group, strategy="primary")
    metrics = group.background_metrics
    assert metrics["local_background_spatial_edge_fraction"] <= 0.01
    assert metrics["local_background_spatial_class"] in {"SMOOTH_NONUNIFORM", "PROVEN_UNIFORM"}


def test_prose_on_art_is_promoted_and_sounds_are_not():
    allowed = region_taxonomy.weak_label_semantic_promotion_allowed
    assert allowed("unknown", "BY THE NIGHTMARE SPELL")
    assert not allowed("unknown", "THE TOWER")
    # One trailing-off dictionary word is speech; a romanised sound is not in the lexicon,
    # and a dictionary sound without trailing-off punctuation stays a sound.
    assert allowed("unknown", "INCREDIBLE...")
    assert allowed("unknown", "HOPELESS,")
    assert not allowed("unknown", "PAEHYEOK...")
    assert not allowed("unknown", "SCREECH")
    assert not allowed("unknown", "CRASH!")
    assert not allowed("unknown", "KABOOOM...")


def test_unread_row_below_a_confident_line_is_proposed_for_reocr():
    image = np.full((200, 300, 3), 245, np.uint8)
    first = _text_box(image, "THIS MUST", (60, 60), 1.0, 2)
    second = _text_box(image, "BE...", (95, 100), 1.0, 2)
    boxes = ob._lettering_continuation_boxes(image, [_line("THIS MUST", first)])
    sx, sy, sw, sh = second
    assert any(bx <= sx + sw // 2 <= bx + bw and by <= sy + sh // 2 <= by + bh
               for bx, by, bw, bh in boxes), boxes


def test_nothing_is_proposed_where_no_lettering_continues():
    image = np.full((200, 300, 3), 245, np.uint8)
    first = _text_box(image, "THIS MUST", (60, 60), 1.0, 2)
    assert ob._lettering_continuation_boxes(image, [_line("THIS MUST", first)]) == []


def test_reocr_crop_gets_a_margin_and_boxes_come_back_in_crop_coordinates():
    seen = {}

    class Engine:
        engine = "fake"

        def detect_lines(self, crop, **_kwargs):
            seen["shape"] = crop.shape
            margin = (crop.shape[0] - 30) // 2
            return [_line("IT...", (margin + 4, margin + 5, 20, 12))]

    candidates = ob._reocr_crop_candidates([Engine()], np.zeros((30, 60, 3), np.uint8))
    assert seen["shape"][0] > 30 and seen["shape"][1] > 60
    assert candidates[0][3][0].box == (4, 5, 20, 12)


def test_panel_border_behind_a_footnote_is_protected_and_the_text_removed():
    image = np.full((90, 420, 3), 252, np.uint8)
    box = _text_box(image, "OJOU-CHAN MEANS YOUNG LADY", (70, 44), 0.6, 1)
    border_y = box[1] + box[3] + 1
    cv2.line(image, (5, border_y), (415, border_y), (15, 15, 15), 2)
    group = _group("OJOU-CHAN MEANS YOUNG LADY", (box[0], box[1], box[2], box[3] + 3))
    cleaned, mask, metrics = ob._remove_text_for_group(image.copy(), image, group, strategy="primary")
    assert metrics["mask_valid"], metrics.get("reason")
    out = cv2.cvtColor(ob._apply_cleanup_mask(image.copy(), image, group, mask), cv2.COLOR_BGR2GRAY)
    gray = cv2.cvtColor(image, cv2.COLOR_BGR2GRAY)
    border = gray[border_y, 5:415] < 100
    assert np.mean(out[border_y, 5:415][border] < 100) > 0.95  # border kept
    text_rows = out[box[1]:border_y - 2, box[0]:box[0] + box[2]]
    assert int(np.count_nonzero(text_rows < 100)) < 0.02 * text_rows.size  # text gone


class _FakeInpainter:
    def __init__(self, fail=False):
        self.fail = fail
        self.calls = 0

    def reconstruct(self, image, mask):
        self.calls += 1
        if self.fail:
            raise ob.advanced_art_inpainting.AdvancedInpaintUnavailable("no model")
        out = image.copy()
        out[mask > 0] = (11, 22, 33)
        return out, {}


def _textured_case(spatial="STRUCTURED_OR_TEXTURED", profile="textured_art"):
    rng = np.random.default_rng(5)
    image = rng.integers(60, 200, (60, 120, 3), dtype=np.uint8)
    mask = np.zeros((60, 120), np.uint8)
    mask[20:40, 30:90] = 255
    group = _group("WORD", (30, 20, 60, 20))
    group.background_metrics = {"local_background_class": profile,
                                "local_background_spatial_class": spatial}
    return image, mask, group


def test_textured_region_is_reconstructed_by_the_learned_model(monkeypatch):
    fake = _FakeInpainter()
    monkeypatch.setattr(ob.config, "CLEAN_LEARNED_TEXTURE_FILL", True)
    monkeypatch.setattr(ob.config, "CLEAN_COMPARE_FILLS", False)  # routing, not the choice
    monkeypatch.setattr(ob.advanced_art_inpainting, "get_default_inpainter", lambda: fake)
    ob._LEARNED_FILL_CACHE.clear()
    image, mask, group = _textured_case()
    out = ob._apply_cleanup_mask(image.copy(), image, group, mask, strategy="primary")
    # The model's flat fill, shifted by the measured tone offset: one colour inside.
    filled = tuple(out[30, 60])
    assert len({tuple(v) for v in out[25:35, 40:80].reshape(-1, 3)}) == 1
    # The model works on the mask grown by 2 px (ghost-letter margin); nothing beyond.
    grown = cv2.dilate(mask, cv2.getStructuringElement(cv2.MORPH_ELLIPSE, (5, 5)))
    assert np.array_equal(out[grown == 0], image[grown == 0])
    assert tuple(out[19, 60]) == filled
    assert group.learned_texture_fill["status"] == "applied"
    ob._apply_cleanup_mask(image.copy(), image, group, mask, strategy="primary")
    assert fake.calls == 1  # same mask and context: cached


def test_learned_fill_falls_back_when_the_model_is_unavailable(monkeypatch):
    monkeypatch.setattr(ob.config, "CLEAN_LEARNED_TEXTURE_FILL", True)
    monkeypatch.setattr(ob.config, "CLEAN_COMPARE_FILLS", False)  # routing, not the choice
    monkeypatch.setattr(ob.advanced_art_inpainting, "get_default_inpainter", lambda: _FakeInpainter(fail=True))
    ob._LEARNED_FILL_CACHE.clear()
    image, mask, group = _textured_case()
    out = ob._apply_cleanup_mask(image.copy(), image, group, mask, strategy="primary")
    assert tuple(out[30, 60]) != (11, 22, 33)
    assert group.learned_texture_fill == {"status": "unavailable", "reason": "AdvancedInpaintUnavailable"}


def test_flat_regions_keep_the_classic_fill(monkeypatch):
    fake = _FakeInpainter()
    monkeypatch.setattr(ob.config, "CLEAN_LEARNED_TEXTURE_FILL", True)
    monkeypatch.setattr(ob.config, "CLEAN_COMPARE_FILLS", False)  # routing, not the choice
    monkeypatch.setattr(ob.advanced_art_inpainting, "get_default_inpainter", lambda: fake)
    ob._LEARNED_FILL_CACHE.clear()
    image, mask, group = _textured_case(spatial="PROVEN_UNIFORM", profile="solid_light")
    ob._apply_cleanup_mask(image.copy(), image, group, mask, strategy="primary")
    assert fake.calls == 0


def test_cached_learned_fill_never_rolls_back_pixels_outside_the_mask(monkeypatch):
    fake = _FakeInpainter()
    monkeypatch.setattr(ob.config, "CLEAN_LEARNED_TEXTURE_FILL", True)
    monkeypatch.setattr(ob.config, "CLEAN_COMPARE_FILLS", False)  # routing, not the choice
    monkeypatch.setattr(ob.advanced_art_inpainting, "get_default_inpainter", lambda: fake)
    ob._LEARNED_FILL_CACHE.clear()
    image, mask, group = _textured_case()
    big = np.zeros((200, 120, 3), np.uint8)
    big[:60] = image
    big_mask = np.zeros((200, 120), np.uint8)
    big_mask[:60] = mask
    ob._apply_cleanup_mask(big.copy(), big, group, big_mask, strategy="primary")
    later = big.copy()
    later[180:190, 10:110] = 255  # another group cleaned, far outside the context crop
    out = ob._apply_cleanup_mask(later.copy(), later, group, big_mask, strategy="primary")
    assert fake.calls == 1
    assert np.array_equal(out[180:190, 10:110], later[180:190, 10:110])


class _ReadingEngine:
    engine = "fake"

    def __init__(self, text):
        self.text = text

    def detect_lines(self, crop, **_kwargs):
        if not self.text:
            return []
        return [_line(self.text, (2, 2, 20, 10), confidence=0.9)]


def _ocr_check(monkeypatch, read_text, source="NOT THE CHEAP STUFF"):
    monkeypatch.setattr(ob.config, "CLEAN_RESIDUAL_OCR_CHECK", True)
    monkeypatch.setattr(ob, "_RESIDUAL_OCR_ENGINES", [_ReadingEngine(read_text)])
    group = _group(source, (10, 10, 80, 20))
    return ob._legible_source_residual(np.full((60, 120, 3), 200, np.uint8), group)


def test_residual_is_lifted_only_when_no_source_word_is_legible(monkeypatch):
    assert _ocr_check(monkeypatch, "")["status"] == "not_legible"
    assert _ocr_check(monkeypatch, "OTHER")["status"] == "not_legible"  # substring of nothing
    legible = _ocr_check(monkeypatch, "CHEAP")
    assert legible["status"] == "legible" and legible["legible_source_tokens"] == ["CHEAP"]


def test_residual_check_fails_closed_without_an_engine(monkeypatch):
    monkeypatch.setattr(ob.config, "CLEAN_RESIDUAL_OCR_CHECK", True)
    monkeypatch.setattr(ob, "_RESIDUAL_OCR_ENGINES", [])
    monkeypatch.setattr(ob, "_reocr_engines_for", lambda *_a, **_k: [])
    group = _group("NOT THE CHEAP STUFF", (10, 10, 80, 20))
    assert ob._legible_source_residual(np.zeros((60, 120, 3), np.uint8), group)["status"] == "unavailable"


def test_dark_backdrop_under_removed_white_letters_is_not_a_blotch():
    image = np.full((80, 200, 3), 20, np.uint8)
    image[30:50, 40:160] = 240  # white lettering block on a dark backdrop
    mask = np.zeros((80, 200), np.uint8)
    mask[30:50, 40:160] = 255
    cleaned = image.copy()
    cleaned[mask > 0] = 20
    group = _group("WORD", (40, 30, 120, 20))
    restored = ob._dark_blotch_artifact_metrics(image, cleaned, group, mask, "textured_art", "primary")
    assert not restored["dark_blotch_rejected"]
    # A light art line swallowed by the mask and painted dark is still erased art.
    art = np.full((80, 200, 3), 230, np.uint8)
    art[30:50, 40:160] = 140
    island = ob._dark_blotch_artifact_metrics(art, np.full_like(art, 20), group, mask, "textured_art", "primary")
    assert island["dark_blotch_rejected"]


def test_white_text_on_a_midtone_surround_is_masked_as_light_text():
    image = np.full((80, 200, 3), 125, np.uint8)
    box = _text_box(image, "WORD", (40, 55), 1.2, 3)
    gray = cv2.cvtColor(image, cv2.COLOR_BGR2GRAY)
    image[gray < 60] = 245  # white letters
    line = _line("WORD", box)
    level = ob._line_polarity_level(cv2.cvtColor(image, cv2.COLOR_BGR2GRAY), line, 190.0)
    assert level <= 118


def test_lexicon_knows_written_words_and_not_romanised_sounds():
    from yomu.review import region_taxonomy as taxonomy
    assert taxonomy.is_english_word("INCREDIBLE")
    assert not taxonomy.is_english_word("PAEHYEOK")
    assert not taxonomy.is_english_word("FWASHAA")


def test_text_touching_a_balloon_border_is_cleaned_without_erasing_the_border():
    rng = np.random.default_rng(11)  # irregular screen-tone art outside the balloon
    image = np.repeat(cv2.GaussianBlur(rng.integers(80, 230, (260, 420), dtype=np.uint8), (0, 0), 1.2)[..., None], 3, axis=2)
    cv2.ellipse(image, (210, 130), (110, 95), 0, 0, 360, (252, 252, 252), -1)
    cv2.ellipse(image, (210, 130), (110, 95), 0, 0, 360, (10, 10, 10), 3)
    texts = (("A DEATH-ROW", 140, 105), ("CONVICT LIKE HIM", 103, 140), ("EVER AGAIN.", 140, 175))
    boxes = [_text_box(image, text, (x, y), 0.75, 2) for text, x, y in texts]
    group = ob.TextGroup(group_id="b", lines=[_line(t, b, line_id=f"l{i}") for i, (t, b) in enumerate(zip(("A DEATH-ROW", "CONVICT LIKE HIM", "EVER AGAIN."), boxes))],
                         text="A DEATH-ROW CONVICT LIKE HIM EVER AGAIN.", classification="speech")
    border = np.zeros(image.shape[:2], np.uint8)
    cv2.ellipse(border, (210, 130), (110, 95), 0, 0, 360, 255, 3)
    _c, mask, metrics = ob._remove_text_for_group(image.copy(), image, group, strategy="primary")
    assert metrics["mask_valid"], metrics.get("reason")
    assert not np.any((mask > 0) & (border > 0))
    out = ob._apply_cleanup_mask(image.copy(), image, group, mask)
    assert np.array_equal(out[border > 0], image[border > 0])


def test_masked_page_rediscovery_adds_only_new_confident_lines(monkeypatch):
    known = _line("HE IS HERE", (20, 20, 120, 20), line_id="k")

    class Engine:
        engine = "fake"

        def detect_lines(self, image, **_kwargs):
            # The known line is painted with its surrounding colour, not its ink.
            assert image[30, 60].tolist() == [230, 230, 230]
            return [_line("STILL NOT FOUND.", (20, 80, 200, 22), confidence=0.92),
                    _line("HE IS HERE", (21, 21, 118, 19), confidence=0.99),  # already read
                    _line("XQZ", (20, 140, 40, 20), confidence=0.95)]           # not real words

    monkeypatch.setattr(ob, "_reocr_engines_for", lambda *_a, **_k: [Engine()])
    page = np.full((200, 300, 3), 230, np.uint8)
    page[20:40, 20:140] = 0  # the known line's ink
    lines, record = ob._masked_page_rediscovery(page, [known], "en", 1)
    assert [l.text for l in lines] == ["HE IS HERE", "STILL NOT FOUND."]
    assert record["accepted"] and record["new_lines"][0]["text"] == "STILL NOT FOUND."


def _halftone(period=6, angle=30, dot=1):
    yy, xx = np.mgrid[0:200, 0:320].astype(np.float32)
    a = np.deg2rad(angle)
    u, v = xx * np.cos(a) + yy * np.sin(a), -xx * np.sin(a) + yy * np.cos(a)
    du, dv = (u % period) - period / 2, (v % period) - period / 2
    tone = np.where(du * du + dv * dv <= (dot + 0.5) ** 2, 40, 235).astype(np.uint8)
    return np.repeat(cv2.GaussianBlur(tone, (0, 0), 0.6)[..., None], 3, axis=2)


def test_screentone_is_detected_and_noise_or_flat_is_not():
    mask = np.zeros((200, 320), np.uint8)
    mask[80:120, 60:260] = 255
    for period, angle in ((5, 45), (7, 15), (9, 0)):
        assert ob._screentone_around(_halftone(period, angle), mask), (period, angle)
    rng = np.random.default_rng(1)
    noise = np.repeat(cv2.GaussianBlur(rng.integers(60, 220, (200, 320), dtype=np.uint8), (0, 0), 1.5)[..., None], 3, axis=2)
    assert not ob._screentone_around(noise, mask)
    assert not ob._screentone_around(np.full((200, 320, 3), 235, np.uint8), mask)


def test_light_halftone_balloon_goes_to_the_learned_fill(monkeypatch):
    fake = _FakeInpainter()
    monkeypatch.setattr(ob.config, "CLEAN_LEARNED_TEXTURE_FILL", True)
    monkeypatch.setattr(ob.config, "CLEAN_COMPARE_FILLS", False)  # routing, not the choice
    monkeypatch.setattr(ob.advanced_art_inpainting, "get_default_inpainter", lambda: fake)
    ob._LEARNED_FILL_CACHE.clear()
    image = _halftone(6, 30)
    mask = np.zeros((200, 320), np.uint8)
    mask[90:110, 100:220] = 255
    group = _group("SINCE THIS", (100, 90, 120, 20))
    group.background_metrics = {"local_background_class": "solid_light",
                                "local_background_spatial_class": "SMOOTH_NONUNIFORM"}
    ob._apply_cleanup_mask(image.copy(), image, group, mask, strategy="primary")
    assert fake.calls == 1 and group.screentone_detected


def test_holes_enclosed_by_the_lettering_mask_are_filled():
    # Black letter cores inside a selected white outline ("*ding*" on a dark wall).
    mask = np.zeros((60, 200), np.uint8)
    cv2.rectangle(mask, (20, 15), (50, 45), 255, 4)       # closed outline: core is a hole
    cv2.rectangle(mask, (80, 15), (110, 45), 255, 4)
    mask[28:33, 108:114] = 0                               # notch: open to the outside
    group = _group("DING", (20, 15, 100, 30))
    filled, added = ob._fill_enclosed_glyph_holes(mask, group)
    assert filled[30, 35] == 255 and added > 0
    assert filled[30, 95] == 0                             # open shape is not a hole
    big = np.zeros((200, 200), np.uint8)
    cv2.rectangle(big, (10, 10), (190, 190), 255, 3)        # hole far larger than a glyph
    assert ob._fill_enclosed_glyph_holes(big, _group("A", (10, 10, 20, 20)))[1] == 0


def test_a_line_carried_through_the_mask_is_not_an_island():
    source = np.full((80, 160, 3), 120, np.uint8)
    source[38:42, :] = 250                                  # white line crossing the text
    mask = np.zeros((80, 160), np.uint8)
    mask[25:55, 50:110] = 255
    carried = source.copy()
    blob = source.copy()
    blob[38:42, :] = 120
    blob[30:36, 70:80] = 250                                # bright spot touching nothing
    blob[38:42, :][:, :50] = 250
    blob[38:42, :][:, 110:] = 250
    assert ob._fill_consistency_parts(source, carried, mask)["islands"] == 0
    assert ob._fill_consistency_parts(source, blob, mask)["islands"] > 0


def test_gradient_balloon_prefers_the_fill_that_follows_the_gradient():
    # Grey on the left, white on the right: a patch copied from the white side into
    # the grey side must lose against a fill that follows the gradient.
    x = np.tile(np.linspace(200, 255, 240), (80, 1))
    source = np.repeat(x[..., None], 3, axis=2).astype(np.uint8)
    mask = np.zeros((80, 240), np.uint8)
    mask[20:60, 30:210] = 255
    follows = source.copy()
    patched = source.copy()
    patched[20:60, 30:120] = 255
    score = lambda c: sum(v for k, v in ob._fill_consistency_parts(source, c, mask).items() if k != "step")
    assert score(follows) < score(patched)


def test_compared_fills_keep_the_one_consistent_with_the_ring(monkeypatch):
    class _Consistent(_FakeInpainter):
        def reconstruct(self, image, mask):
            self.calls += 1
            out = image.copy()
            out[mask > 0] = np.median(image[mask == 0], axis=0).astype(np.uint8)
            return out, {}

    monkeypatch.setattr(ob.config, "CLEAN_LEARNED_TEXTURE_FILL", True)
    monkeypatch.setattr(ob.config, "CLEAN_COMPARE_FILLS", True)
    for fake, expected in ((_FakeInpainter(), "classic"), (_Consistent(), None)):
        monkeypatch.setattr(ob.advanced_art_inpainting, "get_default_inpainter", lambda f=fake: f)
        ob._LEARNED_FILL_CACHE.clear()
        image, mask, group = _textured_case()
        ob._apply_cleanup_mask(image.copy(), image, group, mask, strategy="primary")
        assert fake.calls == 1
        assert set(group.fill_choice) >= {"chosen", "classic", "learned", "terms"}
        if expected:  # a flat (11, 22, 33) block in random texture loses
            assert group.fill_choice["chosen"] == expected
            assert group.fill_alternatives


def _outlined_bars(bottom_extra=4, art_left=False):
    gray = np.full((120, 260), 150, np.uint8)
    glyphs = np.zeros(gray.shape, bool)
    for x in range(60, 200, 20):
        glyphs[40:70, x:x + 8] = True
    outline = cv2.dilate(glyphs.astype(np.uint8), np.ones((3, 3), np.uint8)) > 0
    outline[70:70 + bottom_extra, 58:200] = True            # thicker stroke under the line
    gray[outline] = 255
    if art_left:
        gray[:, :57] = 255                                  # white art area beside the text
    gray[glyphs] = 10
    return gray, glyphs


def test_outline_thicker_under_the_line_is_followed():
    gray, glyphs = _outlined_bars()
    band, width = ob._group_stroke_band(gray, glyphs, [_line("III", (58, 38, 144, 34))])
    assert width >= 1
    assert band[72, 120] and band[73, 120]                  # beyond the typical width


def test_white_art_beside_the_text_is_not_taken_as_outline():
    gray, glyphs = _outlined_bars(art_left=True)
    band, width = ob._group_stroke_band(gray, glyphs, [_line("III", (58, 38, 144, 34))])
    assert width >= 1
    assert not band[50, 45]                                  # inside the white art area
    assert band[72, 150]                                     # the outline far from it stays


def test_letters_touching_grey_art_lines_are_still_letters():
    # White letters on a dark panel touching a grey diagonal: not "art of their colour".
    gray = np.full((80, 200), 20, np.uint8)
    gray[:, 66:68] = 125                                     # grey art line touching the letter
    component = np.zeros((30, 120), bool)
    component[5:25, 30:36] = True
    gray[25:45, 60:66] = 245
    limit = np.zeros(gray.shape, np.uint8)
    limit[18:52, 25:150] = 255
    assert not ob._component_continues_beyond_line(gray, component, (30, 20), limit, 20.0, 225.0)
    gray[:, 66:68] = 245                                     # same-colour art line running through
    assert ob._component_continues_beyond_line(gray, component, (30, 20), limit, 20.0, 225.0)


def test_learned_fill_tone_offset_is_removed(monkeypatch):
    # A model that returns the right texture a few levels too dark (measured bias):
    # the in-mask result is brought back to the surroundings' tone.
    class _Darker(_FakeInpainter):
        def reconstruct(self, image, mask):
            self.calls += 1
            out = image.copy()
            out[mask > 0] = np.clip(base.astype(int) - 5, 0, 255).astype(np.uint8)[mask > 0]
            return out, {}

    monkeypatch.setattr(ob.config, "CLEAN_LEARNED_TEXTURE_FILL", True)
    monkeypatch.setattr(ob.config, "CLEAN_COMPARE_FILLS", False)
    rng = np.random.default_rng(3)
    base = np.clip(150 + rng.normal(0, 3, (60, 120, 3)), 0, 255).astype(np.uint8)
    image = base.copy()
    mask = np.zeros((60, 120), np.uint8)
    mask[20:40, 30:90] = 255
    image[mask > 0] = 20                                      # the lettering
    group = _group("WORD", (30, 20, 60, 20))
    group.background_metrics = {"local_background_class": "textured_art",
                                "local_background_spatial_class": "STRUCTURED_OR_TEXTURED"}
    monkeypatch.setattr(ob.advanced_art_inpainting, "get_default_inpainter", lambda: _Darker())
    ob._LEARNED_FILL_CACHE.clear()
    out = ob._apply_cleanup_mask(image.copy(), image, group, mask, strategy="primary")
    inside = out[25:35, 40:80].astype(int) - base[25:35, 40:80].astype(int)
    assert abs(float(np.median(inside))) <= 1
    assert all(abs(v - 5) <= 1 for v in group.learned_texture_fill["tone_offset_bgr"])


def test_lettering_outline_redrawn_by_the_fill_is_a_ghost():
    rng = np.random.default_rng(1)
    source = np.clip(120 + rng.normal(0, 1, (120, 240, 3)), 0, 255).astype(np.uint8)
    mask = np.zeros((120, 240), np.uint8)
    cv2.putText(mask, "WORD", (30, 80), cv2.FONT_HERSHEY_SIMPLEX, 2.0, 255, 9)
    clean = source.copy()
    ghost = source.copy()
    ghost[mask > 0] = 150                                       # the letters' shape, lighter
    assert not ob._lettering_contour_ghost_metrics(source, clean, mask)["lettering_contour_ghost"]
    assert ob._lettering_contour_ghost_metrics(source, ghost, mask)["lettering_contour_ghost"]


def test_tone_offset_is_measured_locally_across_two_backgrounds(monkeypatch):
    # Mask spanning a white area and a grey one: the fill matches each side; the
    # difference between the two sides is content, not a model bias.
    class _Exact(_FakeInpainter):
        def reconstruct(self, image, mask):
            self.calls += 1
            out = image.copy()
            out[mask > 0] = truth[mask > 0]
            return out, {}

    truth = np.full((80, 200, 3), 240, np.uint8)
    truth[:, 100:] = 90
    image = truth.copy()
    mask = np.zeros((80, 200), np.uint8)
    mask[25:55, 20:180] = 255
    image[mask > 0] = 10
    group = _group("WORD", (20, 25, 160, 30))
    monkeypatch.setattr(ob.advanced_art_inpainting, "get_default_inpainter", lambda: _Exact())
    ob._LEARNED_FILL_CACHE.clear()
    out = ob._learned_inpaint(image, group, mask)
    assert all(abs(v) <= 1 for v in group.learned_texture_fill["tone_offset_bgr"])
    assert int(out[40, 50, 0]) == 240 and int(out[40, 150, 0]) == 90


def test_letters_of_two_touching_lines_are_not_art():
    gray = np.full((100, 200), 200, np.uint8)
    gray[20:45, 40:46] = 20                                     # letter of line 1 ...
    gray[45:75, 40:46] = 20                                     # ... joined to a letter of line 2
    component = np.zeros((30, 120), bool)
    component[0:25, 10:16] = True
    one_line = np.zeros(gray.shape, np.uint8)
    one_line[18:47, 25:150] = 255
    both = one_line.copy()
    both[44:78, 25:150] = 255
    assert ob._component_continues_beyond_line(gray, component, (30, 20), one_line, 200.0, 180.0)
    assert not ob._component_continues_beyond_line(gray, component, (30, 20), both, 200.0, 180.0)


def test_line_box_mask_covers_every_line_padded_and_spares_protected_art():
    group = ob.TextGroup(group_id="g", lines=[_line("A", (20, 10, 60, 20), "L1"), _line("B", (20, 40, 80, 20), "L2")],
                         text="A B", classification="speech")
    base = np.zeros((100, 140), np.uint8)
    protect = np.zeros((100, 140), np.uint8)
    protect[:, 70] = 1
    group.structure_protect_mask = protect
    mask = ob._line_box_mask(group, base)
    assert mask[12, 25] and mask[45, 95] and mask[8, 22]       # boxes plus the outline pad
    assert not mask[30 + 20, 70] and not mask[90, 30]


def test_translation_follows_the_balloon_shape_and_avoids_neighbours():
    from PIL import Image, ImageDraw
    area = np.zeros((300, 300), np.uint8)
    cv2.ellipse(area, (150, 150), (120, 90), 0, 0, 360, 1, -1)
    area = area > 0
    draw = ImageDraw.Draw(Image.new("RGB", (300, 300)))
    font = ob.get_font(ob.config.FONT_PATH, 20, role="regular", text="X")
    text = "UMA FRASE BEM COMPRIDA PARA TESTAR A FORMA DO BALAO OVAL"
    layout = ob._balloon_shape_layout(draw, text, font, area, (150, 150), 2, 1)
    assert layout and " ".join(item[0] for item in layout) == text
    widths = [draw.textlength(item[0], font=font) for item in layout]
    middle = len(widths) // 2
    assert widths[middle] >= max(widths[0], widths[-1])          # wide in the middle of the oval
    for line, lx, ly in layout:                                   # every line inside the balloon
        x1, y1, x2, y2 = draw.textbbox((lx, ly), line, font=font, stroke_width=1)
        assert area[int(y1), int(x1)] and area[int(y2), int(x2)]
    group = _group("X", (120, 130, 60, 40))
    group.light_enclosure_interior = area
    group.neighbor_text_boxes = [(40, 140, 50, 30)]
    shaped = ob._balloon_text_area(group, area.shape)
    assert shaped is not None and not shaped[150, 60]             # the other text's place stays free


def test_mostly_digit_lines_with_real_words_are_kept():
    assert ob._holds_real_word("56,984 Won")
    assert ob._holds_real_word("AccountNo.!!-22334444")
    assert not ob._holds_real_word("111-2233 44")


def test_bounded_edit_distance_matches_the_full_one_within_the_limit():
    from yomu.ocr import ocr_engine
    for a, b in (("house", "horse"), ("kitten", "sitting"), ("abc", "abc"), ("short", "longerword")):
        full = ocr_engine._edit_distance(a, b)
        bounded = ocr_engine._bounded_edit_distance(a, b, 2)
        assert bounded == full if full <= 2 else bounded == 3


def test_outline_measured_without_guessing_the_ink_polarity():
    # Black letters with a white outline on mid grey, mask holding part of the outline.
    gray = np.full((120, 260), 122, np.uint8)
    glyphs = np.zeros(gray.shape, bool)
    for x in range(60, 200, 20):
        glyphs[40:70, x:x + 8] = True
    outline = cv2.dilate(glyphs.astype(np.uint8), np.ones((7, 7), np.uint8)) > 0
    gray[outline] = 250
    gray[glyphs] = 8
    mask = cv2.dilate(glyphs.astype(np.uint8), np.ones((3, 3), np.uint8)) > 0
    band, width = ob._group_stroke_band(gray, mask, [_line("III", (58, 38, 144, 34))])
    assert width >= 1 and band[72, 64]


def test_drawn_translation_is_leaned_like_the_italic_source():
    img = np.full((200, 400), 255, np.uint8)
    cv2.putText(img, "HELLO", (40, 130), cv2.FONT_HERSHEY_SIMPLEX, 2.5, 0, 8)
    upright = (img < 128).astype(np.uint8)
    italic = cv2.warpAffine(upright, np.float32([[1, -0.3, 45], [0, 1, 0]]), (400, 200))
    source_deg = ob._text_slant_degrees(italic)
    base = np.full((200, 400, 3), 255, np.uint8)
    drawn = base.copy()
    drawn[upright > 0] = 0
    group = _group("X", (0, 0, 400, 200))
    profile = {"glyph_style": {"confidence": 1.0, "slant": "italic", "slant_degrees": source_deg}}
    out = ob._match_source_slant(base, drawn, group, profile, (0, 0, 400, 200))
    assert group.slant_match["applied"]
    assert abs(ob._text_slant_degrees((out[..., 0] < 128).astype(np.uint8)) - source_deg) <= 2
    # Upright source (a small reading is noise): nothing changes.
    same = ob._match_source_slant(base, drawn, group, {"glyph_style": {"confidence": 1.0, "slant": "normal", "slant_degrees": 4.0}},
                                  (0, 0, 400, 200))
    assert np.array_equal(same, drawn)


def test_light_art_carried_through_the_lettering_is_not_a_white_patch():
    # Pale sky with a bright ray crossing dark lettering: the reconstruction carries
    # the ray on, which must not read as a white patch.
    source = np.full((120, 240, 3), 228, np.uint8)
    source[:, 110:120] = 252                                   # the light ray
    mask = np.zeros((120, 240), np.uint8)
    mask[40:80, 40:200] = 255
    original = source.copy()
    original[mask > 0] = 10
    group = _group("JUMP", (40, 40, 160, 40), classification="sfx")
    group.background_metrics = {}
    clean = ob._white_patch_artifact_metrics(original, source, group, mask, "textured_art")
    assert not clean["white_patch_rejected"]
    patch = source.copy()
    patch[45:75, 50:100] = 255                                 # white block on the pale sky
    assert ob._white_patch_artifact_metrics(original, patch, group, mask, "textured_art")["white_patch_rejected"]


def test_interjections_and_names_echoed_by_the_provider_are_kept():
    for text, cls in (("A-AH...", "speech"), ("RYU KANG-MIN?", "speech"), ("THROB", "sfx")):
        assert ob._echo_is_name_shaped(_group(text, (0, 0, 50, 20), classification=cls)), text
    assert not ob._echo_is_name_shaped(_group("WHAT ARE YOU DOING?", (0, 0, 50, 20), classification="speech"))
