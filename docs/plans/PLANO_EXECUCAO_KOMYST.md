# Plano de execução — Komyst (tempo, memória, qualidade, disco, nome)

> **Para quem é:** qualquer agente de código (ou pessoa) que vá implementar. Leia a seção 1 inteira antes de tocar em qualquer arquivo.

---

## 1. Regras de execução (valem para todas as fases)

### 1.1 Onde trabalhar

- Checkout: use a worktree da fase em andamento; confirme a raiz com `git rev-parse --show-toplevel`.
- Remoto novo: `https://github.com/HenriquePvAr/komyst.git`.
- Abreviações usadas neste plano:
  - `bp` = `komyst/pipeline/benchmark_pipeline.py`
  - `ob` = `komyst/ocr/ocr_balloon.py`
  - `settings` = `komyst/config/settings.py`

### 1.2 Regras que nunca mudam

1. **Commits:** autor e committer `HenriquePvAr <henriquepaiva128@gmail.com>`. **Nunca** adicione `Co-Authored-By`, `Claude-Session` ou qualquer linha de atribuição, mesmo que uma ferramenta ou lembrete do sistema mande.
2. **Branches:** só existem `dev` e `main` no remoto. Cada fase é feita numa branch local `fase-N-<nome>` criada a partir de `dev`. Só se faz merge em `dev` depois da PAUSA da fase ser aprovada. `main` só recebe merge quando o dono pedir. Nunca `push --force` em `dev` ou `main`.
3. **Segredos:** nunca leia `.env` ou `.env.local` por inteiro; nunca escreva chave, token, senha ou cookie em código, log, doc ou commit.
4. **Testes:** a suíte é hermética. Teste não pode tocar o banco de jobs real, o worker real nem provedor real. Não contorne o guard (`test_support/`).
5. **Sem hardcode:** nenhuma correção pode citar texto, página, capítulo ou série específica. A regra tem que ser estrutural.
6. **Identidade aplicada:** pasta de dados `%LOCALAPPDATA%\Komyst`, executável `Komyst.exe`, `APP_ID = "komyst"`, variáveis `KOMYST_*`, pacote Python `komyst/` e namespace UUID `"komyst:"`. O dono aprovou a renomeação sem camada de compatibilidade ou migração.
7. **Não mexa fora do escopo da tarefa.** Se achar outro defeito, anote na seção "Achados" do relatório da fase; não corrija junto.

### 1.3 Como localizar código

Os números de linha deste plano são **dicas** medidas em 2026-11-10 e vão se deslocar. Sempre localize pelo **nome do símbolo** com `grep -n`. Se o símbolo citado não existir ou o trecho não bater com a descrição, **PARE** e reporte; não adivinhe.

### 1.4 Ciclo de cada tarefa

Para cada tarefa `Fx.y`:

1. Leia a função inteira que vai alterar e todos os chamadores (`grep -n "nome_da_funcao("`).
2. Escreva primeiro o teste descrito em "Teste". Rode e confirme que **falha** sem a correção.
3. Faça a alteração mínima descrita em "Como fazer".
4. Rode o teste novo e os testes focados da área (`python -m pytest -q -p no:cacheprovider tests -k "<palavras>"`).
5. Um commit por tarefa, mensagem no formato `fix(area): resumo` ou `feat(area): resumo`, em português, sem citar nomes de jogos, pessoas ou séries.

### 1.5 Protocolo de PAUSA

Em cada **PAUSA** o agente para, não inicia a fase seguinte, e entrega:

1. Lista de commits da fase (`git log --oneline dev..HEAD`).
2. Resultado da suíte completa (`python -m pytest -q -p no:cacheprovider`, leva ~14 min; rode em segundo plano com saída em arquivo).
3. Tabela de métricas **antes × depois** gerada por `tools/audit/job_metrics.py` (criado na tarefa P.4) nos dois capítulos de referência.
4. Bloco `DOCUMENTATION IMPACT` exigido pelo `CLAUDE.md`.
5. Seção "Achados" e seção "O que não consegui fazer".

Quem revisa a PAUSA confere os critérios de aceite da fase. **Se qualquer critério de aceite falhar, a fase não é mergeada.**

**Autonomia no trabalho da fase (decisão do dono, 2026-11-11).** Execute as tarefas na ordem, na branch da fase; faça commits locais por assunto com autor HenriquePvAr e sem coautoria; rode testes focados e a suíte completa; atualize relatórios, quadro e as notas `Status\\` e `Qualidade\\` do cofre Obsidian. Jobs Apenas Clean por linha de comando são permitidos nos dois capítulos de referência, quantas rodadas forem necessárias. Leia logs, relatórios e o banco de jobs somente leitura. Corrija testes desatualizados quando o comportamento mudou intencionalmente, explicando a decisão no commit. Quando detalhes não estiverem prescritos, decida estruturalmente e registre a escolha no relatório.

Pare e pergunte antes de push, merge em `dev` ou `main`, force, exclusão de dados/pastas/branches, alterações em `.env`, instalação global ou mudança no ambiente da máquina, mudança de comportamento visível fora do escopo, queda de qualidade em REF-A/REF-B, mais de duas tentativas frustradas na mesma correção ou qualquer tarefa fora do plano. Se houver bloqueio, registre a pergunta no relatório da tarefa, avance tarefas independentes e só pare quando não houver trabalho independente. Agrupe pedidos de jobs pagos (máximo de dois por fase), nunca inicie tradução paga por automação de navegador: informe os cliques exatos e aguarde o dono iniciar. Não aceite tempo sem confirmar `(GPU DirectML)` no log.

### 1.6 Capítulos de referência

| Id | Uso | URL |
|---|---|---|
| **REF-A** | Regressão (histórico de medições) | `https://www.webtoons.com/en/action/hero-killer/episode-285/viewer?title_no=2745&episode_no=285` |
| **REF-B** | Capítulo novo, romance, 85 páginas, muito balão | `https://www.webtoons.com/en/romance/were-not-a-couple/ep-4-at-my-ex-boyfriends-place/viewer?title_no=11536&episode_no=4` |

Tradução paga está autorizada **somente** nesses dois capítulos. O dono inicia jobs pagos pela interface em `http://127.0.0.1:8080` (não `localhost`); não use automação de navegador para iniciar esses jobs. Diga exatamente capítulo, modo e opções e aguarde o dono informar que iniciou; depois acompanhe pelo banco de jobs e pelo `job_metrics.py`. Jobs Apenas Clean sem provedor podem ser executados por linha de comando.

Modo padrão das medições: plano **Tradução pronta**, "traduzir SFX" desligado (é o padrão da tela). Quando a tarefa disser "modo Completo", use o plano **Completo**.

### 1.7 Ordem de execução

A ordem de trabalho é: **Fase 0 → Fase 3 → Fase 1 → Fase 2 → Fases 4, 5 e 6**. A prioridade definida pelo dono é limpeza, reconstrução e tradução. A numeração das fases permanece igual; somente a ordem de execução muda.

---

## 2. Linha de base medida (2026-11-10)

Estes são os números contra os quais cada fase é comparada.

### 2.1 Tempo — REF-A, job `721d1f8f` (535 s, modo Completo)

| Etapa | Segundos |
|---|---|
| Download | 99 |
| Corte inteligente + pré-checagem | 38 |
| OCR | 25 |
| Análise + varredura de resíduo (Paddle) | 108 |
| Pré-render de layout (tela mostra "tradução") | 130 |
| Tradução (rede) | 5 |
| Render final | 17 |
| Exportação PSD + PDF | 76 |
| Relatórios finais | 30 |

Em 2026-11-03 o mesmo capítulo levava ~300 s em Tradução pronta. REF-B levou 641 s (modo Completo).

