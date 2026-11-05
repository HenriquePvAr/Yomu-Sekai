"""Protected lore terms: fixed renderings survive provider corruption."""
from yomu.translation.terms_glossary import enforce_protected_terms, protected_terms


def test_gehenna_corruption_is_repaired():
    fixed, repairs = enforce_protected_terms(
        "I'M TALKING ABOUT GEHENNA.", "ESTOU FALANDO DA GEENOM.")
    assert fixed == "ESTOU FALANDO DA GEHENNA."
    assert repairs == ("GEENOM->GEHENNA",)


def test_transposition_corruption_is_one_edit():
    fixed, repairs = enforce_protected_terms("I USED MY EST.", "USEI O MEU SET.")
    assert fixed == "USEI O MEU EST."
    assert repairs == ("SET->EST",)


def test_apostrophe_variant_of_rendering_is_accepted():
    # Letters-only comparison: "TUUMLIM" already carries the term.
    fixed, repairs = enforce_protected_terms("THE POWER OF TU'UMLIM.", "O PODER DO TUUMLIM.")
    assert fixed == "O PODER DO TUUMLIM."
    assert repairs == ()


def test_already_correct_target_is_untouched():
    fixed, repairs = enforce_protected_terms(
        "I'M TALKING ABOUT GEHENNA.", "ESTOU FALANDO DA GEHENNA.")
    assert fixed == "ESTOU FALANDO DA GEHENNA."
    assert repairs == ()


def test_ambiguous_corruption_is_fail_closed():
    # Two DIFFERENT corrupted tokens at the same distance: no guessing.
    fixed, repairs = enforce_protected_terms("GEHENNA OR GEHENNA.", "GEENOM E GEENAM.")
    assert fixed == "GEENOM E GEENAM."
    assert repairs == ()


def test_repeated_identical_corruption_is_fully_repaired():
    fixed, repairs = enforce_protected_terms("GEHENNA AND GEHENNA.", "GEENOM E GEENOM.")
    assert fixed == "GEHENNA E GEHENNA."


def test_unrelated_text_is_untouched():
    fixed, repairs = enforce_protected_terms("HELLO THERE.", "OLA.")
    assert fixed == "OLA."
    assert repairs == ()


def test_terms_data_file_is_well_formed():
    terms = protected_terms()
    assert "GEHENNA" in terms and terms["GEHENNA"] == "GEHENNA"
    assert "EST" in terms and terms["EST"] == "EST"
