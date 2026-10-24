# Mapa de dependências da raiz

> **Base verificada:** `5f482ce1` (branch `main`) · **Revisado em:** 2026-10-24
>
> **Atualização 2026-10-24:** os ponteiros `PRODUCTION_SECRETS_REQUIRED.md` e
> `SEMANTIC_CLASSIFICATION_AUDIT.md` foram removidos da raiz (conteúdo canônico em
> `docs/operations/` e `docs/architecture/`), e os perfis `requirements-*.txt` foram movidos
> para `requirements/` (a base `requirements.txt` continua na raiz). As tabelas de shims e de
> bootstrap/manifests já usam os caminhos atuais (CI em `.github/workflows/tests.yml` instala
> `requirements/requirements-beta.txt` e `requirements/requirements-dev.txt`). A tabela de
> movimentações de documentação e o "Critério de movimentação" são registro histórico da
> auditoria; a estrutura vigente está em [REPOSITORY_STRUCTURE.md](REPOSITORY_STRUCTURE.md).

**Escopo:** caminhos diretamente na raiz do checkout `main`, incluindo imports, execução,
configuração, CI, packaging, testes e links de documentação. A fonte primária de shims é
`config/repository_root_allowlist.json`; referências foram buscadas no checkout com Basinfy e
`rg` para literais de caminho. Consumidores fora do repositório não são totalmente observáveis,
por isso nomes de CLI/documentos antigos permanecem como stubs/entrypoints.

## Movimentações de documentação e links atualizados

| Origem | Destino canônico | Consumidores encontrados e alterados | Validação / risco residual |
|---|---|---|---|
| `docs/PROJECT_STRUCTURE.md` | `docs/architecture/REPOSITORY_STRUCTURE.md` | `README.md`, `docs/README.md`, `docs/DEVELOPMENT_WORKFLOW.md`, `docs/status/board/board.js`; destino também aponta para os novos mapas | Stubs permanecem no path antigo. Risco externo de URL mitigado; nenhum import/runtime |
| `SEMANTIC_CLASSIFICATION_AUDIT.md` | `docs/architecture/SEMANTIC_CLASSIFICATION_AUDIT.md` | `docs/README.md` (índice técnico e auditorias históricas), `docs/technical/DOCUMENTACAO_TECNICA.md`, `docs/DOCUMENTATION_AUDIT.md` | Stub de raiz preserva URL; documento não contém links Markdown relativos que dependam da raiz |
| `PRODUCTION_SECRETS_REQUIRED.md` | `docs/operations/PRODUCTION_SECRETS_REQUIRED.md` | `docs/README.md` agora lista o contrato de operações; não havia link interno literal antes da movimentação | Stub de raiz preserva URL; conteúdo mantém nomes de segredos, sem valores |

Nenhum entrypoint, configuração de runtime, dependency manifest ou caminho de packaging foi
movido. Atualização de nomes de referência não mudou comportamento.

## Mapa dos shims Python

| Raiz (shim) | Implementação | Consumidores comprovados | Restrições |
|---|---|---|---|
| `app_ui.py` | `yomu.ui.app` | README/docs, UI tests, runtime forensics, CI compileall, UI subprocess | Preservar `sys.modules[__name__]` para identidade e monkeypatch/import compatibility |
| `desktop_app.py` | `yomu.desktop.app` | `packaging/tradutor_ia.spec`, `packaging/tradutor_jwks_diagnostic.spec`, CI compileall e desktop tests | PyInstaller verifica/especifica caminho root; não mover sem novo spec e frozen smoke |
| `down.py` | `yomu.download.down` | Imports e testes de compatibilidade do downloader | Mesmo objeto de módulo reexportado; consumidores externos desconhecidos |
| `main.py` | `yomu.commands.legacy_gui` | CLI legado e import compatibility | Preservar nome de comando legado |
| `run_local_folder.py` | `yomu.commands.run_local_folder` | UI/job commands, worker e local-folder tests | Caminho pode ser persistido em comandos de jobs |
| `run_webtoon.py` | `yomu.commands.run_webtoon` | CLI, worker subprocess, docs, compileall e testes | API pública de fato; manter caminho estável |
| `start_tradutor.py` | `yomu.commands.start_tradutor` | `start_tradutor.bat`, docs, launcher/updater/process tests | Usuários chamam comandos `all`, `worker`, `ui`, `status`, `stop` pelo path |
| `worker_service.py` | `yomu.runtime.worker_service` | Worker subprocess, supervisor/recovery/shutdown tests, compileall e process fingerprints | Nome é contrato de processo e substring de supervisão |

