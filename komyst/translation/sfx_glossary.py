"""Portuguese (pt-BR) renderings of English sound effects and action labels.

A machine translator turns "BANG" into "BANG" or "estrondo" and "*bite*" into
"*mordida*" at best; scanlation convention is a pt-BR onomatopoeia ("BAM") or a
present-tense action label ("*morde*"). The glossary is a data file
(``assets/lexicon/sfx_en_pt.json``); a token is matched after collapsing
repeated letters ("BAAANG" -> "BANG"), and the stretch, case and decoration
(asterisks, punctuation) of the source are carried onto the result. Unknown
sounds return ``None``; the pipeline then keeps the source lettering (a
provider turns an unknown sound into a dictionary word, "PRESS" -> "IMPRENSA").
"""
from __future__ import annotations

import json
import re
from functools import lru_cache
from pathlib import Path

_GLOSSARY_PATH = Path(__file__).resolve().parents[2] / "assets" / "lexicon" / "sfx_en_pt.json"


@lru_cache(maxsize=1)
def _glossary() -> dict[str, str]:
    data = json.loads(_GLOSSARY_PATH.read_text(encoding="utf-8"))
    return {str(k).lower(): str(v) for k, v in data.items()}


def _collapse(word: str) -> str:
    return re.sub(r"(.)\1+", r"\1", word.lower())


@lru_cache(maxsize=1)
def _collapsed_index() -> dict[str, tuple[str, str]]:
    return {_collapse(key): (key, value) for key, value in _glossary().items()}


def _lookup(word: str) -> tuple[str, str] | None:
    """(glossary key, pt-BR value) for ``word``, stretched letters allowed ("BOOOM")."""
    glossary = _glossary()
    lower = word.lower()
    if lower in glossary:
        return lower, glossary[lower]
    return _collapsed_index().get(_collapse(lower))


def _stretch(target: str, source: str, key: str) -> str:
    """Repeat the target's last vowel as much as the source outstretches the key."""
    extra = len(source) - len(key)
    if extra <= 0:
        return target
    match = re.search(r"[aeiouAEIOUãõáéíóú](?=[^aeiouAEIOUãõáéíóú]*$)", target)
    if not match:
        return target
    i = match.start()
    return target[:i + 1] + target[i] * extra + target[i + 1:]


def _match_case(target: str, source: str) -> str:
    letters = [c for c in source if c.isalpha()]
    if letters and all(c.isupper() for c in letters):
        return target.upper()
    if letters and letters[0].isupper():
        return target[:1].upper() + target[1:]
    return target.lower()


def translate_sfx(text: str) -> str | None:
    """pt-BR rendering of a sound effect / action label, or ``None`` if unknown."""
    source = str(text or "").strip()
    words = re.findall(r"[A-Za-z]+", source)
    if not words:
        return None
    phrase = " ".join(words)
    whole = _lookup(phrase)
    if whole is not None:
        key, value = whole
        rendered = _match_case(_stretch(value, words[0], key) if len(words) == 1 else value, phrase)
        spans = [m.span() for m in re.finditer(r"[A-Za-z]+", source)]
        # The whole phrase, separators included ("BA-DUMP", "SIT FORWARD").
        return source[:spans[0][0]] + rendered + source[spans[-1][1]:]
    out = source
    for word in words:
        found = _lookup(word)
        if found is None:
            return None
        key, value = found
        out = out.replace(word, _match_case(_stretch(value, word, key), word), 1)
    return out


def _edit_distance_within(left: str, right: str, limit: int) -> int | None:
    """Optimal-string-alignment distance, bounded by ``limit`` (``None`` past it).

    Adjacent-glyph swaps count as one edit: OCR corrupts by substitution,
    insertion, deletion AND transposition ("SET" for "EST").
    """

    if abs(len(left) - len(right)) > limit:
        return None
    if left == right:
        return 0
    size = len(right)
    previous = list(range(size + 1))
    before_previous: list[int] | None = None
    for row_index, left_char in enumerate(left, start=1):
        current = [row_index] + [0] * size
        for column_index, right_char in enumerate(right, start=1):
            cost = min(
                previous[column_index - 1] + (left_char != right_char),
                previous[column_index] + 1,
                current[column_index - 1] + 1,
            )
            if (
                before_previous is not None
                and row_index >= 2
                and column_index >= 2
                and left_char == right[column_index - 2]
                and left[row_index - 2] == right_char
            ):
                cost = min(cost, before_previous[column_index - 2] + 1)
            current[column_index] = cost
        before_previous, previous = previous, current
    distance = previous[-1]
    return distance if distance <= limit else None


