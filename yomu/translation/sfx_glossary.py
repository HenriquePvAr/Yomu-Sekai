"""Portuguese (pt-BR) renderings of English sound effects and action labels.

A machine translator turns "BANG" into "BANG" or "estrondo" and "*bite*" into
"*mordida*" at best; scanlation convention is a pt-BR onomatopoeia ("BAM") or a
present-tense action label ("*morde*"). The glossary is a data file
(``assets/lexicon/sfx_en_pt.json``); a token is matched after collapsing
repeated letters ("BAAANG" -> "BANG"), and the stretch, case and decoration
(asterisks, punctuation) of the source are carried onto the result. Unknown
sounds return ``None`` and go to the provider like any other text.
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
