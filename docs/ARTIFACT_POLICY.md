# Política de artefatos

> **Revisado em:** 2026-10-24 · **Base verificada:** `5f482ce1` · Documento vivo.

## Versionar

- Código, testes, configuração sanitizada e documentação necessária para reproduzir o software.
- Relatórios pequenos, canônicos, sem dados pessoais ou segredos e importantes para a rastreabilidade.
- Fixtures sintéticas mínimas e manifests com hashes, propósito e proveniência.
- Dados pequenos de runtime que o produto carrega, como `assets/lexicon/` (léxico inglês e glossário de SFX, com licença registrada em `assets/lexicon/LICENSE-english-words.md`).

## Manter fora do Git

- `.env` real, tokens, OAuth/Kaggle/Modal/OCI credentials, cookies, chaves privadas e certificados.
- Páginas de terceiros ou de usuários, datasets completos, crops de revisão, máscaras massivas e outputs de inferência.
- Pesos de modelos, PDFs/PSDs gerados em massa, caches OCR, logs de execução, `build/`, `dist/`, virtualenvs e `node_modules/`. Exemplo: o checkpoint LaMa usado pela limpeza local é procurado por padrão em `%LOCALAPPDATA%\TradutorIA\models\` (`ADVANCED_ART_INPAINT_MODEL_PATH` em `yomu/config/settings.py`) e nunca é versionado (`.gitignore` cobre `models/` e `*.pt`).

Armazene esses arquivos em uma área de artefatos local ou remota com acesso apropriado — por exemplo, sob `<pasta-de-experimentos>\YomuExperimental\` na máquina DEV ou `~/yomu/experimental/` em worker R&D. Esses exemplos não são paths de runtime e nunca devem ser hardcoded no produto.

Para artefatos externos necessários a uma conclusão, mantenha um manifesto pequeno com caminho lógico, tamanho, SHA-256, finalidade e identidade do experimento; não copie o conteúdo para `reports/`.

## Higiene

Antes de staging, inspecione os arquivos com `git status --short`, confira tamanhos e faça busca local por segredos. O `.gitignore` protege virtualenvs, caches, logs e outputs usuais; ele não substitui a revisão do conteúdo staged.
