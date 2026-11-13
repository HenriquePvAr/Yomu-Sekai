# E2E em máquina limpa

> Instalação limpa da versão `v0.9.1-beta.18`: **validada por beta tester, informado pelo dono**;
> data não informada. O relato não foi reproduzido nesta sessão.

O teste final cobre instalação, inicialização, login, entitlement/device, seleção de fonte,
OCR, tradução, quality, PDF, viewer, histórico, atualização e uninstall.

**Status:** instalação reportada como validada para essa versão. O E2E completo descrito acima
(incluindo job real, revisão, atualização e desinstalação) não foi afirmado pelo dono e permanece
um gate separado. Existem specs de build (`packaging/komyst.spec`) e o builder
`tools/build_installer.py`; esta documentação não registra uma execução local desses scripts.