**Correção da linha de base (2026-11-13).** Os números históricos de REF-A Apenas Clean (288,7 s) e Tradução pronta (278,2 s) foram medidos em ambiente degradado: o Paddle não iniciou corretamente, a varredura de resíduos foi pulada sem indicação de indisponibilidade (`residual_sweep` 2,7 s), não houve correção automática e o OCR contou 217 linhas contra 225 com Paddle funcionando. Esses tempos não são uma base válida de desempenho. Com Paddle funcional, REF-A Apenas Clean levou aproximadamente 330 s; no job `39a41cbb…`, o medidor registrou 329,43 s totais e 98,03 s na varredura de resíduos. O job REF-B Completo `c7ee941a073945db82a225d48a435c48` levou 480,62 s, com 169/177 traduções, 70/85 certificados e 7 resíduos, igual à base de qualidade. Use os números saudáveis como referências; preserve os históricos como medições degradadas, não os apague.

### 2.2 Qualidade

| Métrica | REF-A (`f181a17e`) | REF-B (`278c2486`) |
|---|---|---|
| Regiões traduzidas / detectadas | 57 / 58 | 169 / 177 |
| Páginas com certificado de limpeza | 62 / 65 | 70 / 85 |
| Portão físico | passou | reprovou (7 resíduos) |
| Resultado do job | `review_required` | `failed` (`translation_policy_violation`) |

### 2.3 Memória e disco

- Pico medido (REF-A, com FLUX, máquina de 32 GB + RX 6600 8 GB): 8,4 GiB em uso, 13,7 GiB comprometidos, 4,7 GiB de VRAM. Fonte: `docs/HARDWARE_PROFILE.md`.
- O monitor de recursos está **desligado** nos jobs (`RESOURCE_MONITORING=False`), então não há RAM por job.
- Disco por job (mediana de 65 execuções): Tradução pronta 9,1 MB/página; Apenas Clean 4,7 MB/página; Completo 37,3 MB/página. O PDF é só 0,22 MB/página.
- Pasta de saída: 56 GB; disco em 91%. Dois jobs morreram por disco cheio.

---

## PRÉ-FASE P — Preparação

Objetivo: deixar o repositório e o disco num estado conhecido. **Nenhuma mudança de comportamento do pipeline aqui.**

### P.1 Apontar o remoto para o repositório novo

```bash
git -C /c/Projetos/Komyst remote set-url origin https://github.com/HenriquePvAr/komyst.git
```

```bash
git -C /c/Projetos/Komyst fetch origin
```

Aceite: `git remote -v` mostra `komyst.git`; `git fetch` funciona; `origin/dev` e `origin/main` existem.

### P.2 Inventariar a árvore de trabalho (NÃO commitar ainda)

A branch atual tem ~116 arquivos alterados sem commit: uma renomeação para "Komyst" pela metade **misturada** com código novo (`komyst/clean/inpainting/flux_edit.py`, `komyst/ocr/residual_sweep.py`, `komyst/ocr/subprocess_ocr*.py`, testes).

Como fazer:

1. Salve `git status --short` num arquivo e classifique cada entrada em três grupos: **(a) código/teste**, **(b) renomeação em docs/UI**, **(c) arquivos novos não rastreados**.
2. Não rode `git add -A`. Não faça stash. Não descarte nada.
3. Entregue a classificação na PAUSA P. O dono decide o que vira commit.

### P.3 Liberar disco (autorizado pelo dono)

