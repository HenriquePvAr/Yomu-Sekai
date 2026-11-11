"""Keep a measured chromatic glow on white lettering over a black backdrop."""
import test_support._test_bootstrap as _test_bootstrap  # noqa: F401

from pathlib import Path

import numpy as np
import pytest
from PIL import Image, ImageDraw, ImageFilter, ImageFont

from yomu.ocr import ocr_balloon as ob
from yomu.ocr.ocr_engine import OCRLine


def sample(glow=True):
    path = Path('C:/Windows/Fonts/comicbd.ttf')
    if not path.exists():
        pytest.skip('reference font unavailable')
    font = ImageFont.truetype(str(path), 40)
    alpha = Image.new('L', (640, 140))
    ImageDraw.Draw(alpha).text((30, 40), 'WHO GAVE US?', font=font, fill=255)
    image = Image.new('RGB', alpha.size, 'black')
    if glow:
        image.paste((180, 70, 220), mask=alpha.filter(ImageFilter.GaussianBlur(5)))
    image.paste('white', mask=alpha)
    box = alpha.getbbox()
    x,y,r,b = box
    line = OCRLine(text='WHO GAVE US?', raw_text='WHO GAVE US?', confidence=.99,
                   box=(x,y,r-x,b-y), polygon=np.array([[x,y],[r,y],[r,b],[x,b]],np.float32))
    group = ob.TextGroup('glow', lines=[line], text=line.text, classification='narration')
    return np.asarray(image)[:,:,::-1].copy(), group


def test_white_core_retains_its_measured_purple_glow():
    image, group = sample()
    lettering = ob.extract_original_lettering_profile(image, group, group.box)
    assert lettering['color_family'] == 'white'
    assert lettering['measured_neutral_glow'] is True
    red, green, blue = lettering['glow_color']
    assert red > green and blue > green
    profile = ob.typography_profile_for_region(image, group, group.box)
    assert profile['glow_color'] == lettering['glow_color']
    assert profile['source_glow_confident'] is True


def test_plain_white_type_does_not_invent_a_glow():
    image, group = sample(glow=False)
    lettering = ob.extract_original_lettering_profile(image, group, group.box)
    assert lettering['measured_neutral_glow'] is False
    assert lettering['glow_color'] is None
