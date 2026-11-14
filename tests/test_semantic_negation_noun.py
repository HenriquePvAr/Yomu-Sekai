from komyst.translation.semantic_fidelity import _negation_asymmetry


def test_a_nobody_noun_is_not_a_verbal_negation():
    assert not _negation_asymmetry("IF HE IS A NOBODY, LEAVE.", "Se ele for um qualquer, va embora.")
    assert not _negation_asymmetry("She is an nobody here.", "Ela é uma pessoa comum aqui.")
    assert not _negation_asymmetry("He is some nobody.", "Ele é um qualquer.")


def test_real_negation_still_detected():
    assert _negation_asymmetry("NOBODY CAME.", "Vieram todos.")
    assert _negation_asymmetry("HE IS NOT A NOBODY.", "Ele é um qualquer.")
    assert not _negation_asymmetry("HE IS NOT A NOBODY.", "Ele não é um qualquer.")
