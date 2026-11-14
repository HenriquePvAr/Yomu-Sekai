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
| `comicneue-regular.ttf`, `comicneue-bold.ttf`, `comicneue-italic.ttf`, `comicneue-bolditalic.ttf` | Comic Neue | SIL OFL 1.1 — `OFL-ComicNeue.txt` |
| `kalam-regular.ttf`, `kalam-bold.ttf` | Kalam (Indian Type Foundry) | SIL OFL 1.1 — `OFL-Kalam.txt` |
| `patrickhand-regular.ttf` | Patrick Hand (Patrick Wagesreiter) | SIL OFL 1.1 — `OFL-PatrickHand.txt` |
| `luckiestguy-regular.ttf` | Luckiest Guy (Astigmatic) | Apache 2.0 — `Apache-2.0-LuckiestGuy.txt` |

Source: https://github.com/google/fonts (`ofl/comicrelief`, `ofl/bangers`), downloaded 2026-10-24.
Used by `komyst.clean.ownership.font_fidelity` (`BUNDLED_FONTS_DIR`); a bundled
file wins over a Windows font of the same role.

## Avaliação de 2026-11-03

Foram avaliadas fontes OFL adicionais (Comic Neue, Patrick Hand, Bubblegum Sans, Londrina Solid,
Short Stack, Itim, Pangolin, Sniglet, Kalam) contra o letreiramento de um capítulo de referência, com a
mesma altura de letra e o estimador de peso do próprio app (`extract_glyph_style_profile`). A Comic Relief
Bold atual ficou entre as mais próximas em peso (0,1019 contra 0,1107 do original), então **nenhuma fonte
nova foi adicionada**. Os arquivos baixados para a comparação não fazem parte do repositório.

## Atualização de 2026-11-14

A fonte agora é escolhida por região, redesenhando as palavras do original em cada fonte das cadeias de papel e
comparando forma, largura e traço (`FONT_RASTER_MATCH`). Com esse critério, Comic Neue, Kalam, Patrick Hand e
Luckiest Guy (`ofl/` e `apache/` do repositório google/fonts, baixadas em 2026-11-14) passaram a fazer parte do
acervo: em balões de um capítulo de referência, Kalam Bold e Comic Neue Bold ficaram entre as mais próximas do
original. Elas só substituem a fonte do papel quando vencem com folga.
