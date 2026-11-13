# Validação F0.8/F0.9 — REF-A Apenas Clean

Data: 2026-11-11  
Branch: `fase-0-jobs-nao-morrem`  
Capítulo: REF-A — Hero Killer, episódio 285  
Método: linha de comando, sem tradução; `TRANSLATION_ENABLED=false`, `TRANSLATE_SFX=false`, modo Quality, force, sem contexto, typesetting off, saída PNG. O intervalo de monitor foi definido somente no processo da segunda execução; nenhum `.env` foi alterado.

## Execuções

| Run | Intervalo | Tempo total | Tempo de inpainting | Amostras | Tempo em amostragem | Custo | Imagens | Certificados |
|---|---:|---:|---:|---:|---:|---:|---:|---|
| `fase0-f09-clean-20261111-151428` | 5 s | 433,888 s | 224,043 s | 83 | 9,243 s | 2,13% | 65 | 64 PASS, 1 REVIEW_REQUIRED |
| `fase0-f09-clean-10s-20261111` | 10 s | 384,824 s | 221,516 s | 38 | 4,117 s | 1,07% | 65 | 64 PASS, 1 REVIEW_REQUIRED |

O custo é calculado diretamente como `resource_monitoring.sampling_seconds / total_seconds`. A diferença de duração total entre as duas execuções não é usada como medida do custo do monitor, pois download, CPU concorrente e variação natural do pipeline diferem.

## Qualidade e dispositivos

- O log da segunda execução contém `Inicializando RapidOCR / ONNX Runtime (GPU DirectML)...`.
- `timing_report.json` registra OCR e LaMa efetivos como `directml`; LaMa teve 46 chamadas DirectML e nenhuma indicação de fallback.
- As 65 imagens finais de `images/translated/` nas duas execuções são pixel a pixel idênticas.
- Ambas tiveram certificados idênticos: 64 `PASS`; página 10 `REVIEW_REQUIRED` por `unresolved_clean_regions`. Portanto, 65 PNGs foram produzidos, mas não se declara que todas as páginas estejam limpas/certificadas: a p010 continua para revisão.
- Segunda execução: pico de RSS da árvore de processos 8.447,20 MB, pico do processo principal 4.087,09 MB, pico dos filhos 4.579,63 MB; pico de RAM usada pelo sistema 27.375,65 MB e pico de swap 1.168,93 MB. VRAM não foi medida pelo monitor.
- O job terminou `review_required`, não `failed`; PDF e conjunto PNG foram gerados. Esta execução foi por CLI e não comprova a correção do cartão/histórico pela interface.

## Intervalo aplicado

10 s ficou abaixo da meta de 2% com 1,07% medido. O padrão do código e `.env.example` foi alterado para 10 s. O dono confirmou que o `.env` local tem uma única entrada `RESOURCE_MONITOR_INTERVAL_SECONDS` na linha 79 e vai alterá-la para 10 s; o arquivo não foi modificado por nós. Para a interface adotar o intervalo medido, reinicie app/worker após a alteração e confirme `interval_seconds: 10.0` no relatório.

## Suíte completa

Com o snapshot do código já usando intervalo padrão de 10 s: **6.497 passaram, 4 falharam, 141 foram ignorados, 1 xfailed, 8 warnings e 787 subtests passaram**, em 1.015,71 s. As quatro falhas são as antigas de máscara/reconstrução registradas em `reports/falhas_preexistentes_20261111.md`; nenhuma falha nova apareceu.

## Controle na base `dev` — página 10

Foi executado REF-A Apenas Clean em worktree isolada no commit `7879bad275bcf4151117fd3d96f982ddba2c9fd1`, importando `Komyst` da própria worktree. Opções idênticas: tradução e SFX desligados, modo Quality, force, sem contexto, typesetting off, PNG, monitor no processo em 10 s.

| Execução | Tempo total* | Inpainting | PNGs | Certificados | Pág. 10 |
|---|---:|---:|---:|---|---|
| `dev` `7879bad` (`fase0-base-dev-refa-clean-7879bad-20261111`) | 341,192 s | 222,401 s | 65 | 63 PASS, 2 REVIEW_REQUIRED (p010, p023) | `REVIEW_REQUIRED`, `unresolved_clean_regions` |
| Fase 0 (`fase0-f09-clean-10s-20261111`) | 384,824 s | 221,516 s | 65 | 64 PASS, 1 REVIEW_REQUIRED (p010) | `REVIEW_REQUIRED`, `unresolved_clean_regions` |

\* Os tempos são informativos; a versão `7879bad` não tem a telemetria de custo/dispositivo adicionada depois, então não são usados para atribuir velocidade nem custo do monitor.

