# CLAUDE.md

Instruções permanentes para agentes (Claude, Codex e equivalentes) que trabalham neste
repositório.

> Estado do projeto descrito pelo código e pelos relatórios de validação identificados abaixo.
> Este arquivo é aditivo. Ao editá-lo, **preserve** as seções existentes; não substitua
> instruções de agente não relacionadas.

---

## Sobre o projeto

**Komyst** — aplicação local (Windows, Python 3.11) que traduz capítulos ilustrados do
inglês para português do Brasil: download, OCR, tradução, reconstrução visual, PDF e gates
de qualidade.

## Fonte oficial e pacote canônico

- A `main` local é a fonte oficial do código concluído; confira `origin/main` antes de preparar uma integração. Uma branch de consolidação não é release nem prova de publicação.
- Mudanças de risco podem usar branch temporária baseada na `main`; depois de testar, documentar e atualizar o board, prepare integração normal e não mantenha uma linha paralela permanente.
- Neste snapshot, `komyst/` é o runtime modular canônico onde callers e testes confirmarem a migração. Entry points e módulos da raiz permanecem como compatibilidade enquanto consumidores não forem auditados; não duplique pipeline, provider, máscara, worker ou contrato de artefatos.
- Preserve branches, worktrees, arquivos não rastreados e alterações de outros agentes. Não use reset/clean/restore em massa para resolver divergências. Classifique mudanças não integradas na matriz de reconciliação.
- Diferencie `IMPLEMENTED`, `INTEGRATED`, `TESTED_OFFLINE`, `TESTED_FROZEN`, `PHYSICALLY_VERIFIED`, `EXTERNAL_GATE` e `DEFERRED`; código ou mocks não autorizam status físico.
- Supabase permanece autoridade de persistência/licença; nunca embuta credenciais administrativas. Não execute Gemini/DeepL pago, consuma YK ou altere produção sem autorização explícita.

Leia antes de mudar qualquer coisa:

- [`docs/technical/DOCUMENTACAO_TECNICA.md`](docs/technical/DOCUMENTACAO_TECNICA.md) — arquitetura, processos, estados, segurança, testes
- [`docs/user/GUIA_DO_USUARIO.md`](docs/user/GUIA_DO_USUARIO.md) — o que o usuário realmente vê
- [`docs/DOCUMENTATION_POLICY.md`](docs/DOCUMENTATION_POLICY.md) — regras completas de manutenção da documentação
- [`docs/README.md`](docs/README.md) — índice

### Comandos essenciais

```powershell
python start_tradutor.py            # worker supervisionado + UI (canônico)
python start_tradutor.py status     # saúde do worker e da fila
python start_tradutor.py stop       # parada graciosa
python -m pytest -q                 # suíte hermética
python run_webtoon.py --help        # flags reais da CLI
```

### Capítulo de referência para teste ponta a ponta (regra permanente)

Para medir gargalos (tempo, limpeza, tradução, reconstrução, PDF) use **sempre** este capítulo,
salvo pedido em contrário de HenriquePvAr. Ele autorizou rodar o capítulo completo com tradução
paga **neste** capítulo; qualquer outro capítulo continua exigindo autorização explícita.

```text
https://www.webtoons.com/en/action/hero-killer/episode-285/viewer?title_no=2745&episode_no=285
```

- Suba o app com `python start_tradutor.py` e abra **`http://127.0.0.1:8080`**, nunca
  `http://localhost:8080`: o CORS das funções do backend (`beta-bootstrap`, `wallet-summary`) só
  aceita a origem `127.0.0.1`; em `localhost` o início falha com "Não foi possível confirmar a
  política de tradução".
- O login (Supabase) é feito pelo próprio usuário no navegador; o agente não digita senha.
  Se a sessão não estiver ativa, peça o login a HenriquePvAr.
- Formulário: URL pública, modo **Qualidade**, saída **Tradução pronta**, "forçar" ligado e cache
  desligado (medição sem reaproveitar nada).
- Tempos por etapa: `timing_report.txt` e `quality_report.json` (`stage_seconds`) na pasta de saída;
  andamento do job em `runtime/jobs.sqlite3` (somente leitura).
- `run_webtoon.py` sozinho **não traduz** (`job_id_required`: só o worker fornece o job); para
  checar apenas limpeza fora do app use `TRANSLATION_ENABLED=false`.

### Regras de segurança do repositório

- **Nunca** leia `.env` ou `.env.local` por inteiro (`cat`, `type`, `Get-Content`). Se
  precisar de uma chave específica, use busca direcionada apenas pelo **nome** da variável.
- **Nunca** escreva valor real de chave, token, senha, cookie, service-role key ou conteúdo
  de token do Drive em código, documentação, log, commit ou captura de tela.
