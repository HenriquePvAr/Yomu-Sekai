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

Foi executado REF-A Apenas Clean em worktree isolada no commit `7879bad275bcf4151117fd3d96f982ddba2c9fd1`, importando `yomu` da própria worktree. Opções idênticas: tradução e SFX desligados, modo Quality, force, sem contexto, typesetting off, PNG, monitor no processo em 10 s.

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

| Capítulo / evidência | Tempo total | Traduzidas / detectadas | Certificados de limpeza | Gate físico / resíduos | Resultado |
|---|---:|---:|---:|---|---|
| REF-A base `f181a17e` (valores históricos da seção 2; diretório de saída não está mais presente) | 535,00 s | 57 / 58 | 62 / 65 | passou / 0 | `review_required` |
| REF-A Fase 0, job `abee1571` (medidor lido agora) | 377,904 s | 57 / 58 | 62 / 65 | passou / 0 | `review_required` |
| REF-B base `278c2486` (medidor) | 641,260 s | 169 / 177 | 70 / 85 | reprovou / 7 | `failed` (`translation_policy_violation`) |
| REF-B Fase 0, job `432b35af` (medidor) | 599,511 s | 169 / 177 | 70 / 85 | reprovou / 7 | `review_required` |

O REF-A manteve cobertura, certificados e gate físico e reduziu o tempo reportado de 535 s para 377,90 s. O artefato de saída da base `f181a17e` não existe mais no caminho registrado pelo banco; para o “antes”, os números de qualidade/tempo são os da linha de base previamente documentada, não uma nova comparação direta do medidor. O REF-B preservou as contagens reais: `job_metrics.py --compare` mediu 70/85 certificados nos dois artefatos e os mesmos 7 resíduos; a gravidade melhorou de `ERROR` para `REVIEW`, e o tempo caiu 41,75 s. Relatos anteriores neste repositório de 69 certificados no REF-B estavam incorretos; prevalece a contagem auditada no `timing_report.json`/`artifact_manifest.json` e pelo medidor.

### F0.8 — resultado pelo painel e proveniência do código

O job `5731a21a89184e07b319041f1ee46aa2` (`run_id=65c904fa-250b-4bb8-830f-f033c2ea7c19`) entregou 65/65 imagens limpas, `review_required`, cartão “concluído — revisão recomendada”, DirectML e 4,35 s de amostragem em 404,26 s (1,08%). Porém, o banco de jobs e o `run_manifest.json` identificam esse job com o commit **`bc02f38`**, anterior à correção `6c4734b`. Portanto ele comprova o resultado desse run, mas não é validação física da correção unificada final. A exceção F0.8 passa a ser usada por todos os sete pontos via `_page_output_is_valid`; os testes focados adicionados cobrem a ordem do worker e a centralização. Falta um Apenas Clean físico no painel cuja proveniência seja `6c4734b` ou descendente para fechar esse aceite estritamente no snapshot final.

O job pago REF-A `abee15719bd346bc86197faaf9307d43` tem proveniência `6c4734b`, terminou `review_required` em 377,904 s, com 57/58 traduzidas, 62/65 certificados e gate físico aprovado, zero resíduos. Página 23: FLUX `ok` em 20,45 s, uma tentativa, sem log de falha. Ele valida o caminho Tradução pronta; não exercita a exceção de Apenas Clean.

### Fase 0 — suíte e falhas antigas

A suíte completa recém-executada nesta checkout importou `yomu` de `C:\Projetos\Yomu-Sekai\yomu` usando Python 3.11, OpenCV 4.10.0 e NumPy 2.3.5: **6.499 passed, 4 failed, 141 skipped, 1 xfailed, 8 warnings e 787 subtests passed**, em 917,27 s. Os quatro testes listados em `reports/falhas_preexistentes_20261111.md` falharam também ao rodar individualmente. Eles usam fixtures sintéticos e não leem PNGs soltos; a execução isolada exclui ordem da suíte. Os arquivos de máscara/testes são idênticos em `bc02f38` e no HEAD. Assim, não confirmamos o resumo externo (6.502/1) nem a afirmação de que três passam em `bc02f38`; diferença de ambiente/importação é hipótese, não causa demonstrada. A F3.0 continua necessária.

### Estado dos critérios da pausa

| Critério | Evidência desta revisão | Estado |
|---|---|---|
| REF-B não termina `failed` | `review_required`; mesmos 169/177, 70/85, 7 resíduos | Atendido |
| Pico de RAM registrado nos dois capítulos | Medidor contém recursos nos jobs de referência Fase 0 | Atendido |
| Qualidade igual ou melhor | REF-A igual; REF-B mesmas contagens auditadas, sem mudança nos resíduos | Atendido, observada a discrepância histórica de contagem 69/70 resolvida pelo artefato |
| F0.8 físico no código final | Job Clean bem sucedido, mas manifestado em `bc02f38`, não `6c4734b` | Não comprovado no snapshot final |
| Suíte completa verde | 4 falhas reproduzidas nesta execução | Não atendido |

A PAUSA 0 está documentada, mas não considero os gates de merge atendidos: a suíte está vermelha nesta checkout e o job Clean do painel não traz a correção `6c4734b`. Não fiz merge nem push. Após a decisão do dono, a F3.0 continua sendo o próximo trabalho de código previsto; não iniciar antes da aprovação do merge.

## DOCUMENTATION IMPACT

- Atualizados plano de execução, relatório da Fase 0, registro das falhas antigas, quadro e notas Obsidian de Status/Qualidade.
- O relatório diferencia `PHYSICALLY_VERIFIED` no job REF-A Tradução pronta de `TESTED_OFFLINE` para a exceção F0.8; o job Clean disponível é anterior ao commit `6c4734b`.
- Base `f181a17e` não está no disco no caminho registrado; comparação REF-A antes usa a linha de base documentada. REF-B foi reextraído diretamente dos dois artefatos com `job_metrics.py`.
- Fase 3/F3.0 e aceite físico Clean no hash final permanecem abertos. Nenhum merge, push, mudança em `.env` ou alteração de comportamento adicional foi realizado.
