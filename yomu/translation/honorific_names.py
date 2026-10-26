"""Names addressed by an abbreviated honorific ("MS. GO"), found in the source text.

An abbreviated form of address is never a verb or a common noun, so the token
right after one is a name even when it is short or an English word: DeepL read
"WITH MS. GO ALONE" as "go alone" and the render kept "SRA. GO ALONE". MISS,
SIR and LADY are left out on purpose ("I MISS YOU" is a verb).
"""
from __future__ import annotations

import html
import re

HONORIFIC_ABBREVIATIONS = ("MRS", "MR", "MS", "DR", "PROF")
_NOT_A_NAME = frozenset({"AND", "OR", "THE", "A", "AN", "OF"})
_PATTERN = re.compile(
    r"\b(?:" + "|".join(HONORIFIC_ABBREVIATIONS) + r")(\.?\s+)([A-Za-z][A-Za-z'’-]*)",
    re.IGNORECASE)
PROTECT_TAG = "x"


# A word in vocative position ("WAKE UP, SUNLESS!", "SUNLESS, WAKE UP!") that is
# rare as an English word (Zipf < 3) is a name: ordinary vocatives are frequent
# words ("GUYS" 5.4, "SIR" 5.1, "KID" 5.0); "SUNLESS" (2.3) was rendered "SEM SOL".
_VOCATIVE_AFTER = re.compile(r",\s*([A-Za-z][A-Za-z'’-]{3,})\s*(?=[!?.…\]]|$)")
_VOCATIVE_BEFORE = re.compile(r"^[\W]*([A-Za-z][A-Za-z'’-]{3,})\s*,")
VOCATIVE_NAME_MAX_ZIPF = 3.0


def _vocative_name_spans(text):
    from yomu.review.region_taxonomy import is_english_word, word_zipf

    spans = []
    for pattern in (_VOCATIVE_AFTER, _VOCATIVE_BEFORE):
        for match in pattern.finditer(text):
            word = match.group(1).strip("'’")
            key = word.upper()
            # Only a dictionary word is at risk of being translated ("SUNLESS"); an
            # unknown token ("ARSKAN", OCR damage like "IPROMISE") is left unclaimed.
            if key not in _NOT_A_NAME and is_english_word(key) and word_zipf(word) < VOCATIVE_NAME_MAX_ZIPF:
                spans.append(match.span(1))
    return spans


def honorific_name_spans(text):
    """(start, end) of each name ``text`` addresses: after an honorific abbreviation
    ("MS. GO"), or in vocative position when rare as an English word ("SUNLESS")."""
    text = str(text or "")
    return sorted(set(
        [match.span(2) for match in _PATTERN.finditer(text)
         if match.group(2).strip("'’").upper() not in _NOT_A_NAME]
        + _vocative_name_spans(text)))


def _name_spans(text, names):
    spans = []
    for name in names or ():
        for match in re.finditer(rf"(?<![A-Za-z]){re.escape(name)}(?![A-Za-z])", text, re.IGNORECASE):
            spans.append(match.span())
    return spans


def _merge_spans(spans):
    merged = []
    for start, end in sorted(spans):
        if merged and start < merged[-1][1]:
            merged[-1] = (merged[-1][0], max(merged[-1][1], end))
        else:
            merged.append((start, end))
    return merged


def protect_for_xml(text, names=()):
    """``text`` XML-escaped with each protected name in ``<x>``, or ``None`` if none.

    Protected: names an honorific addresses, plus the chapter's detected names
    (``names``), which DeepL otherwise sometimes renders ("ARISU" -> "ALICE").
    """
    text = str(text or "")
    spans = _merge_spans(honorific_name_spans(text) + _name_spans(text, names))
    if not spans:
        return None
    parts, last = [], 0
    for start, end in spans:
        parts += [html.escape(text[last:start], quote=False),
                  f"<{PROTECT_TAG}>", html.escape(text[start:end], quote=False), f"</{PROTECT_TAG}>"]
        last = end
    parts.append(html.escape(text[last:], quote=False))
    return "".join(parts)


def unprotect_xml(text):
    return html.unescape(re.sub(rf"</?{PROTECT_TAG}>", "", str(text or "")))