- Use placeholders: `DEEPL_API_KEY=<sua-chave>`, `<repo>`, `<URL_DO_CAPITULO>`.
- Não use caminhos com nome real de pessoa (`C:\Users\<pessoa>\...`).
- Testes não podem tocar o banco de jobs de produção, lançar o worker de produção nem
  chamar provider real. O guard hermético existe para isso — não o contorne.

---

## CONTRATO DE SINCRONIZAÇÃO DA DOCUMENTAÇÃO

**Obrigatório em toda tarefa que muda o projeto.** A documentação viaja junto com o
comportamento: quando prático, código e documentação exigida por ele vivem no **mesmo
commit**.

### Antes de concluir qualquer tarefa

1. **Inspecione `git diff`** — todos os arquivos alterados.
2. **Determine o impacto na documentação** usando os gatilhos abaixo.
3. **Atualize a documentação técnica** quando a mudança tocar: arquitetura, schema de banco,
   estados de job, ciclo de vida do worker/launcher, supervisão de processos, configuração
   de runtime, variáveis de ambiente, integração com provider, segurança, cache, testes,
   API HTTP, empacotamento ou updater.
4. **Atualize o guia do usuário** quando a mudança tocar: instalação, tela, rótulo de botão,
   fluxo de uso, recurso disponível, mensagem de erro ou de status, login, atualização,
   licença, local/nome dos arquivos de saída ou comportamento do PDF.
5. **Atualize as capturas de tela** se a UI visível documentada mudou de forma que a imagem
   existente induza erro. Nunca fabrique uma captura; se não puder capturar com segurança,
   documente a lacuna.
6. **Nunca documente comportamento planejado como implementado.** Classifique como
   IMPLEMENTADO / PARCIAL / PLANEJADO / DEPRECIADO. Documentação de usuário jamais instrui
   o uso de recurso inexistente.
7. **Atualize os metadados de verificação** (`Base verificada` / `Revisado em`) dos
   documentos que você tocou. Use a SHA de base auditada, nunca tente embutir a SHA do
   próprio commit.
8. **Se nenhuma mudança de documentação for necessária, diga isso explicitamente** com
   justificativa.

### Verifique antes de escrever

Nada entra na documentação sem verificação contra o repositório: comandos devem ser
executados (ao menos `--help`), caminhos de módulo devem existir no índice do Git, estados
devem ser lidos de `komyst/runtime/job_store.py` (`JobStatus`), variáveis devem estar em `.env.example` e no consumidor
(ajustes finos de CLEAN/render, como `RENDER_FIT_BALLOON_SHAPE`, existem só em `komyst/config/settings.py` por decisão),
rótulos de UI devem ser lidos de `ui/ui_shell.html` ou `static/*.js`. Um comando que o
repositório não suporta mais **não pode** aparecer na documentação.

### Portão final obrigatório

Toda missão de código termina com este bloco no relatório:

```text
DOCUMENTATION IMPACT

TECHNICAL DOC:   UPDATED / NOT REQUIRED
USER GUIDE:      UPDATED / NOT REQUIRED
SCREENSHOTS:     UPDATED / NOT REQUIRED
WHY:             <uma linha por decisão>
```

Quando nada muda:

```text
DOC IMPACT: NONE
WHY: <motivo — ex.: refatoração interna sem mudança de comportamento, API, config ou UI>
```

**Ausência dessa declaração significa tarefa incompleta.**

### Atualizações futuras já contratadas

- O caminho do usuário é o instalador Beta, instalação e login com licença Beta; não orientar
  testadores a instalar pelo repositório. O guia do usuário cobre primeira execução, atalhos,
  desinstalação e atualização.
- Updater assinado: **já existe** no código e na UI (aba **Atualizações**). Esta obrigação
  está em vigor: doc técnica cobre manifest, verificação de assinatura e de SHA, versão
  mínima, substituição atômica, rollback e estados de falha; o guia do usuário cobre apenas
  como a atualização aparece, o que clicar e o que fazer se falhar. A publicação do manifest
  no canal continua gate externo.
- Instalador Beta: `packaging/Komyst.iss`, `packaging/komyst.spec` e
  `tools/build_installer.py` definem o pacote `Komyst-<versão>-Setup-x64.exe`. A versão
  `v0.9.1-beta.18` foi **validada por beta tester, informado pelo dono**; data não informada.
- Licença de tester: `komyst/auth/beta_license.py` define a autorização fail-closed e a
  integração remota; a versão `v0.9.1-beta.18` foi **validada por beta tester, informado pelo
  dono**; data não informada. Nenhum segredo administrativo deve entrar na documentação.

