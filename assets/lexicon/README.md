# English lexicon

`english_words.txt.gz` — upper-case English words of 3–20 letters, one per line,
filtered from `words_alpha.txt` of https://github.com/dwyl/english-words
(Unlicense / public domain, see `LICENSE-english-words.md`). Downloaded 2026-10-23.

Used by `yomu.review.region_taxonomy.is_english_word` to tell a written word
("INCREDIBLE...") from an onomatopoeia ("PAEHYEOK...") without a hand-made list.

`english_freq.tsv.gz` — `WORD<TAB>zipf` for ~114,000 English words (apostrophes
removed), exported from the `wordfreq` 3.1.1 `best` English list
(https://github.com/rspeer/wordfreq). The data is CC BY-SA 4.0 (attribution:
Robyn Speer, wordfreq); this derived table is distributed under the same licence.
Used by `yomu.review.region_taxonomy.segment_words` to split words the OCR glued
together ("WEPLANTO" -> WE PLAN TO) by word frequency.

`portuguese_freq.tsv.gz` — `WORD<TAB>zipf` for ~148,000 Portuguese forms, exported the same
way from the `wordfreq` 3.1.1 `best` Portuguese list (CC BY-SA 4.0, same attribution and
licence). Used by `yomu.translation.portuguese_words` to find a word a translation carries
that Portuguese does not have ("ESTOVA").