Os estados de certificado diferem somente na página 23 (`dev`: REVIEW_REQUIRED; Fase 0: PASS). Para p010, ambos têm `clean_execution_status=EXECUTION_COMPLETED`, `clean_produced=true`, `clean_verified=false`, motivo `unresolved_clean_regions` e certificado `REVIEW_REQUIRED`. As imagens finais da p010 têm o mesmo tamanho e são pixel a pixel idênticas. Assim, a pendência da página 10 já existe na `dev` e não é regressão da Fase 0; registrar para a Fase 3. Nesta comparação, a Fase 0 não perdeu certificado; a p023 passou nela.

O `timing_report.json` antigo da `dev` não contém `inference_devices`; o provider DirectML está disponível no ambiente, mas não alegamos uso efetivo nem usamos o tempo comparativamente sem a linha de log do dispositivo.

## Estado do F0.9 físico

Os testes simulados de F0.9 confirmam a gravação das últimas 40 linhas do stderr, o motivo real, retry único para `output_or_process_failure`, ausência de retry para `device_memory` e fallback LaMa após duas falhas. O job Clean não exercitou falha real do FLUX. A página 23 precisa ser verificada no REF-A `Tradução pronta` iniciado pelo dono; se o FLUX falhar, conferir `errors/flux_<página>_<região>.log`.

## DOCUMENTATION IMPACT

- Plano: custo medido, intervalo padrão e evidência parcial F0.9 registrados.
- Quadro: estado físico e bloqueios atualizados.
- Obsidian: notas de Estado e Métricas atualizadas com a comparação contra `dev`.
- Pendências físicas: F0.8 via interface e REF-A pago `Tradução pronta`/página 23.
- Publicação: nenhuma; sem merge ou push.


## Fechamento da PAUSA 0 — 2026-11-11

### Tabela antes × depois

| Capítulo / evidência | Tempo total | Traduzidas / detectadas | Certificados de limpeza | Pico RSS da árvore | Gate físico / resíduos | Resultado |
|---|---:|---:|---:|---:|---|---|
| REF-A base `f181a17e` (valores históricos da seção 2; diretório de saída não está mais presente) | 535,00 s | 57 / 58 | 62 / 65 | não medido por job | passou / 0 | `review_required` |
| REF-A Fase 0, job `abee1571` (medidor lido agora) | 377,904 s | 57 / 58 | 62 / 65 | 8.901,411 MB | passou / 0 | `review_required` |
| REF-A Apenas Clean, job final `5dae49f7` (`8791609`) | 477,645 s | não se aplica | 64 / 65 | 8.461,906 MB | não se aplica | `review_required`, 65/65 PNGs |
| REF-B base `278c2486` (medidor) | 641,260 s | 169 / 177 | 70 / 85 | não medido | reprovou / 7 | `failed` (`translation_policy_violation`) |
| REF-B Fase 0, job `432b35af` (medidor) | 599,511 s | 169 / 177 | 70 / 85 | 3.230,395 MB | reprovou / 7 | `review_required` |

No job Clean `5dae49f7`, `timing_report.json` registra 46 amostras, intervalo de 10,0 s e 23,600 s dentro do monitor (4,94% do tempo total). O pico de RSS da árvore foi 8.461,906 MB. Essa medição observada fica acima da comparação anterior de 1,07%; preservo ambos os resultados conforme cada execução, sem atribuir a diferença a uma mudança de código.

O REF-A manteve cobertura, certificados e gate físico e reduziu o tempo reportado de 535 s para 377,90 s. O artefato de saída da base `f181a17e` não existe mais no caminho registrado pelo banco; para o “antes”, os números de qualidade/tempo são os da linha de base previamente documentada, não uma nova comparação direta do medidor. O REF-B preservou as contagens reais: `job_metrics.py --compare` mediu 70/85 certificados nos dois artefatos e os mesmos 7 resíduos; a gravidade melhorou de `ERROR` para `REVIEW`, e o tempo caiu 41,75 s. Relatos anteriores neste repositório de 69 certificados no REF-B estavam incorretos; prevalece a contagem auditada no `timing_report.json`/`artifact_manifest.json` e pelo medidor.

### F0.8 — resultado pelo painel e proveniência do código

O job anterior `5731a21a…` (`bc02f38`) não provava o snapshot final. Essa lacuna foi fechada pelo job `5dae49f7326b4c56b0c0e0731ec6b253`, executado no painel com commit `8791609`: `review_required`, 65/65 imagens limpas entregues, DirectML. O worker registrado foi PID `36048`, executável `C:\Users\henri\AppData\Local\Programs\Python\Python311\pythonw.exe`. O `timing_report.json` histórico não continha ainda o campo `runtime_environment`; a versão importada nessa execução é atribuída ao mesmo interpretador Python 3.11, cuja resolução atual foi conferida como OpenCV 4.10.0 no caminho global abaixo. A telemetria adicionada agora passa a registrar versão e caminho em novos relatórios. Isto fecha a prova física da F0.8 no código final.

