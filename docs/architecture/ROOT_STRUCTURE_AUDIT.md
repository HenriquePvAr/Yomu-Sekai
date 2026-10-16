# Auditoria da estrutura direta da raiz

**Snapshot:** 2026-10-16, checkout canônico da `main` consolidada (worktree Windows).
**Git:** `main` local inicia em `c6bc48d97ba28fba89b027aea0ac5b5b87baedcd`; `origin/main` permanece
`ec9ca9e4acd0849020eb13a089817c1c11aeab7a`. Havia 31 arquivos e 19 diretórios rastreados
diretamente na raiz. A enumeração física tinha 33 arquivos no total, incluindo o ponteiro `.git` e
o `.mcp.json` local, e 27 diretórios (19 rastreados mais oito caches/contextos ignorados ou locais).
Nenhum processo com linha de comando apontando para o checkout canônico foi encontrado.

**Decisão geral:** manter na raiz os contratos convencionais, manifests, hooks, launchers e
shims. Mover apenas o conteúdo de três documentos para categorias já existentes e conservar
stubs nos caminhos antigos. Assim os 31 caminhos rastreados da raiz continuam presentes, mas
nenhuma implementação/runtime foi deslocada e a documentação canônica fica organizada.

## Arquivos diretamente na raiz

Cada linha consolida categoria/finalidade, consumidores/importadores, referências de script,
build e teste, contrato, localização, decisão, justificativa e risco.

