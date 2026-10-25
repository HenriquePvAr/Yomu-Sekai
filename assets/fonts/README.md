# Bundled fonts

Comic-lettering faces shipped with the app, so a translation can follow the
source lettering on any machine. Chosen by rendering candidates against real
webtoon lettering (Comic Neue, Patrick Hand, Kalam, Bubblegum Sans and others
were compared): Comic Relief Bold was closest for dialogue; Bangers is used
only for shouts and sound effects.

| File | Family | License |
| --- | --- | --- |
| `comicrelief-regular.ttf`, `comicrelief-bold.ttf` | Comic Relief (Jeff Davis; Comic Sans metrics) | SIL OFL 1.1 — `OFL-ComicRelief.txt` |
| `bangers-regular.ttf` | Bangers (Vernon Adams) | SIL OFL 1.1 — `OFL-Bangers.txt` |

Source: https://github.com/google/fonts (`ofl/comicrelief`, `ofl/bangers`), downloaded 2026-10-24.
Used by `yomu.clean.ownership.font_fidelity` (`BUNDLED_FONTS_DIR`); a bundled
file wins over a Windows font of the same role.
