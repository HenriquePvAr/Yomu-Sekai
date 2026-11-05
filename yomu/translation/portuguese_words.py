"""Words of a pt-BR translation that are not Portuguese ("ESTOVA ESPERANDO").

DeepL occasionally returns a non-word; nothing downstream noticed, because the
validators ask whether the text is Portuguese overall, not whether each word is.
The table (assets/lexicon/portuguese_freq.tsv.gz, from wordfreq, CC BY-SA 4.0)
covers ~148,000 forms. A word the source itself carries (a name, "COSSACK") or
an English word kept on purpose is never counted.
"""
from __future__ import annotations

import functools
import gzip
import re
import unicodedata

_WORD = re.compile(r"[A-Za-zÀ-ÖØ-öø-ÿ]+")
MIN_WORD_LENGTH = 4


@functools.lru_cache(maxsize=1)
def _portuguese_words() -> frozenset[str]:
    from yomu.runtime.paths import REPO_ROOT

    path = REPO_ROOT / "assets" / "lexicon" / "portuguese_freq.tsv.gz"
    try:
        with gzip.open(path, "rt", encoding="utf-8") as handle:
            words = set()
            for line in handle:
                word = line.split("\t", 1)[0].strip()
                if word:
                    words.update(word.split("-"))
            # Accent-free forms too: the table spells "SAIRMOS", DeepL "SAÍRMOS".
            return frozenset(words | {_fold(word) for word in words})
    except OSError:
        return frozenset()


def _fold(text: str) -> str:
    return "".join(c for c in unicodedata.normalize("NFKD", str(text or "").upper()) if not unicodedata.combining(c))


def unknown_target_words(translation: str, source: str = "") -> list[str]:
    """Words of ``translation`` that are neither Portuguese nor taken from ``source``."""
    vocabulary = _portuguese_words()
    if not vocabulary:
        return []
    from yomu.review.region_taxonomy import is_english_word

    source_words = {_fold(word) for word in _WORD.findall(str(source or ""))}
    # Glued source tokens ("SEOKJINKIM") still carry the name the translation splits out.
    source_letters = re.sub(r"[^A-Z]", "", _fold(source))
    unknown = []
    for word in _WORD.findall(str(translation or "")):
        key = unicodedata.normalize("NFC", word.upper())
        folded = _fold(key)
        if (len(key) < MIN_WORD_LENGTH or key in vocabulary or folded in vocabulary or folded in source_words
                or folded in source_letters or is_english_word(folded)):
            continue
        if key not in unknown:
            unknown.append(key)
    return unknown


MIN_RESTORE_SIMILARITY = 0.55


def restore_corrupted_source_words(translation: str, source: str, unknown: list[str]) -> str:
    """Put back the source word a provider turned into a non-word ("GEHENNA" -> "GEENOM").

    A translation word Portuguese does not have, that resembles a source word the translation
    dropped, is that source word mangled: the source spelling is the only safe repair. Words
    with no close source counterpart (a real invented word) are left for review, untouched.
    """
    import difflib

    present = {_fold(w) for w in _WORD.findall(str(translation or ""))}
    candidates = [w for w in _WORD.findall(str(source or ""))
                  if len(w) >= MIN_WORD_LENGTH and _fold(w) not in present]
    repaired = str(translation or "")
    for bad in unknown:
        best, best_ratio = "", MIN_RESTORE_SIMILARITY
        for word in candidates:
            if _fold(word)[:1] != _fold(bad)[:1]:
                continue
            ratio = difflib.SequenceMatcher(None, _fold(word), _fold(bad)).ratio()
            if ratio >= best_ratio:
                best, best_ratio = word, ratio
        if best:
            repaired = re.sub(rf"\b{re.escape(bad)}\b", best.upper(), repaired, flags=re.IGNORECASE)
            candidates.remove(best)
    return repaired