| PATH | CATEGORY / PURPOSE | USED_BY / IMPORTERS | SCRIPT / BUILD / TEST REFERENCES | COMPATIBILITY CONTRACT | RECOMMENDED LOCATION | DECISION / RATIONALE / RISK |
|---|---|---|---|---|---|---|
| `.env.example` | Template público de configuração, somente placeholders | Operador; documentação de configuração; não é carregado como `.env` pela aplicação | README, `docs/CONFIGURATION.md`, instalação, testes de ambiente | Nome e caminho de cópia documentados | Raiz | `KEEP_ROOT_REQUIRED`; evita quebrar onboarding e referências; nunca preencher com segredos |
| `.gitattributes` | Regras Git de atributos/EOL | Git | Aplicado automaticamente em operações Git | Convenção Git da raiz | Raiz | `KEEP_ROOT_REQUIRED`; mover altera descoberta/aplicação de atributos |
| `.gitignore` | Política de exclusão local | Git e scripts de ambiente | Regras de runtime, caches e outputs | Convenção Git da raiz | Raiz | `KEEP_ROOT_REQUIRED`; não ampliar padrões sem auditar arquivos já rastreados |
| `AGENTS.md` | Instruções para agentes | Agentes de código e ferramentas compatíveis | Descoberto por convenção no checkout | Nome e posição convencionais | Raiz | `KEEP_ROOT_REQUIRED`; mover pode retirar instruções do escopo |
| `CHANGELOG.md` | Histórico de mudanças do produto | Mantenedores e leitores de release | Convenção GitHub/ecossistema | Nome convencional | Raiz | `KEEP_ROOT_REQUIRED`; nenhuma dependência que justifique mover |
| `CLAUDE.md` | Instruções Claude/Codex e contratos de contribuição | Agentes que leem instruções de raiz | Referências a launchers e invariantes de desenvolvimento | Nome e posição convencionais | Raiz | `KEEP_ROOT_REQUIRED`; comportamento de agentes depende da descoberta na raiz |
| `CONTRIBUTING.md` | Guia de contribuição | Pessoas e automações de contribuição | Convenção GitHub | Nome convencional | Raiz | `KEEP_ROOT_REQUIRED`; preservar entrada pública padrão |
| `PRODUCTION_SECRETS_REQUIRED.md` | Ponteiro para contrato de segredos de produção | Bookmarks/consumidores externos não observáveis | Link canônico no índice de docs | URL histórica na raiz preservada | Conteúdo em `docs/operations/PRODUCTION_SECRETS_REQUIRED.md`; stub na raiz | `MOVE_WITH_REFERENCE_UPDATES`; o documento completo é operacional; stub mantém compatibilidade. Nenhum valor secreto foi copiado |
| `README.md` | Página inicial e comandos básicos | Pessoas, GitHub e contribuidores | Liga instalação, CLI e estrutura | Página inicial convencional | Raiz | `KEEP_ROOT_REQUIRED`; links internos atualizados para o mapa canônico |
| `SEMANTIC_CLASSIFICATION_AUDIT.md` | Ponteiro para auditoria semântica histórica/técnica | Bookmarks/consumidores externos não observáveis | Links do índice e documentação técnica atualizados | URL histórica da raiz preservada | Conteúdo em `docs/architecture/SEMANTIC_CLASSIFICATION_AUDIT.md`; stub na raiz | `MOVE_WITH_REFERENCE_UPDATES`; auditoria técnica pertence à arquitetura; risco externo mitigado pelo stub |
| `THIRD_PARTY_NOTICES.txt` | Avisos/licenças de terceiros | Distribuição e revisão legal | Empacotamento/distribuição consultam avisos | Nome esperado por consumidores de pacote | Raiz | `KEEP_ROOT_REQUIRED`; mover pode omitir notices em distribuição |
| `app_ui.py` | Shim para UI `yomu.ui.app` | CLI histórico, subprocessos, testes e automações | `tests`, runtime forensics e compilação CI | O shim preserva `sys.modules`/identidade e `python app_ui.py` | Raiz | `KEEP_ROOT_COMPATIBILITY`; mover quebra caminhos documentados e monkeypatch/importers |
| `conftest.py` | Bootstrap pytest de rede offline e runtime isolado | Pytest em todo o repositório | Carregado automaticamente antes dos testes | Descoberta pytest por nome/raiz | Raiz | `KEEP_ROOT_REQUIRED`; mover enfraquece proteção de teste ou muda descoberta |
| `desktop_app.py` | Shim de desktop `yomu.desktop.app` | PyInstaller, desktop legado, testes | `packaging/tradutor_ia.spec`, spec diagnóstico, CI compileall | Caminho esperado pelo spec e import compatibility | Raiz | `KEEP_ROOT_COMPATIBILITY`; risco alto de build se movido |
| `down.py` | Shim do downloader histórico | Imports antigos e chamadas CLI | Testes de compatibilidade/download | Módulo histórico reexporta implementação preservando identidade | Raiz | `KEEP_ROOT_COMPATIBILITY`; não substituir por reexport simples nem mover sem prova de callers externos |
| `main.py` | Shim de GUI legado | CLI/imports históricos | Entrada histórica de aplicativo | `python main.py` / import path | Raiz | `KEEP_ROOT_COMPATIBILITY`; implementador está em `yomu.commands.legacy_gui` |
| `pytest.ini` | Config de coleta, markers, exclusões e modo offline | Pytest | `python -m pytest`; CI | Descoberto por pytest a partir da raiz | Raiz | `KEEP_ROOT_REQUIRED`; caminho determina coleta e isolamento |
| `requirements-beta.txt` | Perfil runtime Beta que compõe base/OCR e extras empacotados | Instalação limpa e validação de runtime | CI, docs de instalação, checks de perfil, pip includes relativos | Nome consumido por CI/docs e includes relativos | Raiz | `KEEP_ROOT_REQUIRED`; mover exige reescrever consumidores e validar resolução pip |
| `requirements-dev.txt` | Dependências de teste, não runtime distribuído | Pytest e testes ASGI | CI e docs de teste/instalação | Nome e caminho diretamente invocados | Raiz | `KEEP_ROOT_REQUIRED`; separado do runtime por contrato |
| `requirements-gemini-vps.txt` | Dependências do serviço remoto Gemini/VPS | Deploy/worker remoto | Procuras locais não encontraram referência literal no checkout; provável consumo externo precisa de verificação no deploy | Caminho de instalação operacional não pode ser inspecionado integralmente daqui | Raiz | `DEFER_HIGH_RISK`; conservar até confirmar scripts/imagem/host de deploy, não presumir órfão |
| `requirements-optional.txt` | Dependências opcionais de transporte/PSD | Instalações seletivas e módulos lazy | Docs de desenvolvimento/instalação e guias de runtime | Nome referenciado por documentação | Raiz | `KEEP_ROOT_REQUIRED`; perfil separado por design |
| `requirements-paddle.txt` | OCR Paddle legacy opcional, isolado por conflito OpenCV | Ambiente de pesquisa/compatibilidade | Docs e validação de perfil | Nome de instalação documentado | Raiz | `KEEP_ROOT_REQUIRED`; risco alto de conflitar distribuição OpenCV se agregado |
| `requirements-rapidocr.txt` | OCR primário RapidOCR/ONNX | Runtime Beta | CI, runtime profile, instalação, README e testes | Include relativo de requirements-beta e caminho documentado | Raiz | `KEEP_ROOT_REQUIRED`; mover altera cadeia de inclusão e CI |
| `requirements-ui.txt` | Pin de NiceGUI espelhado | Instalação/UI | README, docs e verificadores de dependência | Nome documentado e pin alinhado ao base | Raiz | `KEEP_ROOT_REQUIRED`; monitorado por testes de conflito de pin |
| `requirements.txt` | Dependências base de produto/imagem/UI | Runtime Python | Beta compõe com `-r`; CI, Docker/deploy, docs e scripts | Manifest padrão de pip e include relativo | Raiz | `KEEP_ROOT_REQUIRED`; movimentação de alto risco e sem benefício funcional |
| `run_local_folder.py` | Shim de entrada local-folder | Worker, CLI e testes | Comandos persistidos e testes subprocess | Caminho serializado/documentado | Raiz | `KEEP_ROOT_COMPATIBILITY`; mover quebra execução de comandos persistidos |
| `run_webtoon.py` | Shim de CLI principal | Operador, worker e testes | CLI, subprocessos, CI compileall, docs | `python run_webtoon.py` é API pública de fato | Raiz | `KEEP_ROOT_COMPATIBILITY`; implementador em `yomu.commands.run_webtoon` |
| `sitecustomize.py` | Hook Python precoce dos guards de teste para filhos | Python children iniciados em ambiente de teste | Propaga guard/runtime isolation | Descoberto automaticamente no startup quando raiz está em `sys.path`/`PYTHONPATH` | Raiz | `KEEP_ROOT_REQUIRED`; mover pode remover proteção antes de importar código |
| `start_tradutor.bat` | Launcher Windows | Usuário Windows e testes de launcher | Invoca o Python local ou fallback e `start_tradutor.py` | Nome/caminho do atalho documentado | Raiz | `KEEP_ROOT_REQUIRED`; manter entrada operacional simples |
| `start_tradutor.py` | Shim de launcher/supervisor | Usuário, worker, updater e testes | `start_tradutor.bat`, docs e testes de processo | `python start_tradutor.py ...` é entrada documentada | Raiz | `KEEP_ROOT_COMPATIBILITY`; comandos e automações o chamam diretamente |
| `worker_service.py` | Shim do worker persistente | Worker subprocess e testes de supervisão | CI compileall, testes de worker/processo | `worker_service.py` aparece em comandos e fingerprints | Raiz | `KEEP_ROOT_COMPATIBILITY`; implementador em `yomu.runtime.worker_service` |
| `.git` (worktree pointer) | Ponteiro administrativo Git do worktree | Git | Operações Git | Arquivo administrativo obrigatório nesta forma de worktree | Raiz | `KEEP_ROOT_REQUIRED` (administrativo); não editar manualmente |
| `.mcp.json` (local, untracked) | Configuração contextual local de MCP | Ferramenta local do owner | Nenhum consumidor do produto | Configuração fora de controle de versão | Raiz local | `GENERATED_LOCAL_IGNORE`; preservada e fora do staging. Conteúdo não foi lido nem copiado |