O job pago REF-A `abee15719bd346bc86197faaf9307d43` tem proveniência `6c4734b`, terminou `review_required` em 377,904 s, com 57/58 traduzidas, 62/65 certificados e gate físico aprovado, zero resíduos. Página 23: FLUX `ok` em 20,45 s, uma tentativa, sem log de falha. Ele valida o caminho Tradução pronta; não exercita a exceção de Apenas Clean.

### Fase 0 — suíte e falhas antigas

A suíte completa local anterior importou `Komyst` deste repositório em Python 3.11/OpenCV 4.10.0/NumPy 2.3.5 e deu 6.499 passed, 4 failed, 141 skipped, 1 xfailed, 8 warnings e 787 subtests. O dono confirmou que, com OpenCV 5.0.0 do ambiente de referência, três falhas de máscara passam e resta uma falha real. Portanto as medições locais de suíte e os testes individuais que usaram OpenCV 4.10.0 devem ser lidos como resultados do ambiente divergente, não como quatro falhas de código. A lista e a classificação atualizadas estão em `reports/falhas_preexistentes_20261111.md`; a F3.0 mantém uma falha real para bisectar/corrigir.

### Versão do OpenCV no runtime

Os comandos `python -c "import cv2;print(cv2.__version__, cv2.__file__)"` e `python -s -c ...` retornaram ambos `4.10.0 C:\Users\henri\AppData\Local\Programs\Python\Python311\Lib\site-packages\cv2\__init__.py`. O worker do job `5dae49f7` era `pythonw.exe` do mesmo diretório Python311 (PID 36048), então sua resolução de pacotes corresponde a esse ambiente; o artefato antigo não gravou `cv2` diretamente, logo essa identificação é inferida pelo executável e pela instalação atual, não lida do log do job. Para fechar essa lacuna futura, o timing report agora registra executável Python, versão e caminho de `cv2`, e `job_metrics.py` exibe os dados. Não foi instalado nem removido pacote.

As rodadas por CLI deste relatório — REF-A Fase 0 (`384,824 s`), controle `dev` (`341,192 s`) e medições de inpainting/certificados/pixels associadas — foram executadas pelo Python 3.11 global e usaram OpenCV 4.10.0. Estão marcadas como runtime divergente; não usar esses números para comparar velocidade ou atribuir qualidade entre branches até reexecutar sob OpenCV 5.0.0. Os artefatos físicos de painel não são medições CLI e permanecem evidência própria; o job `5dae49f7` tem OpenCV inferido pelo executável do worker, sem registro direto no timing report antigo.

### Estado dos critérios da pausa

| Critério | Evidência desta revisão | Estado |
|---|---|---|
| REF-B não termina `failed` | `review_required`; mesmos 169/177, 70/85, 7 resíduos | Atendido |
| Pico de RAM registrado nos dois capítulos | Medidor contém recursos nos jobs de referência Fase 0 | Atendido |
| Qualidade igual ou melhor | REF-A igual; REF-B mesmas contagens auditadas, sem mudança nos resíduos | Atendido, observada a discrepância histórica de contagem 69/70 resolvida pelo artefato |
| F0.8 físico no código final | Job `5dae49f7`, commit `8791609`, painel, 65/65 imagens, DirectML | Atendido |
| Suíte completa no runtime OpenCV de referência | Dono confirma três testes passam com OpenCV 5.0.0; uma falha real permanece para F3.0 | Fase 0 pronta; suíte completa verde segue como aceite da Fase 3 |

A PAUSA 0 está documentada e a Fase 0 está pronta para revisão/merge em `dev`, conforme a decisão do dono. Uma falha real preexistente de máscara segue para F3.0; os três resultados extras locais são dependentes do OpenCV 4.10.0 divergente. Nenhum merge ou push foi feito; aguardo aprovação explícita.

## DOCUMENTATION IMPACT

- Atualizados plano de execução, relatório da Fase 0, registro das falhas antigas, quadro e notas Obsidian de Status/Qualidade.
- F0.8 é `PHYSICALLY_VERIFIED` no job REF-A Apenas Clean `5dae49f7` em `8791609`; REF-A Tradução pronta também é `PHYSICALLY_VERIFIED` no job `abee1571`.
- Base `f181a17e` não está no disco no caminho registrado; comparação REF-A antes usa a linha de base documentada. REF-B foi reextraído diretamente dos dois artefatos com `job_metrics.py`.
- F3.0 permanece aberta para a única falha real. Nenhum merge, push, mudança em `.env` ou instalação/remoção de pacote foi realizado.
