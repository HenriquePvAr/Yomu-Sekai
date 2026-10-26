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


def honorific_name_spans(text):
    """(start, end) of each name an honorific abbreviation addresses in ``text``."""
    return [match.span(2) for match in _PATTERN.finditer(str(text or ""))
            if match.group(2).strip("'’").upper() not in _NOT_A_NAME]


def protect_for_xml(text):
    """``text`` XML-escaped with each addressed name in ``<x>``, or ``None`` if none."""
    text = str(text or "")
    spans = honorific_name_spans(text)
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
