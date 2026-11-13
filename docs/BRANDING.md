# Marca do Komyst

O nome mostrado no aplicativo é **Komyst**. A logo principal usa a imagem K
fornecida pelo usuário: `assets/branding/komyst-logo.png`. A versão usada
pela interface fica em `static/assets/auth/komyst-logo.png`, e o ícone do
aplicativo/navegador é `assets/branding/generated/komyst.ico`.

As telas, mensagens visíveis, traduções, título da janela, versão exibida,
instalador, guia do usuário e documentação passaram a usar Komyst.

A renomeação interna completa (pacote Python `komyst/`, variáveis de ambiente
`KOMYST_*`, cabeçalhos internos `X-Komyst-*`, `APP_ID`, namespace UUID, pasta
de dados `%LOCALAPPDATA%\Komyst`, executável `Komyst.exe` e instalador
`packaging/Komyst.iss`) foi autorizada e aplicada em 2026-11-12 porque não
existe nenhuma instalação distribuída (beta testers ou produção) para migrar.
Não há código de migração porque não há dado antigo para migrar.

Exceções deliberadas, mantidas como estão por serem referências externas reais
e não nomes de exibição do produto:

- `komyst/runtime/update_bootstrap.DEFAULT_MANIFEST_URL` continua apontando
  para `github.com/HenriquePvAr/YomuSekai-Releases` — repositório de releases
  separado; não renomear sem ordem explícita do dono (ver plano Fase 6, F6.3).
- `komyst/security/ad_url_policy.CANONICAL_AD_HOST` continua
  `yomusekai.com.br` — domínio externo real usado pela CSP/allowlist de
  anúncios; renomear exigiria registrar/apontar um domínio novo, o que este
  repositório não pode decidir sozinho.
- `start_tradutor.py` e `start_tradutor.bat` (e o módulo interno
  `komyst/commands/start_tradutor.py` que eles chamam) mantêm o nome do
  arquivo: são os entry points documentados no `CLAUDE.md` e no guia de
  desenvolvimento; renomear o arquivo exigiria atualizar todo atalho/documento
  que já aponta para ele sem nenhum ganho de comportamento.
- Conteúdo histórico (`docs/archive/`, `docs/research/`, `docs/consolidation/`,
  `docs/status/`, `reports/` e os relatórios/planos já datados) preserva o
  nome usado na época, por ser registro do que existia então.
