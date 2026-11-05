"""Protected lore terms and names: fixed pt-BR renderings that must survive translation.

Story vocabulary ("EST", "GIFT", place and artifact names) is terminology, not
ordinary vocabulary: a machine translator renders "Gehenna" as "Geenom" and
"Gift" as "presente", and both read as translation errors to a reader of the
series. The data file (``assets/lexicon/terms_en_pt.json``) maps each source
term to the exact rendering the output must carry (for names, the name itself).

``enforce_protected_terms`` repairs a provider candidate after translation: if
the source used a protected term and the target does not carry its rendering,
the most plausible corrupted token (bounded edit distance, unambiguous) is
rewritten. When no token can be blamed confidently the target is left untouched
(fail-closed) and the existing validation/retry gates decide.
"""
from __future__ import annotations

import json
import re
from functools import lru_cache
from pathlib import Path

_GLOSSARY_PATH = Path(__file__).resolve().parents[2] / "assets" / "lexicon" / "terms_en_pt.json"


@lru_cache(maxsize=1)
def protected_terms() -> dict[str, str]:
    """Uppercase source term -> required rendering (may be identical, e.g. names)."""

    data = json.loads(_GLOSSARY_PATH.read_text(encoding="utf-8"))
    return {str(key).strip().upper(): str(value).strip() for key, value in data.items()}


def _letters(text: str) -> str:
    return re.sub(r"[^A-Za-z]", "", str(text or ""))


def _edit_distance_within(left: str, right: str, limit: int) -> int | None:
    """Optimal-string-alignment distance (transposition = one edit), bounded."""

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


def _term_used_in_source(term: str, source: str) -> bool:
    pattern = r"(?<![A-Za-z])" + re.escape(term) + r"(?![A-Za-z])"
    return bool(re.search(pattern, str(source or ""), flags=re.IGNORECASE))


def _rendering_present(rendered: str, target: str) -> bool:
    # Letters-only substring: punctuation between glyphs ("TU'UMLIM", "TUUMLIM")
    # must not defeat the presence check.
    return _letters(rendered).upper() in _letters(target).upper()


def _distance_limit(reference: str) -> int:
    length = len(_letters(reference))
    if length >= 6:
        return 3
    if length >= 5:
        return 2
    return 1


def enforce_protected_terms(source: str, target: str) -> tuple[str, tuple[str, ...]]:
    """Rewrite corrupted protected-term tokens in ``target``; never invent text.

    Returns (possibly repaired target, repair descriptions). A repair only
    happens when exactly one target token is within bounded edit distance of
    the required rendering (or of the source term), so an ambiguous target is
    left for the validation gates instead of being guessed at. Several tokens
    corrupted the same way are each repaired (one pass per occurrence).
    """

    target = str(target or "")
    if not target.strip():
        return target, ()
    repairs: list[str] = []
    source = str(source or "")
    for term, rendered in protected_terms().items():
        if not _term_used_in_source(term, source):
            continue
        expected_letters = _letters(rendered).upper()
        term_letters = _letters(term).upper()
        limit = max(_distance_limit(rendered), _distance_limit(term))
        for _ in range(4):
            if _rendering_present(rendered, target):
                break
            candidates: dict[str, tuple[int, int]] = {}
            for match in re.finditer(r"[A-Za-z]+", target):
                token = match.group(0)
                token_letters = _letters(token).upper()
                if not token_letters or token_letters == expected_letters:
                    continue
                distance: int | None = None
                for reference in (expected_letters, term_letters):
                    candidate = _edit_distance_within(token_letters, reference, limit)
                    if candidate is not None and (distance is None or candidate < distance):
                        distance = candidate
                if distance is None:
                    continue
                if token not in candidates or distance < candidates[token][0]:
                    candidates[token] = (distance, match.start())
            if not candidates:
                break
            best_distance = min(value[0] for value in candidates.values())
            best_texts = sorted(
                token for token, value in candidates.items() if value[0] == best_distance
            )
            if len(best_texts) != 1:
                # Two different corruptions at the same distance: which one owns
                # the term cannot be decided; leave it to the validation gates.
                break
            best_text = best_texts[0]
            letters_only = best_text
            if letters_only.isupper():
                replacement = rendered.upper()
            elif letters_only.islower():
                replacement = rendered.lower()
            else:
                replacement = rendered
            pattern = r"(?<![A-Za-z])" + re.escape(best_text) + r"(?![A-Za-z])"
            target = re.sub(pattern, replacement.replace("\\", "\\\\"), target)
            repairs.append(f"{best_text}->{replacement}")
    return target, tuple(repairs)
