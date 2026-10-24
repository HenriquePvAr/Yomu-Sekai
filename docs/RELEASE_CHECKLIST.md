# Release checklist

> **Revisado em:** 2026-10-24 (base `5f482ce1`, branch `main`) — apenas as notas entre parênteses
> foram reconferidas no código; as caixas continuam históricas.

> Este checklist contém caixas e estados herdados de uma avaliação anterior à Beta 17. Eles
> não são um retrato atual nem foram revalidados pela M18. Use-o como roteiro para uma futura
> execução do gate; confirme cada item de novo antes de tratar qualquer marcação/pendência como
> válida. A M18 não executou auditoria de release.

## Pré-RC

- [x] Pipeline, quality, provenance, PDF e accounting validados
- [x] Testes herméticos e launcher verdes
- [x] Excluir harness/debug da build de produção
- [x] Alinhar versão, installer e manifests

## RC

- [ ] Canal updater e chave pública *(código: chave `beta-2026-10` em `TRUSTED_PUBLIC_KEYS` e `DEFAULT_MANIFEST_URL` configurada; publicação/validação do manifest no canal pendente)*
- [ ] Code signing Authenticode
- [ ] Installer final *(script `packaging/TradutorIA.iss` + `tools/build_installer.py` existem; build final não validada)*
- [ ] Licensing/device operacional
- [ ] Clean-VM E2E
- [ ] Secret/privacy scan final

## Closed beta

- [ ] Distribuição controlada
- [ ] Testers, licenças e limites
- [ ] Canal de bugs e suporte
- [ ] Política de `review_required`

## Pós-beta

- [ ] Cloudflare/Edge hardening, se necessário (decisão: não obrigatório para a primeira beta)
- [ ] Otimização de grouping/classification
- [ ] Investigação histórica se os inputs forem recuperados