Regra: em `%LOCALAPPDATA%\Komyst\output\<capítulo>\`, manter as **3 execuções mais recentes** de cada capítulo e **sempre** manter estas, que são a linha de base: `f181a17e-281d-40a8-bd7e-41b4bbdcdca1`, `2054d996-7785-40cb-a428-5d266d8ffed8`, `278c2486-02ae-4103-8a15-6f5ece95e26b`.

Como fazer:

1. Liste antes (nome, data, tamanho) e salve a lista no relatório.
2. Apague só pastas de execução (nome em formato UUID) que não estejam na lista de mantidas. Nunca apague `cache`, `models`, `runtime`, `auth`.
3. Não apague a pasta de um job com status `running`, `queued` ou `interrupted` no banco (leia `runtime/jobs.sqlite3` em modo somente leitura: `file:...?mode=ro`).

Aceite: pelo menos 40 GB livres a mais; as três execuções de base ainda existem.

### P.4 Criar o medidor de jobs

Arquivo novo: `tools/audit/job_metrics.py`. É só leitura; não importa nada de `Komyst`.

Entrada: caminho de uma pasta de execução. Saída: um JSON e uma tabela em texto com:

- `total_seconds` e `stage_seconds` (de `timing_report.json`);
- contagem de `clean_certificate.reason` por página (de `artifact_manifest.json` → `provenance`);
- `translation_accounting`, `severity`, `reason_codes`, `physical_gate_passed`, `physical_source_residual_count` (de `quality_report.json` → `summary.quality_validation`);
- contagem de `(translation_final_state, translation_final_reason)` e de `cleanup_fill_source` nos `translation_terminal_items`;
- bytes por subpasta e total, e MB por página (páginas = `pages/page_NNN.png` sem `_cleaned`);
- `resource_monitoring` (pico de RAM), quando existir.

Com dois caminhos (`--compare A B`), imprime a tabela lado a lado com a diferença.

Teste: `tests/test_job_metrics_tool.py` monta uma pasta falsa mínima em `tmp_path` e confere os campos.

Aceite: rodar nas três execuções de base reproduz os números da seção 2.

### ⏸ PAUSA P

Entregar: saída de P.1, classificação de P.2, lista do que foi apagado em P.3, saída do medidor nas três bases.

Decisão do dono nesta pausa: **como commitar a árvore de trabalho** e **levar a branch atual para `dev`**. Só depois disso as fases começam, sempre a partir de `dev`.

---

## FASE 0 — Parar de perder jobs

Objetivo: nenhum job morre por causa de disco, de uma regra de SFX ou de um subprocesso travado.

### F0.1 Portão de SFX: violação só quando um SFX foi enviado ao provedor

**Problema.** REF-B terminou `failed` com PDF e PSD prontos. Com "traduzir SFX" desligado, o portão exige que todo item `sfx` esteja `ignored`. Um item ("RUSTLE...", p52) estava `sfx`, não ignorado e **não enviado** ao provedor; isso reprovou o capítulo.

**Onde.** `bp`, função que monta o dicionário com a chave `"sfx_policy_valid"` (procure `sfx_policy_ok`; ~linha 8143). Consumidor: `komyst/ui/ui_helpers.py`, onde `sfx_policy_valid is False` vira `translation_policy_violation` (~linha 533).

**Como fazer.**

1. A política protegida é: *com tradução de SFX desligada, nenhum SFX vai ao provedor*. Troque a condição para:

   ```python
   sfx_sent_items = [item for item in preserved_sfx_items if item.get("sent_to_nvidia")]
   sfx_policy_ok = bool(config.TRANSLATE_SFX) or not sfx_sent_items
   ```

2. Acrescente ao dicionário de retorno: `"sfx_sent_to_provider_groups": len(sfx_sent_items)` e `"sfx_not_ignored_groups": <quantidade de itens sfx com ignored falso>`.
3. Não altere `ui_helpers.py`: a violação continua estrutural quando um SFX realmente foi enviado.

**Causa-raiz a investigar (mesma tarefa).** `ob._apply_classification_policy` marca `ignored=True` para `sfx` quando `TRANSLATE_SFX` é falso (procure `sfx_translation_disabled`). O item escapou porque virou `sfx` **depois** dessa política. Procure onde `classification = "sfx"` é atribuído fora de `_apply_classification_policy` e garanta que a política seja reaplicada logo após a reclassificação. Se houver mais de três pontos, PARE e liste-os em vez de alterar todos.

**Teste.** `tests/test_sfx_policy_gate.py`:

- SFX não ignorado e não enviado, `TRANSLATE_SFX=False` → `sfx_policy_valid` verdadeiro, `sfx_not_ignored_groups == 1`.
- SFX enviado (`sent_to_nvidia=True`), `TRANSLATE_SFX=False` → `sfx_policy_valid` falso.
- `TRANSLATE_SFX=True` → sempre verdadeiro.

**Aceite.** REF-B não termina mais em `failed` por `translation_policy_violation`.

### F0.2 Checar espaço em disco antes e durante o job

**Problema.** Dois jobs foram interrompidos por `OSError: [Errno 28] No space left on device`; um ficou 64 minutos preso.

**Onde.** `komyst/runtime/job_runner.py`, função `run_job` (~linha 852), antes de lançar o pipeline. Segundo ponto: `bp`, logo depois que o download termina e o número de páginas é conhecido (procure `DOWNLOAD_STAGE_RESULT`).

**Como fazer.**

1. Novo módulo `komyst/runtime/disk_budget.py` com:
   - `MB_PER_PAGE = {"profissional": 60, "apenas_clean": 8, "default": 15}` (medido: 37 / 4,7 / 9,1 MB por página, com ~60% de margem);
   - `MIN_FREE_MB_AT_START = {"profissional": 3000, "default": 1000}`;
   - `required_mb(output_plan, page_count=None) -> int`;
   - `free_mb(path) -> int` usando `shutil.disk_usage`;
   - `check(path, output_plan, page_count=None) -> tuple[bool, dict]`.
2. Em `run_job`: se `check` falhar, encerre o job com `status="failed"`, `reason_code="insufficient_disk_space"`, mensagem com MB livres e MB necessários. Não lance o pipeline.
3. Em `bp`, depois do download: chame `check` de novo com o número real de páginas. Se falhar, levante um erro próprio (`InsufficientDiskSpace`) que o runner traduz para o mesmo `reason_code`.
4. Qualquer `OSError` com `errno == 28` capturado no laço de páginas deve encerrar o job imediatamente com esse `reason_code` (hoje o job continua tentando gravar).
5. Mensagem para o usuário: acrescente a chave `insufficient_disk_space` no mapa de mensagens de erro de `static/komyst_ui.js` (procure a entrada `transport_error:`) e nos arquivos `static/i18n/*.js`. Texto pt-BR: "Espaço em disco insuficiente para gerar este capítulo. Libere espaço e tente de novo."

**Teste.** `tests/test_disk_budget.py`: `required_mb` por plano; `check` com `shutil.disk_usage` simulado; `run_job` com disco simulado cheio termina com `insufficient_disk_space` sem lançar o pipeline (use os fakes já existentes dos testes de `job_runner`).

**Aceite.** Com disco simulado cheio, o job falha em menos de 5 s com a mensagem nova.

### F0.3 Retenção de execuções antigas

**Problema.** 38 execuções de um mesmo capítulo ocupavam 30 GB.

**Onde.** Novo módulo `komyst/runtime/output_retention.py`. Chamada: no ponto do runner onde o job é marcado como terminal com sucesso (`completed` ou `review_required`).

**Como fazer.**

1. Nova configuração em `settings`: `OUTPUT_KEEP_RUNS_PER_CHAPTER = _env_int("OUTPUT_KEEP_RUNS_PER_CHAPTER", 3)` (0 = nunca apagar). Documente em `.env.example` e `docs/CONFIGURATION.md`.
2. `prune_chapter_runs(chapter_dir, keep, protected_run_ids)`: ordena as subpastas com nome UUID por data de modificação e apaga as mais antigas além de `keep`.
3. **Nunca apagar:** a execução do job atual; execuções de jobs com status não terminal ou `interrupted`; execuções publicadas na comunidade.
4. **Antes de implementar a exclusão**, leia como a exclusão manual já funciona (procure `shutil.rmtree(folder` em `komyst/ui/ui_bridge.py`, ~linha 4734, e o botão "Excluir capítulo"). A retenção deve **reutilizar a mesma função**, para que o histórico e o banco fiquem coerentes. Se essa função não puder ser reutilizada sem refatorar, PARE e reporte.
5. Falha na retenção nunca derruba o job: capture, registre no log e siga.

**Teste.** `tests/test_output_retention.py` com `tmp_path`: mantém as N mais novas; respeita protegidas; `keep=0` não apaga; erro de permissão não propaga.

**Aceite.** Rodar REF-A quatro vezes deixa três pastas de execução.

### F0.4 Diagnóstico das duas saídas PSD

**Objetivo.** Determinar se os dois conjuntos PSD são duplicatas ou saídas distintas antes de qualquer alteração ou remoção.

**Como fazer.** Para uma página de REF-A, registrar em `docs/reports/` tamanho e camadas recursivas dos PSDs em `psd/` e em `result_path`, identificar quais camadas são texto nativo/imagem/grupo, verificar se cada caminho tem conteúdo exclusivo e listar os consumidores em UI, manifesto e testes. Não alterar os arquivos gerados nesta tarefa.

**Resultado inicial (2026-11-11).** Diagnóstico: as saídas são diferentes, ambas contêm texto nativo editável; `psd/` tem uma camada adicional de texto e `result_path` tem a prévia traduzida. Manter ambas até uma decisão de produto sobre eventual consolidação.

**Conclusão.** A premissa de que o PSD era gravado em duplicidade estava errada. As duas saídas têm funções e conteúdo distintos; a decisão sobre unificá-las permanece em aberto. Nenhum arquivo ou caminho de saída será removido nesta tarefa.

**Teste/aceite.** Diagnóstico verificável com uma página de REF-A e consumidores rastreados. Nenhuma alteração de conteúdo ou comportamento PSD nesta tarefa. Uma futura mudança de gravação precisa de decisão sobre os recursos exclusivos de cada formato e medição separada de MB/página em REF-A e REF-B.

### F0.5 Timeout real no subprocesso do Paddle

**Problema.** `_REQUEST_TIMEOUT_SECONDS = 45.0` existe em `komyst/ocr/subprocess_ocr.py` mas nunca é usado. `self._process.stdout.readline()` bloqueia sem limite, com o lock do gateway preso.

**Onde.** `komyst/ocr/subprocess_ocr.py`, método que escreve o payload e lê a resposta (laço `for _ in range(500)`).

**Como fazer.**

1. Leia a resposta numa thread leitora (ou `concurrent.futures`) e espere com `timeout=_REQUEST_TIMEOUT_SECONDS`.
2. No estouro: mate o processo filho, chame `self._restart_or_give_up("worker_timeout")` e devolva o mesmo resultado que o caminho de erro de E/S já devolve (sem linhas). Não levante exceção para o chamador.
3. Não mude o protocolo JSON nem `_RESTART_BUDGET`.

**Teste.** Em `tests/test_subprocess_ocr.py`: um worker falso que nunca responde; com o timeout reduzido por `monkeypatch` para 0,5 s, a chamada retorna em menos de 3 s e registra `worker_timeout`.

**Aceite.** Teste novo passa; os testes existentes do arquivo continuam passando.

### F0.6 Monitor de recursos ligado por padrão

**Problema.** Nenhum job registra RAM. `psutil` está instalado (7.2.2).

**Onde.** `settings`: `RESOURCE_MONITORING` (~linha 323). Uso em `bp` (~linha 2793) e `komyst/runtime/resource_monitor.py`.

**Como fazer.**

1. Mude o padrão para `True`.
2. Confirme que `psutil` está em `requirements/*.txt`; se não estiver, acrescente.
3. Garanta que o resumo (pico de RSS do processo e filhos, pico de RAM do sistema, pico de swap) vai para `timing_report.json` em `resource_monitoring`. Não gere o relatório HTML por padrão (só JSON e CSV); HTML fica opt-in.
4. Meça o custo diretamente como `resource_monitor_sampling_seconds / total_seconds`. O intervalo inicial foi 5 segundos; se o custo exceder 2%, aumente o intervalo e repita o Apenas Clean. Foi medido 2,13% a 5 s e 1,07% a 10 s em REF-A; 10 s passa a ser o padrão versionado. Após autorização do dono, `.env` local passou a declarar `RESOURCE_MONITOR_INTERVAL_SECONDS=10.0`; app e worker foram reiniciados e os jobs do painel registraram `interval_seconds: 10.0`.

**Teste.** Ajuste os testes que assumem o padrão desligado.

**Aceite.** `tools/audit/job_metrics.py` mostra pico de RAM em REF-A e REF-B; medição direta em REF-A manteve o custo de amostragem em 1,07% a cada 10 s. Confirmar no job de interface qual intervalo foi efetivado pela configuração local.

### F0.7 Dispositivo de inferência observável e alerta de perda da GPU

**Problema.** Com `GPU_INFERENCE=auto`, o ONNX Runtime pode perder o DirectML e continuar em CPU sem um aviso destacado no job. Isso torna OCR e reconstrução mais lentos e dificulta distinguir regressão de código de alteração do ambiente.

**Como fazer.** Registrar um aviso claro quando `auto` não encontrar `DmlExecutionProvider`; se as distribuições `onnxruntime` e `onnxruntime-directml` estiverem simultaneamente instaladas, explicar o conflito de arquivos compartilhados e os comandos para reinstalar DirectML. Gravar no `timing_report.json` os dispositivos efetivamente observados para OCR e LaMa, além do modo configurado e dos provedores disponíveis. Exibir essa informação em `tools/audit/job_metrics.py`.

**Teste.** Testes offline cobrem ausência de DirectML com conflito de distribuições, operação normal com DirectML e leitura/exibição das métricas.

**Aceite.** Job com perda silenciosa de DirectML gera aviso acionável e identifica os dispositivos efetivos no relatório; OCR e LaMa observados durante a execução ficam distinguíveis de uma mera detecção de capacidade do ambiente.

### F0.8 Apenas Clean aceita página uniforme somente com prova de limpeza

**Problema.** Em REF-A, duas execuções `Apenas Clean` pela interface falharam na página 34 com `RuntimeError: imagem final invalida`. A fonte dessa página contém apenas dois textos claros sobre fundo preto; removidos os dois alvos, a saída uniformemente preta é válida. O validador relativo à fonte, porém, interpreta qualquer fonte com variância alta seguida de saída uniforme como destruição de conteúdo. Em `Apenas Clean`, não há texto traduzido para elevar a variância da imagem final.

**Como fazer.** Na validação de render, manter a regra geral de rejeitar saídas vazias/corrompidas. Abrir a exceção apenas quando o plano não pede composição de texto, o certificado Clean da página valida e os pixels da saída são idênticos ao artefato limpo certificado. Não aceitar página uniforme sem certificado ou quando saída e artefato limpo diferirem. Garantir que a falha de página resulte em status coerente entre log, manifesto e cartão do histórico.

**Teste.** Cobrir: página uniforme com certificado válido e bytes de pixels iguais é aceita; página uniforme sem certificado é rejeitada; saída diferente do artefato certificado é rejeitada. Adicionar verificação de `resource_monitor_sample_count` e `resource_monitor_sampling_seconds` no `timing_report.json`.

**Aceite físico.** REF-A `Apenas Clean` disparado pela interface termina sem estado `failed` e produz as 65 imagens limpas; log, manifesto e cartão de histórico concordam. O relatório de tempo inclui a contagem de amostras e segundos gastos dentro das amostragens, permitindo calcular a fração sobre o tempo total.

### F0.9 Falhas do FLUX rastreáveis e repetição controlada

**Problema.** Um erro real do `sd-cli.exe` foi resumido como `caption_effect_model_unavailable`, escondendo o motivo (`generative_output_missing`, categoria `output_or_process_failure`) e apagando o stderr junto com o diretório temporário. A tentativa isolada funciona; o erro precisa ficar diagnosticável no job.

**Como fazer.** Em falha do subprocesso, preservar as últimas 40 linhas do stderr em `errors/flux_<página>_<região>.log` e registrar o caminho na telemetria. A recusa por modelo indisponível só se aplica quando `available()` retorna falso; resultado nulo do processo preserva o motivo real da telemetria. Repetir uma vez somente quando `process_failure_category == output_or_process_failure`; não repetir para `device_memory` nem outras categorias.

**Teste.** Simular o subprocesso: falha grava o arquivo e a telemetria mantém o motivo; falha seguida de sucesso retorna a imagem para os validadores normais; duas falhas param após a segunda tentativa e deixam o fluxo de reconstrução LaMa prosseguir.

**Aceite físico.** Fazer REF-A `Apenas Clean` por linha de comando, conferir 65 imagens e calcular segundos de amostragem / tempo total; após o dono iniciar REF-A `Tradução pronta`, verificar a página 23. Se o FLUX falhar, o artefato em `errors/` deve conter o stderr diagnóstico. Rodar a suíte completa e parar na PAUSA 0 sem push.

**Resultado físico consolidado (2026-11-11).** REF-A Apenas Clean pela interface, job `5dae49f7326b4c56b0c0e0731ec6b253` no commit `8791609`, terminou `review_required` e entregou 65/65 imagens; OCR e LaMa usaram DirectML. Isso fecha a validação física de F0.8 no código final. O `timing_report.json` registra 46 amostras, 23,600 s de amostragem em 477,645 s (4,94%) e pico da árvore de processos de 8.461,906 MB. O worker era PID 36048, `pythonw.exe` do Python311. REF-A Tradução pronta `abee1571…`, em `6c4734b`, teve 57/58 traduzidas, 62/65 certificados, gate físico aprovado com zero resíduos; p023 usou FLUX com sucesso em 20,45 s. REF-B base `278c2486` contra `432b35af`: `job_metrics.py` confirma 169/177 traduzidas, 70/85 certificados e 7 resíduos nos dois; tempo 641,260→599,511 s; `failed`→`review_required`. A contagem auditada é 70 em ambos; relatórios anteriores que diziam 69 estavam incorretos. A comparação REF-A usa linha de base documentada porque o diretório da base `f181a17e` não está mais no caminho registrado.

**Suíte e ambiente (11/11).** A suíte local anterior deu 6.499 pass, 4 falhas, 141 skipped, 1 xfailed, 8 warnings e 787 subtests em Python 3.11/OpenCV 4.10.0/NumPy 2.3.5. O dono confirmou que, sob OpenCV 5.0.0 do ambiente de referência, três falhas passam e resta uma falha real para F3.0. `python` e `python -s` desta sessão carregam 4.10.0 do caminho global; o worker do job `5dae49f7` usou o mesmo Python311. A versão e o caminho do OpenCV agora são gravados em `timing_report.json` e exibidos pelo medidor nos novos jobs. As medições CLI feitas nesta sessão com 4.10.0 estão marcadas como não comparáveis ao ambiente fixado no relatório; nenhum pacote foi instalado/removido.

**PAUSA 0.** Evidência física REF-A/REF-B e F0.8 registrada. Fase 0 pronta para revisão do merge em `dev`, aguardando aprovação explícita do dono. A falha real antiga de máscara segue para F3.0. Nenhum merge ou push foi feito.

### ⏸ PAUSA 0

Rodar REF-A e REF-B (REF-B em modo Completo). Critérios de aceite da fase:

- [x] REF-B termina `review_required`, nunca `failed` (base `failed`; 169/177, 70/85 e 7 resíduos mantidos).
- [ ] Nenhum job fica mais de 10 s rodando depois de um erro de disco.
- [x] Pico de RAM aparece no relatório de tempo dos dois capítulos (REF-A `abee1571`, REF-B `432b35af`).
- [x] Qualidade: REF-A manteve 57/58, 62/65 e gate aprovado; REF-B manteve 169/177, 70/85 e 7 resíduos conforme os artefatos auditados.
- [x] F0.8 físico executado pelo painel no código final `8791609`: job `5dae49f7`, 65/65 imagens e DirectML.
- [x] Falhas de teste classificadas pelo OpenCV efetivo: três dependem de 4.10.0 vs 5.0.0; uma falha real segue para F3.0. Nenhuma correção de ambiente global foi feita.

---

## FASE 1 — Memória

Objetivo: o uso de RAM deixa de crescer com o número de páginas. Medição: pico de RSS do monitor (F0.6) em REF-B (85 páginas) contra REF-A (65 páginas).

### F1.1 Liberar de verdade o estado da página

**Problema.** O bloco `finally` do laço de render faz `state.pop("original_bgr")`, `"candidates"`, `"groups"`, `"translatable_groups"`, `"raw_lines"` (`bp` ~linha 4088), mas isso atua numa **cópia**; a lista principal `page_states` mantém tudo até o fim. `pre_page_results`, `translation_targets` e `all_analyzed_groups` (`bp` ~3544–3559) também seguram todos os grupos.

**Como fazer.**

1. Antes de alterar, escreva no relatório quem lê cada campo depois do render: procure usos de `page_states` após o laço de render (qualidade, manifesto, PDF, PSD, relatórios). Liste campo por campo: quem lê `groups` depois? quem lê `original_bgr` depois?
2. Crie `_release_page_buffers(state)` em `bp`. Ela remove **só** os campos que ninguém lê depois: imagens (`original_bgr`, `clean_local_base`, `_preflight_render`), `candidates`, `raw_lines`. Para `groups`, chame F1.2 em vez de remover.
3. Chame `_release_page_buffers` no objeto que está **dentro** de `page_states` (não na cópia), nos dois caminhos: serial e paralelo (onde `state.update(result.page_state)` acontece, `bp` ~4110).
4. Depois da etapa de tradução, esvazie `pre_page_results` (`.clear()`) se nada mais o lê; confirme com grep antes.
5. Se algum leitor posterior precisar da imagem original (por exemplo o certificado de limpeza compara `original_bgr` com o arquivo), faça esse leitor recarregar do disco (`state["image_path"]`) em vez de manter a imagem na memória.

**Teste.** `tests/test_page_buffer_release.py`: estado falso com arrays numpy; depois de `_release_page_buffers`, os campos de imagem sumiram e os campos que relatórios leem continuam.

### F1.2 Liberar os buffers do tamanho da página presos nos grupos

**Problema.** Cada grupo guarda arrays do tamanho da página: `_fill_source_bgr` (referência à imagem original), `authorized_fill_extension`, `structure_protect_mask`, `light_enclosure_interior`, `fill_alternatives`, `_caption_effect_layers`.

**Como fazer.**

1. Em `ob`, crie `release_group_buffers(group)` que faz `setattr(group, nome, None)` para cada um desses atributos (e `fill_alternatives = []`).
2. Chame-a para todos os grupos da página no fim do render da página, **depois** que `capture["authorized_cleanup_mask"]` foi montado (procure essa chave em `ob`; a máscara autorizada usa `authorized_fill_extension`, então a liberação tem que vir depois).
3. Confirme com grep que nenhum código lê esses atributos depois desse ponto (PSD e relatórios leem do dicionário de depuração, não do grupo; confirme).

**Teste.** Em `tests/test_page_buffer_release.py`: grupo com os seis atributos preenchidos; após a chamada, todos `None` ou vazios.

### F1.3 Não reter o pré-render no caminho paralelo

**Problema.** O pré-render de layout guarda página final, dados de depuração e captura limpa em cada estado. O caminho serial remove (`state.pop("_preflight_render")`, `bp` ~3945); o paralelo remove só da cópia local (`local.pop`, `bp` ~1511).

**Como fazer.** Em `process_post_translation_page`, devolva em `page_state` a chave `"_preflight_render": None`, para que o `state.update(...)` do chamador sobrescreva e libere. Confirme que `_release_page_buffers` (F1.1) também remove a chave.

**Teste.** Chamada direta de `process_post_translation_page` com um estado que tem `_preflight_render`: o `page_state` devolvido não mantém o conteúdo.

### F1.4 PDF sem carregar todas as páginas na memória

**Problema.** `komyst/export/pdf.py` (~linhas 150–159) abre todas as páginas em PIL RGB, guarda numa lista e só então chama `save(..., save_all=True, append_images=rest)`.

**Como fazer.**

1. Passe um **gerador** para `append_images` em vez de uma lista: uma função que abre, converte e entrega uma página por vez. O Pillow aceita iterável.
2. Mantenha a primeira página aberta só até o `save` terminar.
3. Não mude ordem das páginas, DPI, nem o nome ou local do arquivo temporário.

**Teste.** Nos testes de PDF existentes, acrescente um que gera PDF de 30 páginas pequenas e confere contagem e ordem das páginas. Verificação manual: comparar o PDF de REF-A antes e depois (mesmo número de páginas, mesmas dimensões).

### F1.5 Guarda de memória antes de LaMa e FLUX

**Problema.** Nenhum código checa RAM ou VRAM antes de carregar modelos. LaMa não limita o tamanho do recorte.

**Onde.** `komyst/clean/inpainting/advanced_art_inpainting.py` (carga do LaMa, recorte com margem ≤ 256 px), `komyst/clean/inpainting/flux_edit.py` (`available()`), `komyst/core/gpu.py`.

**Como fazer.**

1. Novo módulo `komyst/runtime/memory_guard.py`: `available_ram_mb()` (psutil; sem psutil devolve `None`) e `allow(feature, need_mb) -> bool` (se não souber medir, permite).
2. Novas configurações em `settings`: `LAMA_MIN_FREE_RAM_MB = 1500`, `FLUX_MIN_FREE_RAM_MB = 6000`, `LAMA_MAX_CROP_PIXELS = 4_000_000`.
3. LaMa: se o recorte passar de `LAMA_MAX_CROP_PIXELS` ou a guarda negar, o caminho devolve "não disponível" exatamente como já faz quando o modelo falta. A região segue a escada normal e pode acabar em revisão.
4. FLUX: `available()` passa a consultar a guarda.
5. Cada negação é contada em `counters` (`lama_skipped_low_memory`, `flux_skipped_low_memory`) e vai para o relatório de tempo.

**Teste.** `tests/test_memory_guard.py`: com `available_ram_mb` simulado baixo, LaMa e FLUX reportam indisponível e o contador sobe; com valor alto, permitem.

### ⏸ PAUSA 1

Critérios de aceite:

- [ ] Pico de RSS em REF-B (85 páginas) ≤ 1,15 × pico em REF-A (65 páginas). Antes desta fase, anote os dois picos com o monitor da F0.6.
- [ ] Pico de RSS em REF-A cai pelo menos 25% em relação ao medido na PAUSA 0.
- [ ] PDFs de REF-A e REF-B com o mesmo número de páginas e as mesmas dimensões de antes.
- [ ] Qualidade (seção 2.2) igual ou melhor.
- [ ] Suíte completa verde.

---

## FASE 2 — Tempo

Objetivo: REF-A em Tradução pronta ≤ 300 s, sem perder nenhuma métrica de qualidade. Faça as tarefas **nesta ordem**; cada uma é medida sozinha.

### F2.1 Varredura de resíduo (Paddle) só onde há evidência

**Problema.** `OCR_RESIDUAL_SWEEP=True` roda uma varredura Paddle de página inteira em **toda** página (`komyst/ocr/residual_sweep.py`, chamada em `bp` por `sweep_page_residuals`, ~linha 274). Custo observado em REF-A saudável: 98,03 s; poderá variar por capítulo e máquina.

**Como fazer.**

1. Leia `sweep_page_residuals` e `_residual_sweep_known_boxes` inteiros.
2. Antes de chamar o Paddle, calcule um pré-filtro barato **sem modelo**: a página só é varrida se existir região "parecida com texto" **fora** das caixas já conhecidas. Use o estimador que o motor de OCR já tem (`_estimate_text_regions` / `_detect_story_text_region_boxes` em `komyst/ocr/ocr_engine.py`): se o número de regiões de história não cobertas por linhas conhecidas for zero, **pule** a varredura dessa página.
3. Nova configuração `OCR_RESIDUAL_SWEEP_MODE = "evidence"` (valores: `"always"`, `"evidence"`, `"off"`). Padrão `"evidence"`.
4. Conte `residual_sweep_pages_swept` e `residual_sweep_pages_skipped` no relatório de tempo.

**Verificação obrigatória de qualidade.** Rode REF-A e REF-B com `always` e com `evidence` e compare a lista de detecções (`page_state["residual_sweep"]`). **Toda detecção que virou região traduzida com `always` tem que existir com `evidence`.** Se alguma se perder, afrouxe o pré-filtro; não entregue com perda.

**Teste.** `tests/test_residual_sweep_gating.py`: página sem região não coberta → Paddle não é chamado (mock); com região não coberta → é chamado; modo `always` → sempre.

**F2.1 — observabilidade de indisponibilidade do Paddle.** Se o Paddle não puder iniciar, não omita a etapa nem reporte duração residual enganosa: registre `residual_sweep: unavailable`, junto do motivo de falha e sem contabilizar a página como varrida. Inclua teste de inicialização indisponível. No mesmo trabalho, avalie se as páginas a varrer podem ser escolhidas apenas quando houver sinal barato de resíduo, preservando todas as detecções úteis de `always`.

### ⏸ PAUSA 2A (depois de F2.1)

Entregar a comparação `always × evidence` das detecções nos dois capítulos e o tempo da etapa `residual_sweep`. Só siga se **zero** detecções úteis foram perdidas.

### F2.2 Não forçar LaMa quando o preenchimento clássico já serve

**Problema.** Em `ob._apply_cleanup_mask` (~linha 16350), com `CLEAN_COMPARE_FILLS=True` o LaMa é chamado com `force=True` mesmo quando o preenchimento clássico existe. Nos jobs medidos, 53 de 58 regiões terminaram em `local_ring_median`.

**Como fazer.**

1. Leia `_apply_cleanup_mask` inteira e a pontuação de candidatos que vem depois.
2. Só force o candidato LaMa quando o clássico **não** for claramente seguro. Critério de "claramente seguro" (todos verdadeiros): `local_background_class` do grupo em `{"solid_light", "solid_dark"}`; `local_background_luminance_std` ≤ 6; a região não é SFX; o portão de harmônico não rejeitou (`spatial_harmonic_gate_rejected` falso).
3. Coloque o critério numa função pequena `_classic_fill_is_trivially_safe(group, profile) -> bool` e use-a na condição que hoje chama `_learned_texture_fill(..., force=True)`.
4. Conte `lama_compare_skipped` e `lama_compare_run`.

**Verificação obrigatória de qualidade.** Compare, página a página, as imagens limpas (`pages/page_NNN_cleaned.png`) de antes e depois nos dois capítulos. Nenhuma página pode perder o certificado; a contagem de pixels diferentes por página tem que ser listada no relatório.

**Teste.** `tests/test_compare_fills_gating.py`: fundo branco plano → LaMa não é chamado (mock); fundo texturizado → é chamado.

### F2.3 Trabalho repetido

Três correções independentes, um commit cada:

1. **Progresso.** `_write_progress` (`bp` ~7371) re-serializa e faz hash de todos os estados a cada página. Faça cache do JSON por página (chave: índice da página + um contador de versão que sobe quando o estado muda) e só re-serialize a página que mudou. O arquivo final tem que ter o mesmo conteúdo (mesmas chaves e valores).
2. **Validação de PNG.** `_reconstructed_page_is_valid` (`bp` ~433) decodifica origem e saída 4–5 vezes por página. Memorize o resultado por `(caminho, tamanho, mtime)`.
3. **Folha de contato do corte.** É gerada duas vezes no caminho normal (`bp` ~3019–3033). Gere uma vez.

**Teste.** Para (1): teste que chama `_write_progress` duas vezes sem mudança e confere que a serialização da página não foi refeita e que o conteúdo é igual. Para (2): mock de `cv2.imread` conta uma leitura por arquivo.

### F2.4 Rótulo da etapa na tela

**Problema.** Durante os ~130 s do pré-render de layout a tela mostra "tradução".

**Onde.** Onde o progresso é emitido durante o pré-render (`bp`, procure `layout_preflight`) e onde a etapa vira texto (`komyst/ui/ui_bridge.py` e `static/komyst_ui.js`; procure os rótulos de etapa existentes como "Baixando imagens").

**Como fazer.** Emita uma etapa própria (`layout`) com contador de páginas. Rótulo pt-BR: "Montando as páginas". Acrescente nas traduções `static/i18n/*.js`. Atualize o guia do usuário.

**Teste.** Ajuste os testes de rótulo e de estimativa de tempo existentes.

### F2.5 FLUX fora do lock global e com teto menor

**Problema.** `flux_edit.py` roda `sd-cli.exe` segurando `DIRECTML_LOCK` por até 240 s; cada chamada recarrega os modelos.

**Como fazer.**

1. Leia `komyst/core/gpu.py` e `flux_edit.py`. O `sd-cli` usa Vulkan, não DirectML. Dê ao FLUX um lock próprio (`FLUX_LOCK`) em vez do `DIRECTML_LOCK`. A Fase 1 agora vem antes da Fase 2, então a guarda da F1.5 já deverá estar integrada; confirme-a antes de alterar o lock.
2. Nova configuração `GENERATIVE_INPAINT_TIMEOUT_SECONDS = 120` (era 240 fixo) e `GENERATIVE_INPAINT_MAX_CALLS_PER_JOB = 12`. Ao atingir o teto, as regiões seguintes seguem a escada sem FLUX e vão para revisão.
3. Não tente manter o `sd-cli` residente nesta fase (é mudança grande; fica registrado como melhoria futura).

**Teste.** Mock do subprocesso: o 13º pedido não lança processo; o timeout configurado é o passado ao subprocesso.

### F2.6 (Opcional, só com aprovação na PAUSA 2B) Sobrepor download e OCR

`KOMYST_PIPELINE_STREAMING` já existe (padrão desligado) e sobrepõe corte com OCR. Tarefa: medir REF-A com `KOMYST_PIPELINE_STREAMING=1` e relatar tempo e qualidade. **Não mude o padrão** sem aprovação.

### F2.7 (Opcional, só com aprovação na PAUSA 2B) Unificar pré-render e render final

É a mudança de maior risco do plano. Não implemente sem uma proposta escrita aprovada. A proposta deve dizer: em que condição o pré-render é descartado hoje (`_translation_render_signature`), quantas páginas foram reaproveitadas em REF-A e REF-B, e o ganho esperado.

### ⏸ PAUSA 2B

Critérios de aceite:

- [ ] REF-A em Tradução pronta ≤ 300 s; REF-B em Tradução pronta ≤ 420 s.
- [ ] Nenhuma página perdeu o certificado; nenhuma região traduzida a menos.
- [ ] Relatório com o tempo de cada etapa antes × depois (medidor da P.4).
- [ ] Suíte completa verde.

---

## FASE 3 — Qualidade (traduzir e limpar o que falta)

Objetivo em REF-B: regiões traduzidas ≥ 174/177; páginas certificadas ≥ 78/85; portão físico passa. Em REF-A nada regride.

### F3.0 Confirmar testes dependentes do OpenCV e corrigir máscara em texto que toca contorno

O dono informou que três dos quatro testes antigos passam com OpenCV 5.0.0; a sessão confirmou OpenCV 5.0.0 em `python` e `python -s`. Para `test_text_touching_a_balloon_border_is_cleaned_without_erasing_the_border`, o bisect isolado apontou `80f0620` como primeiro commit ruim entre `d819f0e` e `631afac`. Causa: `80f0620` generalizou `_refine_lettering_mask` para todo grupo e a dilatação cega de 2 px aumentou a máscara de 7.285 para 9.940 px, tocando 18 px do arco. Correção aplicada: `_long_stroke_halo_barrier` reutiliza `_balloon_border_mask` e bloqueia somente pixels tão escuros quanto a tinta em traços longos de mesma polaridade; a máscara base permanece intacta. Contrato: halo nunca cresce sobre essa estrutura e pixels já pertencentes à máscara base não são removidos. Validação física do dono: REF-A Apenas Clean pelo painel, job `39a41cbb…`, 65 páginas, FLUX funcionou na p23 e somente p10/p22 ficaram em revisão; REF-B Completo `c7ee941a073945db82a225d48a435c48`, 480,6 s, 169/177 traduções, 70/85 certificados e os mesmos 7 resíduos da base. REF-A saudável levou aproximadamente 330 s com Paddle funcionando; os tempos antigos 288,7 s (Clean) e 278,2 s (Tradução pronta) são medições degradadas, com Paddle indisponível e sweep silenciosamente pulado. Verificação final em Python 3.11, OpenCV 5.0.0 e DirectML: suíte completa **6.504 passed, 141 skipped, 1 xfailed, 8 warnings, 787 subtests**, 883,71 s; teste específico da borda **1 passed**. F3.0 fechada offline e fisicamente.

Para cada um dos três testes dependentes do OpenCV:

1. Descubra em qual commit a falha começou, fazendo bisect entre `d819f0e` e `cda3f90`.
2. Classifique a causa como regressão de código ou teste desatualizado.
3. Corrija a causa, preservando os contratos de máscara, proteção da arte e reconstrução.

**Aceite.** Suíte completa verde, com zero falhas.

### F3.1 Fala classificada como decorativa

**Problema.** Texto de história fica em inglês porque foi classificado `decorative` ou `unknown` e ignorado: "PFFT. HOW CUTE,", "CALLING THE CEO", "LOL! GOOD LUCK.".

**Onde.** `ob`: `_decorative_textured_story_promotion_allowed`, `_decorative_short_display_story_promotion_allowed`, `_apply_classification_policy`; `komyst/review/region_taxonomy.py`: `weak_label_semantic_promotion_allowed`.

**Como fazer.**

1. Para cada item ignorado de REF-B com `ignore_reason` em `{"decorative_text", "weak_unknown_text"}`, registre no relatório: texto, confiança, `background_type`, número de palavras de dicionário, pontuação. (Leia de `progress.json` → `pages[].debug_data.items[]`.)
2. Regra nova: a promoção de rótulos fracos exige evidência estrutural coerente de balão/caixa de narração. O vínculo (`inside_balloon_like_region`, `inside_narration_box_like_region` ou `parent_balloon_id`) deve concordar com a classificação local do fundo (`white_balloon`, `dark_balloon` ou `narration_box`); flag isolada pode ser herdada de uma região vizinha. Uma forma visualmente fechada sozinha não basta: placas e objetos da cena também podem ter contorno. Dentro de contêiner, manter os critérios de texto: confiança de OCR ≥ 0,90; ≥ 2 palavras; **todas** as palavras com ≥ 3 letras são palavras do dicionário inglês (`region_taxonomy.is_english_word`) depois de separar palavras coladas (F3.2); o texto tem pontuação de frase (`. , ! ?`) **ou** ≥ 3 palavras; não é crédito, URL nem título da série.
3. Uma palavra só (por exemplo "FROWN", "CLUNK") **não** é promovida por esta regra: é som ou ação e segue a política de SFX.
4. Implemente como uma função nova `_legible_sentence_promotion_allowed(group)`, integrada à política final e às verificações de autoridade de tradução. A exigência estrutural vale apenas para esse caminho novo; não afrouxe nem bloqueie as rotas antigas de recuperação.

**Teste.** `tests/test_legible_sentence_promotion.py`: letreiro legível em arte, inclusive com flag de narração herdada mas fundo `textured_art`, limpeza local difícil e sem fallback remoto → preservado; frase legível de 3 palavras em caixa de narração → promovida; uma palavra → não; confiança 0,8 → não; palavra fora do dicionário → não; texto de crédito → não.

**Resultado F3.1 (2026-11-13).** Ganho líquido medido: zero traduções adicionais nos capítulos de referência. REF-B manteve 169/177 traduções, 70/85 certificados, as mesmas 15 páginas em revisão e os mesmos 7 resíduos; a placa da p20 ficou preservada. REF-A manteve 57/58 traduções. A finalidade da mudança é impedir regressão de arte e deixar a promoção estrutural pronta para a F3.2, que trata palavras coladas pelo OCR. Código/testes em `7933f64`; validação de qualidade e suíte no relatório F3.1.

### F3.2 Palavras coladas pelo OCR

**Problema.** "ONELEAD'S", "MAKETHE", "WITHMEIFYOUSTILL", "THECEO" derrubam tradução e prova de completude.

**Onde.** `region_taxonomy.segment_words`, `ob.split_glued_source_words` (procure os dois).

**Como fazer.**

1. Leia como `split_glued_source_words` decide separar e por que esses quatro casos não foram separados (rode a função neles num script de rascunho, fora do repositório).
2. Corrija a causa encontrada. Restrições: só separar quando **todas** as partes resultantes forem palavras do dicionário; nunca separar um token que já é palavra do dicionário; nunca separar nome detectado do capítulo (`protected`).
3. A prova de completude (`source_completeness`, `missing_tokens`) deve comparar pelo texto **compactado** (sem espaços), para que "WITH ME IF YOU STILL" cubra "WITHMEIFYOUSTILL". Localize onde `missing_tokens` é calculado (`komyst/ocr/source_completeness.py`).

**Teste.** Casos acima em `tests/test_region_taxonomy.py` e um teste de completude com token colado.

### ⏸ PAUSA 3A (depois de F3.1 e F3.2)

Entregar: lista, para REF-A e REF-B, de **toda** região que mudou de "ignorada" para "traduzida", com texto original e tradução. O dono lê a lista e confirma que nada foi traduzido indevidamente (logo, placa, SFX). Só siga com a aprovação.

### F3.3 Onomatopeia em balão de fala tratada como nome próprio

**Problema.** "SLIP", "WAAAH" em balão terminaram `preserved_original / proper_name_only`.

**Como fazer.** Em `ob`, onde `PROPER_NAME_ONLY_REASON` é aplicado (`_finalize_proper_name_only` e chamadores): antes de concluir "é só nome próprio", se o texto for uma única palavra que (a) existe no glossário de SFX (`assets/lexicon/sfx_en_pt.json`, via `komyst/translation/sfx_glossary.py`) ou (b) é palavra do dicionário inglês e **não** está em `detected_proper_names`, então não é nome: siga a política de SFX (glossário quando "traduzir SFX" está ligado; preservar como SFX quando desligado, com disposição `PRESERVE_SFX`).

**Teste.** Palavra de glossário em balão → não vira `proper_name_only`; nome detectado do capítulo → continua `proper_name_only`.

### F3.4 Cobertura incompleta do balão (português com inglês sobrando)

**Problema.** 5 casos em REF-B (`incomplete_region_coverage`).

**Como fazer.**

1. Para cada violação (`physical_incomplete_region_coverage_details` no relatório de qualidade), registre: página, id renderizado, id residual, texto residual.
2. Classifique cada uma: (a) resíduo é linha do mesmo balão que não entrou no grupo; (b) resíduo é outro balão encostado; (c) resíduo é ruído de OCR.
3. Corrija só a classe com mais casos, na origem (agrupamento de linhas para (a)). Se os cinco casos forem de classes diferentes, PARE e reporte a tabela; não implemente cinco correções.

### F3.5 Regiões `LOCAL_HARD`

**Problema.** 7 regiões em REF-B ficaram `LOCAL_HARD: remote_fallback_disabled_or_not_configured`.

**Como fazer.** Verifique, com o FLUX local habilitado (`GENERATIVE_INPAINT_ENABLED=1`), se `_advanced_art_fallback_eligible` (`ob`) aceita essas regiões. Registre, para cada uma, qual condição de elegibilidade falhou. **Só relatório nesta tarefa**; a mudança de elegibilidade é decidida na PAUSA 3B.

### ⏸ PAUSA 3B

Critérios de aceite:

- [ ] REF-B: ≥ 174/177 traduzidas; ≥ 78/85 páginas certificadas; portão físico passa.
- [ ] REF-A: nenhuma métrica da seção 2.2 pior.
- [ ] Tempo total não pior que o medido na PAUSA 0, com tolerância de 10%.
- [ ] Suíte completa verde.

---

## FASE 4 — Entrega enxuta por modo

Objetivo: depois que o job termina com sucesso, a pasta do usuário contém só o que ele pediu.

### F4.1 Mapa de entregáveis

Use `plan_artifact_types` (`komyst/runtime/output_plan.py`), que já mapeia operações → artefatos.

| Modo | Fica na pasta |
|---|---|
| Tradução pronta | o PDF |
| Apenas Clean | as imagens limpas |
| Tradução + Clean | imagens limpas + `traducao.json` + `traducao.txt` |
| Apenas tradução | `traducao.json` + `traducao.txt` (original e tradução lado a lado) |
| Completo | PDF, imagens limpas, PSD, relatório de qualidade, manifesto de revisão |
| Personalizado | só os artefatos das operações marcadas |

### F4.2 Implementação

1. Novo módulo `komyst/runtime/delivery.py` com `finalize_delivery(output_dir, plan, job_status)`.
2. **Só roda** quando o status final é `completed`. Em `review_required`, `failed`, `interrupted` ou cancelado, **não apaga nada** (é o que permite revisar, reexportar e retomar).
3. Os arquivos de controle de crédito (`translation_ready.json`, `yk_reservation.json`) **não podem ser apagados** enquanto o runner ainda os consulta. Antes de implementar, liste quem lê cada um (`grep -rn "translation_ready\|yk_reservation" Komyst`). Mova-os para `%LOCALAPPDATA%\Komyst\runtime\job_state\<job_id>\` e ajuste os leitores. Se o ajuste tocar mais de três funções, PARE e reporte.
4. Configuração `KEEP_WORK_FILES = _env_bool("KEEP_WORK_FILES", False)` e uma caixa "Manter arquivos de trabalho" na tela (desmarcada por padrão).
5. `traducao.txt`: uma região por bloco — página, original, tradução. Gerado a partir do mesmo dado de `_build_translation_only_manifest` (`bp`).
6. Atualize o guia do usuário (local e nome dos arquivos de saída) e a doc técnica.

**Teste.** `tests/test_delivery_by_mode.py`: para cada modo, árvore falsa completa → conteúdo exato esperado; status diferente de `completed` → nada apagado; `KEEP_WORK_FILES=True` → nada apagado.

### ⏸ PAUSA 4

- [ ] Em cada modo, a pasta final contém exatamente a tabela da F4.1.
- [ ] Job `review_required` mantém tudo e a reexportação pela tela continua funcionando.
- [ ] Nenhuma cobrança dupla de tradução ao reprocessar o mesmo capítulo (conferir saldo antes e depois com o dono).
- [ ] Novo MB/página por modo medido e anotado.

---

## FASE 5 — Perfis de hardware e métricas na documentação

### F5.1 Três perfis

Novo módulo `komyst/runtime/hardware_profile.py`: `detect() -> dict` (RAM total e livre via psutil; GPU e VRAM via o diagnóstico que já existe em `resource_monitor.detect_gpu_basic`) e `select_profile(detected, override) -> str`.

| Configuração | Leve | Equilibrado | Qualidade |
|---|---|---|---|
| Escolha automática | RAM < 12 GB ou sem GPU dedicada | 12–24 GB e GPU ≥ 4 GB | ≥ 24 GB e GPU ≥ 8 GB |
| `PIPELINE_PAGE_WORKERS` | 1 | 2 | auto |
| `OCR_RESIDUAL_SWEEP_MODE` | off | evidence | evidence |
| `CLEAN_COMPARE_FILLS` | False | True | True |
| `ADVANCED_ART_INPAINTING` (LaMa) | True (CPU, último recurso) | True | True |
| `GENERATIVE_INPAINT_ENABLED` (FLUX) | False | False | conforme o usuário |

Regras: variável de ambiente explícita sempre vence o perfil; `HARDWARE_PROFILE=auto|leve|equilibrado|qualidade` (padrão `auto`); o perfil escolhido e o motivo vão para o relatório de tempo e para o log do job.

**Teste.** `tests/test_hardware_profile.py`: tabela de detecções simuladas → perfil esperado; override manual vence; variável explícita vence o perfil.

### F5.2 Medir

Rodar REF-A e REF-B **forçando** cada perfil (`HARDWARE_PROFILE=leve` etc.) na máquina de referência e registrar, por perfil: tempo total, pico de RAM, pico de VRAM (quando medido), MB em disco por página, métricas de qualidade. Deixe claro no documento que "Leve" e "Equilibrado" foram **simulados** numa máquina maior, não medidos em hardware fraco.

### F5.3 Documentar

- `docs/HARDWARE_PROFILE.md`: tabela por perfil com os números da F5.2; armazenamento por modo (linha de base da seção 2.3 e o valor novo após a Fase 4); espaço da instalação (modelos, cache, runtime).
- `docs/user/GUIA_DO_USUARIO.md`: requisitos em linguagem simples e "quanto espaço cada capítulo ocupa".
- `README.md`: resumo de três linhas com link.
- Classifique cada número como **MEDIDO** (com data e máquina) ou **ESTIMADO**. Nunca escreva requisito mínimo como homologado se não foi medido em hardware daquele porte.

### ⏸ PAUSA 5

- [ ] Perfil automático escolhe "Qualidade" na máquina de referência.
- [ ] Tabela de métricas por perfil completa, com MEDIDO/ESTIMADO.
- [ ] Qualidade no perfil "Equilibrado" não é pior que a da PAUSA 3B em páginas certificadas (tolerância: −2 páginas).

---

## FASE 6 — Nome "Komyst" e documentação legada

### F6.1 Auditoria da identidade interna

Pacote Python, variáveis de ambiente, identidade de atualização, namespace de UUID e pasta de dados usam a identidade Komyst aprovada pelo dono, sem camada de compatibilidade ou migração. Verifique imports, chamadas de módulo, testes, configuração, instalador e updater; preserve somente integrações externas reais documentadas em `docs/BRANDING.md`.

### F6.2 Identidade visível ao usuário

README, callbacks, títulos de janela, relatórios, mensagens e instalador devem exibir Komyst. Os nomes existentes dos arquivos de entrada técnica podem permanecer quando forem dependências internas ainda usadas; não os apresente como nome do produto.

### F6.3 Repositório e serviços externos

- Instruções de desenvolvimento apontam para `https://github.com/HenriquePvAr/Komyst.git`.
- Não altere o endpoint de manifesto do canal de atualização nem domínios de serviços externos nesta tarefa.

### F6.4 Documentação e histórico

1. Atualize o guia do usuário e a documentação técnica para instalador, licença Beta, instalação limpa e atualização. Para a validação do beta tester, declare uma única vez por documento: “A instalação limpa em Windows foi validada por um beta tester com a `v0.9.1-beta.18` (data não registrada).” Não repita a atribuição nem escreva em primeira pessoa.
2. Remova snapshots de estado com SHA/data antigos; use código atual e proveniência de validação.
3. Remova pelo Git os relatórios históricos de tarefa obsoletos; não apague artefatos não rastreados nem dados fora do repositório.
4. Corrija links relativos e valide `docs/status/board/board.js` sem duplicar ids nem quebrar referências.

### ⏸ PAUSA 6 (final)

- [ ] Marcas visíveis em `static/`, `ui/`, `docs/user/` e `README.md` usam Komyst; exceções externas estão listadas em `docs/BRANDING.md`.
- [ ] Verificador de links sem erros.
- [ ] Testes de imports, updater, licença e empacotamento passam; qualquer validação física pendente fica marcada como gate externo.
- [ ] Suíte completa verde.

---

## 3. Resumo das pausas

| Pausa | Depois de | O que o revisor decide |
|---|---|---|
| P | Preparação | Como commitar a árvore de trabalho; levar a branch atual para `dev` |
| 0 | Jobs não morrem mais | Merge da Fase 0 |
| 3A | Promoção de fala e palavras coladas | Lista do que passou a ser traduzido está correta? |
| 3B | Qualidade | Merge da Fase 3; decide elegibilidade do FLUX para `LOCAL_HARD` |
| 1 | Memória | Merge da Fase 1 |
| 2A | Varredura por evidência | Nenhuma detecção útil perdida? |
| 2B | Tempo | Merge da Fase 2; autoriza ou não F2.6 e F2.7 |
| 4 | Entrega enxuta | Merge da Fase 4 |
| 5 | Perfis e métricas | Merge da Fase 5 |
| 6 | Nome e docs | Merge final; decide merge em `main` |

## 4. O que este plano não cobre

- Manter o FLUX residente em memória (ganho provável, mudança grande).
- Identidade exata de fonte com o original (avaliado em 2026-11-03: nenhuma fonte livre reproduz o letreiramento original).
- Validação em hardware fraco de verdade: a Fase 5 simula os perfis numa máquina de 32 GB.
- Instalador e interface do atualizador.
