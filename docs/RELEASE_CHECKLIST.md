# Release checklist

> A instalação limpa em Windows foi validada por um beta tester com a `v0.9.1-beta.18` (data não registrada). Essa validação não cobre outros builds,
> assinatura Authenticode ou publicação de um manifesto novo.

## Pré-RC

- [x] Pipeline, quality, provenance, PDF e accounting validados
- [x] Testes herméticos e launcher verdes
- [x] Excluir harness/debug da build de produção
- [x] Alinhar versão, installer e manifests

## RC

- [ ] Canal updater e chave pública *(código: chave `beta-2026-10` em `TRUSTED_PUBLIC_KEYS` e `DEFAULT_MANIFEST_URL` configurada; publicação/validação do manifest no canal pendente)*
- [ ] Code signing Authenticode
- [x] Installer da `v0.9.1-beta.18`
- [x] Licença Beta da `v0.9.1-beta.18`
- [x] Instalação limpa da `v0.9.1-beta.18`
- [ ] E2E funcional completo em Windows limpo *(não inferir a partir do smoke de instalação)*
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