Os oito shims estão listados no allowlist raiz e todos são `KEEP_ROOT_COMPATIBILITY`.
Não trocar por wrappers diferentes sem cobrir identidade de módulo, monkeypatch, argv,
subprocessos, cwd e PyInstaller.

## Bootstrap de testes e manifests

| Entrada raiz | Consumidores/encadeamento | Consequência de mover |
|---|---|---|
| `pytest.ini` | pytest → `tests/`, `experiments/`; `norecursedirs`, markers e modo offline | Muda coleta/markers/exclusões |
| `conftest.py` | pytest carrega guard runtime hermético e guard de rede, antes de testes | Pode remover defesa global/inverter ordem de import |
| `sitecustomize.py` | Python startup em testes/filhos guardados → `test_support` | Pode impedir bloqueio precoce de rede e isolamento de dados |
| `requirements.txt` | base; incluído por Beta; CI/docs/Docker/deploy | `-r` e comandos existentes usam caminhos raiz |
| `requirements/requirements-beta.txt` | CI, pip profile, runtime checks, packaging preflight | Perfil deliberadamente compõe manifests e é referenciado literalmente |
| `requirements/requirements-dev.txt` | CI e instruções pytest; não empacotado | Nome usado pelos comandos de instalação de dev |
| `requirements/requirements-rapidocr.txt` | Include Beta, CI e docs | Include relativo e perfil do OCR primário |
| `requirements/requirements-ui.txt` | README/docs e verificação do pin NiceGUI | Manter o pin espelhado e verificado |
| `requirements/requirements-optional.txt` | docs e dependências lazy opcionais | Não misturar com o perfil base sem revisar extras |
| `requirements/requirements-paddle.txt` | documentação/ambiente isolado legacy | Conflita com contrato OpenCV; não incluir em Beta |
| `requirements/requirements-gemini-vps.txt` | contrato operacional remoto; literal não encontrado no checkout | Dependência externa não inspecionável; manter path até verificar o deploy consumer |

## Configuração, distribuição e documentação

- `.env.example` é template para o operador; `README.md`, `docs/CONFIGURATION.md`, instalação e
  teste de ambiente apontam para esse nome. O próprio exemplo não é carregado pela aplicação.
- `start_tradutor.bat` chama `%HERE%start_tradutor.py`; `README.md`, `CLAUDE.md` e docs de fila
  documentam a entrada. `test_support/hermetic_runtime.py` reconhece esse entrypoint para não
  iniciar processos de usuário durante teste.
- `packaging/tradutor_ia.spec` inclui `desktop_app.py` do root; o spec diagnóstico também
  valida esse caminho. `.github/workflows/tests.yml` chama `compileall` sobre shims e hooks.
- `AGENTS.md`/`CLAUDE.md` são descobertos pelas ferramentas; `README.md`, `CHANGELOG.md`,
  `CONTRIBUTING.md` e `THIRD_PARTY_NOTICES.txt` possuem convenções externas usuais.
- `PRODUCTION_SECRETS_REQUIRED.md` e `SEMANTIC_CLASSIFICATION_AUDIT.md` não existem mais na
  raiz (ponteiros removidos em 2026-10-24); o conteúdo canônico está em `docs/operations/` e
  `docs/architecture/`, e os links do índice e da documentação técnica apontam para lá.
- `config/repository_root_allowlist.json` e `tools/repository/check_root_policy.py` definem e
  testam a política de raiz Python; `tests/test_repository_root_policy.py` lê essa configuração.

## Critério de movimentação

Movidos três corpos documentais para pastas já existentes. Nos três casos foram atualizados
links internos e deixados stubs nos caminhos antigos, pois bookmarks/consumidores externos não
podem ser inventariados. Nenhum arquivo Python, manifest, startup hook, recurso local, diretório
grande ou arquivo de usuário foi movido. Para reduzir mais a raiz seria necessário provar
compatibilidade externa para entrypoints e manifests; até essa prova, a decisão correta é
preservá-los.