## Diretórios diretamente na raiz

Os 19 diretórios versionados permanecem em seus caminhos; nenhum foi movido.

| Diretório | Responsabilidade | Decisão |
|---|---|---|
| `.github/` | Workflows e automação de CI | Manter |
| `apps/` | Serviços de aplicação e suporte | Manter |
| `assets/` | Assets aprovados do aplicativo | Manter |
| `config/` | Configuração versionada e políticas de ferramenta | Manter |
| `deploy/` | Recursos de deploy/serviços | Manter |
| `docs/` | Documentação canônica e histórica | Manter; usar categorias existentes |
| `experiments/` | Testes/experimentos isolados | Manter fora do runtime |
| `packaging/` | Specs e definição de pacote | Manter |
| `reports/` | Evidência selecionada e sanitizada | Manter; não despejar artifacts temporários |
| `research/` | Provas de conceito e pesquisa | Manter separada da implementação |
| `scripts/` | Scripts de suporte operacional/build | Manter |
| `static/` | Assets servidos pelo runtime UI | Manter |
| `supabase/` | Configuração, migrações e Edge Functions versionadas | Manter |
| `test_fixtures/` | Dados/fixtures de teste | Manter |
| `test_support/` | Helpers e guards herméticos | Manter |
| `tests/` | Suítes Python/Node/contrato | Manter |
| `tools/` | Auditoria, validação e tooling | Manter |
| `ui/` | Código de UI separado do pacote Python | Manter |
| `yomu/` | Implementação canônica do produto Python | Manter; novos módulos de runtime aqui |

## Estado local e alterações

Os diretórios locais `.agents/`, `.basinfy/`, `.codex/`, `.pytest_cache/`, `__pycache__/`,
`.runtime/`, `.vscode/` e `out/` foram preservados sem inspeção de payloads de usuário ou limpeza.
Os artefatos untracked (`.agents/`, `.basinfy/`, `.codex/`, `.mcp.json`) não foram adicionados.
Nenhuma mudança funcional, dependência, secret, runtime, configuração Supabase ou serviço externo
foi modificada.

**Movimentações:** `docs/PROJECT_STRUCTURE.md` → `docs/architecture/REPOSITORY_STRUCTURE.md`;
`SEMANTIC_CLASSIFICATION_AUDIT.md` → `docs/architecture/SEMANTIC_CLASSIFICATION_AUDIT.md`;
`PRODUCTION_SECRETS_REQUIRED.md` → `docs/operations/PRODUCTION_SECRETS_REQUIRED.md`. Stubs nos
caminhos antigos preservam links. Contagem de arquivos da raiz não muda por decisão de compatibilidade.
