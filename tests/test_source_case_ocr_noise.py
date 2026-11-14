"""All-caps lettering stays all caps although the OCR reads some case-alike letters as lowercase."""
from komyst.ocr.ocr_balloon import _match_source_case


def test_case_alike_lowercase_reads_do_not_break_all_caps():
    assert _match_source_case("WHO KNOWS? GO AHEAD, NOTo SURE.", "Quem sabe? Vai em frente.") == "QUEM SABE? VAI EM FRENTE."
    assert _match_source_case("THE RocK IS HERE", "a pedra está aqui") == "A PEDRA ESTÁ AQUI"
    assert _match_source_case("RocK?", "Rocha?") == "ROCHA?"  # 50 % lowercase, all of it case-alike
    assert _match_source_case("NOTo SoS", "nem sos") == "NEM SOS"


def test_real_mixed_case_source_is_kept():
    assert _match_source_case("Who knows? Go ahead.", "Quem sabe? Vai em frente.") == "Quem sabe? Vai em frente."
