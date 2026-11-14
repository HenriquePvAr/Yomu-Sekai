from komyst.ocr.ocr_balloon import _looks_like_noise


def test_quoted_and_parenthesized_text_is_not_noise():
    assert not _looks_like_noise('"ME?"')
    assert not _looks_like_noise("“ME?”")
    assert not _looks_like_noise("(OKAY)")


def test_real_noise_still_detected():
    assert _looks_like_noise("#@%^&*")
    assert _looks_like_noise("~|\/<>{}")
