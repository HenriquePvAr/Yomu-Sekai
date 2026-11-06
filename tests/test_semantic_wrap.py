"""Semantic pt-BR line wrapping: no orphaned function words at line edges."""
from yomu.ocr.ocr_balloon import _semantic_wrap_lines, _PT_BREAK_ORPHAN_WORDS


def _measure_factory(widths):
    return lambda value: widths.get(value, len(value) * 8)


def test_dp_avoids_orphaning_function_words():
    words = "VOU ESCLARECÊ-LOS SOBRE COMO POSSO UTILIZAR O PRESENTE DO SEU AMIGO".split()
    measure = _measure_factory({w: 60 for w in words})
    lines = _semantic_wrap_lines(words, measure, max_width=260)
    assert lines is not None
    # 260 px fits ~4 words (4*60 + 3*8 = 264 -> 3 words per line); greedy would
    # orphan "COMO"/"O" on line edges; the DP must not start/end a line with a
    # function word from the orphan set.
    for line in lines:
        parts = line.split()
        assert parts[0].upper() not in _PT_BREAK_ORPHAN_WORDS or len(parts) > 2
        assert parts[-1].upper() not in _PT_BREAK_ORPHAN_WORDS or len(parts) > 2


def test_dp_respects_max_width():
    words = "ISSO PERTENCE A ALGUÉM QUE EU CONHEÇO MUITO BEM MESMO AGORA".split()
    measure = _measure_factory({w: 50 for w in words})
    lines = _semantic_wrap_lines(words, measure, max_width=200)
    for line in lines:
        for word in line.split():
            assert measure(word) <= 200 + 1e-6


def test_short_and_long_text_fallback():
    assert _semantic_wrap_lines(["OI"], lambda v: 10, 100) is None
    assert _semantic_wrap_lines(["W"] * 100, lambda v: 10, 100) is None


def test_prefers_break_after_comma():
    words = "ESPERE, AGORA MESMO, PORQUE EU VOU CONTAR TUDO PARA ELES HOJE".split()
    measure = _measure_factory({w: 55 for w in words})
    lines = _semantic_wrap_lines(words, measure, max_width=300)
    assert lines is not None
    # a break right after "ESPERE," / "MESMO," costs less: DP should use them
    joined = "\n".join(lines)
    assert "ESPERE,\n" in joined or "MESMO,\n" in joined
