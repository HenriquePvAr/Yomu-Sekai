# E2E em máquina limpa

> **Revisado em:** 2026-10-24 · **Base verificada:** `5f482ce1` · Documento vivo.

O teste final cobre instalação, inicialização, login, entitlement/device, seleção de fonte,
OCR, tradução, quality, PDF, viewer, histórico, atualização e uninstall.

**Status:** `E2E_PENDING` — nenhuma evidência de execução em VM Windows limpa no repositório
(dívida `CLEAN-VM-VALIDATION-PENDING` na
[Documentação Técnica §29](technical/DOCUMENTACAO_TECNICA.md#29-snapshot-histórico-de-dívida-técnica-não-revalidado-na-m18)).
Existem specs de build (`packaging/tradutor_ia.spec`) e o builder `tools/build_installer.py`,
mas build ou smoke frozen em máquina de desenvolvimento não substitui este teste. É também a
condição 2 para sair do [Quality Freeze](QUALITY_FREEZE.md#como-sair-do-freeze).
