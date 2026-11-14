# E2E em máquina limpa

> A instalação limpa em Windows foi validada por um beta tester com a `v0.9.1-beta.18` (data não registrada).

O teste final cobre instalação, inicialização, login, entitlement/device, seleção de fonte,
OCR, tradução, quality, PDF, viewer, histórico, atualização e uninstall.

**Status:** instalação reportada como validada para essa versão. O E2E completo descrito acima
(incluindo job real, revisão, atualização e desinstalação) não foi registrado como validado e permanece
um gate separado. Existem specs de build (`packaging/komyst.spec`) e o builder
`tools/build_installer.py`; não há registro de execução local desses scripts neste documento.