def _fuzzy_word_limit(length: int) -> int:
    # Short tokens get no slack: "VAS" must never wander into an unrelated
    # sound. Medium tokens tolerate one misread glyph, long ones two.
    if length <= 3:
        return 0
    if length <= 4:
        # Same-length substitution only; the lookup loop additionally refuses
        # length changes for these short tokens.
        return 1
    if length <= 5:
        return 1
    return 2


@lru_cache(maxsize=1)
def _fuzzy_index() -> tuple[tuple[str, str, str], ...]:
    """Precomputed (letters-only key, collapsed key, value) rows for the fuzzy pass."""

    return tuple(
        (letters, _collapse(letters), value)
        for key, value in _glossary().items()
        for letters in (re.sub(r"[^A-Za-z]", "", key),)
        if letters
    )


@lru_cache(maxsize=1)
def _english_lexicon() -> frozenset[str]:
    """Letters-only lowercase words, used to refuse fuzzy matches on real words.

    "ROCK?" is a shouted name (an English word), not a misread of "TOCK": a
    real word must never be rewritten into an onomatopoeia by the fuzzy pass.
    """

    from gzip import open as gzip_open

    words: set[str] = set()
    path = Path(__file__).resolve().parents[2] / "assets" / "lexicon" / "english_words.txt.gz"
    try:
        with gzip_open(path, "rt", encoding="utf-8", errors="replace") as handle:
            for line in handle:
                entry = re.sub(r"[^A-Za-z]", "", line.strip())
                if entry:
                    words.add(entry.lower())
    except OSError:
        return frozenset()
    return frozenset(words)


def _vowel_only_difference(shorter: str, longer: str) -> bool:
    """Whether deleting one vowel from ``longer`` yields ``shorter``.

    OCR on stylized caps most often drops or adds a vowel ("SMSH" for "SMASH");
    a consonant change at this length is where false positives live, so those
    stay forbidden for short tokens.
    """

    if len(longer) - len(shorter) != 1:
        return False
    for index, char in enumerate(longer):
        if char in "aeiou" and longer[:index] + longer[index + 1:] == shorter:
            return True
    return False


def _fuzzy_lookup(word: str) -> tuple[str, str, int] | None:
    """(glossary key, pt-BR value, edit distance) allowing OCR misreads."""

    exact = _lookup(word)
    if exact is not None:
        return (*exact, 0)
    letters = re.sub(r"[^A-Za-z]", "", str(word or ""))
    if not letters:
        return None
    limit = _fuzzy_word_limit(len(letters))
    if limit <= 0:
        return None
    if letters.lower() in _english_lexicon():
        # A real word keeps its meaning (or the name path handles it); the
        # fuzzy pass exists for glyph damage, not for vocabulary.
        return None
    collapsed_query = _collapse(letters)
    short_token = len(letters) <= 4
    best: tuple[str, str, int] | None = None
    for key_letters, key_collapsed, value in _fuzzy_index():
        if short_token and len(key_letters) != len(letters):
            if not (
                _vowel_only_difference(collapsed_query, key_collapsed)
                or _vowel_only_difference(key_collapsed, collapsed_query)
            ):
                continue
        distance = _edit_distance_within(collapsed_query, key_collapsed, limit)
        if distance is None:
            continue
        if best is None or distance < best[2]:
            best = (key_letters, value, distance)
            if distance == 0:
                break
    return best


def translate_sfx_fuzzy(text: str) -> str | None:
    """pt-BR rendering tolerant of OCR misreads, or ``None`` if not a known sound.

    Same contract as ``translate_sfx`` (unknown -> None, decorations and case
    preserved), but a token a few edits away from a glossary entry still hits,
    which is what lets "CLAMTER" clean to "barulho". Exact matches win; the
    fuzzy pass only runs when the exact lookup found nothing.
    """

    source = str(text or "").strip()
    exact = translate_sfx(source)
    if exact is not None:
        return exact
    words = re.findall(r"[A-Za-z]+", source)
    if not words:
        return None
    if len(words) == 1:
        found = _fuzzy_lookup(words[0])
        if found is None:
            return None
        key, value, distance = found
        if distance == 0:
            rendered = _match_case(_stretch(value, words[0], key), words[0])
        else:
            # OCR noise like "FluCK" carries no casing evidence; comic SFX
            # lettering is caps, so follow the majority of the source letters.
            uppers = sum(1 for char in words[0] if char.isupper())
            lowered = sum(1 for char in words[0] if char.islower())
            rendered = value.upper() if uppers >= lowered else value.lower()
        spans = [m.span() for m in re.finditer(r"[A-Za-z]+", source)]
        return source[:spans[0][0]] + rendered + source[spans[-1][1]:]
    # Multi-word phrases only match exactly (fuzzy multi-word would wander).
    return None