### Estado do produto e evidência

A tabela resume o código atual e os gates externos conhecidos. Para cada release, confira novamente os contratos no código e os artefatos de validação.
A tabela é um instantâneo do código. Ela envelhece: confira o código antes de assumir que um valor não mudou.

> Os estados desta tabela devem ser conferidos contra o código atual antes de qualquer release.

| Recurso | Estado verificado |
| --- | --- |
| Tradução | **IMPLEMENTADO** — todo job habilitado usa `komyst_backend` (`komyst/translation/providers/komyst_backend_provider.py`, `benchmark_pipeline._resolve_translation_runtime`), motor remoto DeepL na Edge Function `supabase/functions/translation-execute`. O cliente nunca chama a DeepL; `--translation-provider` é metadado/guard; `riva`/`nemotron` num job habilitado → `provider_mismatch`. `ui_helpers.DEFAULT_TRANSLATION_PROVIDER = "deepl"` é só rótulo; o seletor de provider da UI está oculto |
| Provider de auth padrão | **supabase** no código (`community_auth.build_auth_provider`); o `.env.example` traz `local` para desenvolvimento. Este snapshot **não** afirma que o projeto Supabase remoto está acessível (problema operacional, não de código) |
| Estados de job | 15 em `komyst/runtime/job_store.py` `JobStatus.ALL`; terminais `finished`, `review_required`, `failed`, `cancelled` |
| Supervisão do worker | implementada em `komyst/runtime/worker_supervisor.py`: 2s/5s/15s, 3 tentativas, `degraded`, reset em 120s |
| Retomada de job interrompido na UI | **implementada** — `#interruptedJobsPanel` + botão `Retomar` em `static/komyst_ui.js`, exibido só com `can_resume` |
| SFX e tipografia | `TRANSLATE_SFX=False` por padrão (SFX preservados no original); `RENDER_FIT_BALLOON_SHAPE` e `RENDER_MATCH_SOURCE_SLANT` padrão `True`, só em `komyst/config/settings.py` |
| Updater | **IMPLEMENTADO** (código + UI): `komyst/runtime/update_manifest.py` (Ed25519 + SHA-256, chave `beta-2026-10`), `update_transport.py`, `update_installer.py`, `installer_update.py`, `update_bootstrap.py` (`DEFAULT_MANIFEST_URL` configurada), aba **Atualizações** e rotas `/api/update/*` em `komyst/ui/app.py`. Manifest publicado no canal: `EXTERNAL_GATE` |
| Instalador | **IMPLEMENTADO** — `packaging/komyst.spec`, `packaging/Komyst.iss`, `tools/build_installer.py`; `v0.9.1-beta.18` validada por beta tester, informado pelo dono; data não informada |
| Licença de tester Beta | **IMPLEMENTADA** — autorização remota fail-closed; versão `v0.9.1-beta.18` **validada por beta tester, informado pelo dono**; data não informada |
| Instalação limpa em Windows | **Validada por beta tester, informado pelo dono** — versão `v0.9.1-beta.18`; data: não informada |
| CF clearance (comix.to) | o persistidor `_save_comix_cf_clearance` do branch `feat/comix-cloudflare-clearance-v1` **não está** na `main`; só o posicionamento oculto do CloakBrowser existe (`komyst/download/readers/scrapling_reader_resolver.py`) |
| Requisitos | `requirements.txt` na raiz; perfis em `requirements/` (`requirements-beta.txt` inclui `-r ../requirements.txt`) |
| Suíte hermética | Consulte o resultado da suíte anexado à revisão da branch; totais históricos não são estado atual |

Para proveniência e níveis de evidência, consulte o [board operacional](docs/status/board/index.html)
e os documentos técnicos. A validação Beta da versão acima foi informada pelo dono e não foi
executada por esta integração.

### Main-first e preservação

- `main` é a fonte canônica de código concluído. Baseie novas tarefas na `main` atual; use branch temporária para trabalho arriscado e, após testes/documentação/board, prepare integração normal de volta à `main`.
- Não mantenha linhas paralelas permanentes nem descarte worktrees, arquivos não rastreados, evidências ou trabalho de outro agente sem uma decisão explícita e registrada.
- Uma branch de integração local não é merge remoto, beta ou release. Push, merge remoto, instalador e publicação exigem autorização própria.
- Para Supabase, versionar migrations e testes; não alterar produção sem autorização. Preservar fail-closed e não incluir segredos administrativos no cliente.

Detalhes técnicos e dívida histórica:
[Documentação Técnica §29](docs/technical/DOCUMENTACAO_TECNICA.md#29-dívida-técnica-conhecida).
