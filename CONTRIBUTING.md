# Contribuindo

> **Base verificada:** `5f482ce1` (branch `main`) · **Revisado em:** 2026-10-24

## Organização

- Código de runtime Python novo vai para o pacote canônico `yomu/`; a raiz mantém apenas shims/entrypoints de compatibilidade (verificados por `python tools/repository/check_root_policy.py`). As demais áreas ativas são `apps/`, `ui/`, `static/`, `supabase/` e `packaging/`.
- Testes automatizados ficam em `tests/`; experimentos isolados ficam em `experiments/` ou `research/`, nunca no runtime de produção.
- Scripts operacionais ficam em `scripts/`; harnesses e ferramentas de desenvolvimento ficam em `tools/`.
- Relatórios pequenos e canônicos podem ser versionados em `reports/`. Outputs volumosos seguem [a política de artefatos](docs/ARTIFACT_POLICY.md).

## Verificações

Use Python 3.11 e o perfil de dependências indicado em [Desenvolvimento](docs/DEVELOPMENT.md) (`requirements/requirements-beta.txt` + `requirements/requirements-dev.txt`). Para a suíte offline padrão (~6160 testes, ~10 min):

```powershell
python -m pytest -q
```

As suítes frontend podem ser executadas individualmente com:

```powershell
node --experimental-vm-modules tests/test_chapter_reader.mjs
```

Não execute smokes de rede ou providers pagos sem opt-in explícito e escopo autorizado.

## Git e segurança

- Nunca versione `.env`, tokens, chaves privadas, credenciais, caches, virtualenvs ou dados de usuário.
- Mantenha produção e pesquisa separadas; não transforme resultados experimentais em afirmações de produto sem validação.
- Prefira commits pequenos com escopo descritivo. Não faça push, release ou deploy sem solicitação explícita.
- Antes de concluir, confira `git diff --check`, os testes relevantes e `git status`.
