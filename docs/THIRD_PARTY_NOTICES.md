# Third-party notices

> **Revisado em:** 2026-10-24 · **Base verificada:** `5f482ce1` · Documento vivo.

Este documento acompanha a revisão de licenças. O aviso que viaja com o artefato distribuído é
[`THIRD_PARTY_NOTICES.txt`](../THIRD_PARTY_NOTICES.txt) na raiz (Scrapling, psd-tools, Pillow,
Playwright, Patchright, BrowserForge, curl_cffi, msgspec, protego, scipy, scikit-image, aggdraw,
english-words, entre outros). A tabela abaixo lista o que ainda depende de revisão.

| Componente | Uso | Situação |
|---|---|---|
| RapidOCR / ONNX Runtime (DirectML no Windows: `onnxruntime-directml`, MIT; `DirectML.dll` sob a licença da Microsoft que acompanha o pacote) | OCR local e LaMa na GPU | `LICENSE_REVIEW_REQUIRED` |
| OpenCV / Pillow | imagem e reconstrução | `LICENSE_REVIEW_REQUIRED` (Pillow listado em `THIRD_PARTY_NOTICES.txt`) |
| PyInstaller | empacotamento | `LICENSE_REVIEW_REQUIRED` |
| NiceGUI / WebView2 | UI | `LICENSE_REVIEW_REQUIRED` |
| NVIDIA OCR / DeepL | providers externos | termos pendentes |
| Anime-Manga Big-LaMa (checkpoint TorchScript) | preenchimento aprendido da limpeza local, ligado por padrão (`CLEAN_LEARNED_TEXTURE_FILL`, `ADVANCED_ART_INPAINTING`) | **NOT CLEARED** — direitos de redistribuição do checkpoint não resolvidos; não empacotado (lido de `ADVANCED_ART_INPAINT_MODEL_PATH`). Ver [matriz de licenças de modelos](research/colab-clean-models/MODEL_LICENSE_MATRIX.md) |
| english-words (dwyl) | léxico `assets/lexicon/english_words.txt.gz`, empacotado | Unlicense — listado em `THIRD_PARTY_NOTICES.txt` e `assets/lexicon/LICENSE-english-words.md` |
| wordfreq (Robyn Speer), dados de frequência | tabelas `assets/lexicon/english_freq.tsv.gz` e `portuguese_freq.tsv.gz`, empacotadas (derivadas) | CC BY-SA 4.0 — a tabela derivada segue a mesma licença; ver `assets/lexicon/README.md` |
| Comic Relief, Bangers | fontes de letreiro `assets/fonts/`, empacotadas | SIL OFL 1.1 — `assets/fonts/OFL-*.txt`, listadas em `THIRD_PARTY_NOTICES.txt` |
| Glossário de SFX | `assets/lexicon/sfx_en_pt.json`, empacotado com `assets/lexicon/` | origem não registrada em `assets/lexicon/README.md` — confirmar autoria/licença |
| Fontes / ícones / outros modelos | assets | origem/licença pendentes |
