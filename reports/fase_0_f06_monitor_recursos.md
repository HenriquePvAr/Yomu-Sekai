# F0.6 — Monitoramento de recursos

Data: 2026-11-11  
Escopo: coleta no runner, inclusão no `timing_report.json` e escrita dos artefatos de recursos.

## Implementado

- `RESOURCE_MONITORING` passa a iniciar como `True` quando não há override de ambiente.
- O `.env.local` não define intervalo próprio; o padrão de código é o valor efetivo desta branch. Não alterei configurações secretas nem credenciais locais.
- `psutil` já consta em `requirements.txt`; nenhuma dependência foi adicionada.
- O pipeline já incluía o resumo retornado pelo monitor em `timing_report.json` sob `resource_monitoring`. O resumo registra pico da árvore do processo (pai + filhos), RSS do processo e filhos, uso/percentual de RAM do sistema e uso de swap.
- O monitor grava JSON e CSV por padrão. HTML agora é opt-in (`generate_html=True`), e seu caminho fica vazio no resumo quando desativado.
- Intervalo padrão ajustado de 1 para 5 segundos para reduzir o custo de amostragem. O resumo registra `interval_seconds`; o ganho ainda precisa ser medido fisicamente em condições equivalentes.

## Evidência offline

Comandos executados:

```text
python -m pytest -q -p no:cacheprovider tests/test_resource_monitor.py tests/test_subprocess_ocr.py
14 passed in 2.55s

python -c "from yomu.config import settings; print({'resource_monitoring_enabled': settings.RESOURCE_MONITORING, 'interval_seconds': settings.RESOURCE_MONITOR_INTERVAL_SECONDS})"
{'resource_monitoring_enabled': True, 'interval_seconds': 5.0}
```

O teste valida pico de RSS combinado, uso máximo de RAM e swap, JSON/CSV padrão, ausência do HTML e geração HTML explicitamente solicitada. Isso é `TESTED_OFFLINE`, não comprova consumo/custo em job físico.

A suíte completa foi executada novamente em 2026-11-11, depois das alterações locais de F0.1, F0.6 e F0.7:

```text
4 failed, 6486 passed, 141 skipped, 1 xfailed, 8 warnings,
787 subtests passed in 942.84s
```

As quatro falhas foram as antigas de máscara/reconstrução já registradas em `reports/falhas_preexistentes_20261111.md`: pontuação fora do polígono (`GLYPH_ART_BOUNDARY_UNCERTAIN`), linha de arte cruzando glifos, componente unido `MW` classificado como fundo e texto tocando borda do balão. Nenhuma falha nova atribuível à integração foi identificada. A suíte não está verde.

## Evidência física — REF-A, 2026-11-11

Job `c034a1cf-903b-471b-a799-575cad7f85de`, disparado pela interface autenticada em `http://127.0.0.1:8080`: Hero Killer, episódio 285, modo `Qualidade`, saída `Tradução pronta`, forçar ligado, cache desligado e tradução de SFX desligada. O job completou 65 páginas em 354,78 s no pipeline (aprox. 5min59s na interface), com 59 grupos.

O primeiro sinal de GPU foi confirmado no log do job (`Inicializando RapidOCR / ONNX Runtime (GPU DirectML)...`). O `timing_report.json` confirma OCR efetivo `directml`, LaMa efetivo `directml`, 56 chamadas LaMa em DirectML e nenhum fallback. O monitor estava ligado, intervalo 5 s, 68 amostras. Pico amostrado da árvore do pipeline: 3.020,32 MB RSS (pai + filhos); pico de RAM usada pelo sistema: 22.765,21 MB. Isso não mede VRAM.

| Métrica | REF-A base `f181a17e` | REF-A novo `c034a1cf` | Diferença |
|---|---:|---:|---:|
| Tempo total do medidor | 528,68 s | 354,78 s | -173,90 s (-32,9%) |
| Inpainting | 219,24 s | 195,44 s | -23,80 s (-10,9%) |
| Tamanho por página | 37,36 MB | 9,12 MB | -28,24 MB |
| Portão físico / resíduos-fonte | passou / 0 | passou / 0 | igual |

A comparação é histórica, não um A/B controlado: versões e condições de execução não foram congeladas. Portanto, não atribuir a redução de tempo somente às alterações da Fase 0. O tempo total do relatório é o tempo medido pelo pipeline; a interface exibiu aproximadamente 5min59s.

O estado geral do job ficou `review_required` (`REVIEW`), apesar do portão físico de remoção de texto-fonte passar. O manifesto lista revisão manual/qualidade de tradução e revisão semântica; há um item semântico em `p016:REGION_002:source_segmentation_recovered:GIFTSARERATHER`. Todos os 65 outputs e o PDF foram produzidos. A aprovação de qualidade geral permanece pendente.

## Validação complementar — REF-A, REF-B e Apenas Clean (2026-11-11)

### REF-A: base versus job novo

`job_metrics.py --compare` entre `f181a17e-281d-40a8-bd7e-41b4bbdcdca1` e `c034a1cf-903b-471b-a799-575cad7f85de` confirmou 57/58 regiões traduzidas nos dois jobs. A base certificou 54 páginas, 8 foram classificadas como sem texto comprovado e 3 reprovaram (`10, 52, 60`). O job novo certificou 53, manteve 8 sem texto comprovado e reprovou 4 (`10, 23, 52, 60`); todos com `clean_certificate_not_pass`. O portão físico passou nos dois, com zero resíduos-fonte.

O novo REF-A ficou em `review_required` por 5 grupos com revisão manual, avisos de qualidade de tradução e uma revisão semântica. Na página 16, o OCR leu `OTHER GIFTSARERATHER COMMON,BUTTHAT ONE ISN'T.`; a recuperação canônica foi `OTHER GIFTS ARE RATHER COMMON,BUT THAT ONE ISN'T.`; tradução: `OUTROS PRESENTES SÃO BASTANTE COMUNS, MAS ESSE NÃO É.`. A decisão semântica permaneceu em revisão. Os registros manuais também incluem p10 `FluCK` (SFX preservado) e p60 `PWIP` → `PIP` (fidelidade da reconstrução incerta). O mesmo item de p16 e `PWIP` → `PIP` já constavam na base; a página 23 é a reprovação de certificado que surgiu no job novo.

### REF-B: job completo pela interface

Job `432b35af-048b-4553-b6f6-0d351cf633d0`, modo `Completo`, Qualidade, force ligado, cache desligado e SFX desligado (conferido na configuração da interface). DirectML foi confirmado no log. O job terminou em `review_required`/`REVIEW`, não em `failed`; produziu PDF, imagens e PSDs. A comparação com `278c2486-02ae-4103-8a15-6f5ece95e26b`:

| Métrica | Base `278c2486` | Novo `432b35af` |
|---|---:|---:|
| Tempo total | 641,26 s | 599,51 s |
| Regiões traduzidas / detectadas | 169 / 177 | 169 / 177 |
| Certificados de limpeza | 69 / 85 | 69 / 85 |
| Páginas sem texto comprovado | 1 | 1 |
| Páginas reprovadas | 15 | 15 |
| Portão físico | reprovado | reprovado |
| Resíduos-fonte | 7 | 7 |

As mesmas 15 páginas reprovaram certificação: `2, 13, 24, 30, 34, 48, 53, 54, 65, 68, 72, 75, 77, 80, 85`, com `clean_certificate_not_pass`. Os relatórios apontam entre os resíduos idênticos `SIMPLE` (p. 2), `CLUNK-.` (p. 18), texto OCR em inglês (p. 38), `WHOOSH` (p. 53) e `ME?` (p. 72); são 7 no total nos dois jobs. O status melhorou de `ERROR`/`failed` para `REVIEW`/`review_required`, sem mudar a contagem de resíduos nem a cobertura de tradução.

### Custo do monitor e falha real de Apenas Clean pela interface

Foram executados dois REF-A consecutivos pela interface em `Apenas Clean`, Qualidade, force ligado, cache desligado, 65 páginas, sem chamadas de tradução paga. O primeiro teve monitor ligado (5 s); o segundo, desligado temporariamente. O override foi removido depois, e o worker voltou a `RESOURCE_MONITORING=True`, intervalo 5 s.

| Execução | Monitor | RAM livre no início | Total medido | Inpainting |
|---|---|---:|---:|---:|
| `5ffc081a-8847-4d32-a944-006e2853eda5` | ligado, 5 s, 70 amostras | 12,99 GB | 364,10 s | 194,00 s |
| `3ee21928-3731-4b9b-b773-8a8bb5603914` | desligado | 11,17 GB | 331,84 s | 173,22 s |

A diferença observada foi 32,26 s (8,9%) a favor da rodada sem monitor. É uma medição sequencial única, não suficiente para atribuir toda a diferença ao monitor; RAM inicial, variação entre execuções e o custo de outros estágios não foram controlados/repetidos. O objetivo de custo ≤2% não foi demonstrado.

**A interface realmente marca ambos os cartões como falha.** Os logs do pipeline dizem `status=success`, mas os manifestos dos jobs dizem `failed`; os dois têm erro não recuperável em `page_034`: `RuntimeError: imagem final invalida`. Os códigos agregados são `page_processing_error`, `physical_page_population_incomplete` e `source_page_coverage_incomplete`. As imagens Clean foram produzidas; o PDF não faz parte das operações pedidas neste modo (`requested_operations=['clean']`), não houve tentativa de PDF nem erro no estágio de PDF. Assim, o defeito observado pela interface é a falha de processamento da página 34 e o status do job, não uma falha de geração de PDF.

## Diagnóstico e implementação F0.8 (2026-11-11)

### Página 23 do REF-A

Os artefatos das duas execuções mostram uma diferença concreta, não apenas variação de saída:

| Evidência | Base `f181a17e` (`cda3f90`) | Novo `c034a1cf` (`e3fa1dff`) |
|---|---|---|
| Método final da região | `flux2_klein_reference` | `lama_large` |
| Decisão | `accepted`, `ok` | `accepted_with_review`, `art_reconstruction_fidelity_uncertain` |
| Tentativa FLUX | validada e aceita | tentativa registrada como `caption_effect_model_unavailable`; depois LaMa foi aceito com revisão |
| Tempo de inpainting da página | 27,17 s (estágio agregado) | 18,80 s (estágio agregado) |
| Certificado da página | sem reprovação | `clean_certificate_not_pass` |

O dono complementou a inspeção: no job novo `sd-cli.exe` encerrou com código 1 em 7,2 s, telemetria `generative_output_missing` / `output_or_process_failure`; na base a chamada levou 21 s e terminou `ok`. Os modelos existem e uma chamada isolada funciona hoje. Isso fecha a causa observável como falha do processo, não timeout nem perda de modelo e não indica regressão da Fase 0. A implementação F0.9 abaixo preserva o stderr e repete uma vez somente essa categoria.

### Causa da falha do Apenas Clean

O erro nasce em `_process_post_translation_page` / no caminho serial equivalente, no teste `_reconstructed_page_is_valid(output_path, source_path)`. Ele rejeita arquivo ilegível/vazio e, quando a fonte tem variância acima de 5, também rejeita uma saída com variância até 5. A página 34 é uma página preta com dois textos brilhantes; sua limpeza correta remove os únicos pixels visíveis e deixa a página uniforme preta. No modo `Apenas Clean`, a saída é exatamente a imagem limpa, sem texto traduzido sobreposto, então o teste genérico a marcou incorretamente como conteúdo destruído. A `dev` em `7879bad` mantém o mesmo teste relativo à fonte e não contém uma exceção baseada em certificado Clean; o modo falha pela mesma regra. Isso é consistente com os dois erros já observados em jobs anteriores.

Correção local: `_clean_only_output_is_valid` permite saída uniforme só no plano sem typeset quando `_clean_page_certificate_valid` passa e a saída é pixel a pixel idêntica ao artefato limpo certificado. Saída corrompida, sem certificado ou divergente continua reprovada. Os caminhos paralelo e serial usam a exceção restrita; a regra geral permanece intacta. Em `run_webtoon.py`, `PIPELINE_MAIN_RESULT` agora usa a classificação terminal do relatório (`failed`, `review_required` ou `finished`) em vez de indicar sucesso só porque algum arquivo foi gerado. Isso elimina o sinal de sucesso enganoso quando há erro estrutural. **Ainda não foi fisicamente validado pela interface**, então não há evidência de que os 65 artefatos serão entregues com sucesso.

### Medição direta do monitor

`ResourceMonitor` acumula com `perf_counter` a duração interna de cada tentativa de amostragem e grava `sampling_seconds`, `sampling_count` e `sample_count` em `resource_report.json`. O `timing_report.json` recebe `resource_monitor_sampling_seconds` e `resource_monitor_sample_count`; com monitor desligado, ambos valem zero. O teste unitário confirmou acumulação positiva e contagem de amostras. A razão física (segundos de amostragem / total do job) permanece pendente até o novo REF-A Apenas Clean autorizado por CLI.

Testes offline executados nesta alteração:

```text
tests/test_short_page_reconstruction.py
tests/test_resource_monitor.py
tests/test_clean_page_completion_integration.py
tests/test_local_benchmark_pipeline_e2e.py
tests/test_run_webtoon_terminal_status.py
24 passed in 63.46s
```

### Pendências

- Rodar REF-A `Apenas Clean` por CLI (autorizado em 2026-11-11) e verificar 65 imagens, certificados e a página 34. Isso valida o pipeline; o estado do cartão de UI ainda requer execução pela interface.
- Ler os dois novos campos do `timing_report.json` nesse job e calcular o custo direto; o limite de 2% ainda não foi medido.
- Se a página 34 ou qualquer outra continuar falhando, preservar o log/manifesto e corrigir a causa estrutural antes de declarar F0.8 aceito.
- Reproduzir a página 23 em REF-A `Tradução pronta` após o dono iniciar o job pago; conferir dispositivo DirectML e, se FLUX falhar, ler o novo log em `errors/`.
- Corrigir os 7 resíduos/falhas de qualidade do REF-B sem enfraquecer o portão físico; revisar os itens de REF-A em `review_required`.
- As quatro falhas preexistentes de máscara/reconstrução continuam documentadas em `reports/falhas_preexistentes_20261111.md`.

## Implementação F0.9 — falha de FLUX rastreável (2026-11-11)

- `flux_edit.py` salva as últimas 40 linhas de stderr em `errors/flux_<página>_<região>.log` antes de remover o diretório temporário e registra `diagnostic_log_path` na telemetria. Falhas de persistência registram apenas a classe do erro.
- `ocr_balloon.py` reporta `caption_effect_model_unavailable` apenas quando `available(purpose="caption_effect")` retorna falso; se o processo retornar nulo, mantém o `reason` real. Repete uma vez exclusivamente para `output_or_process_failure`; não repete `device_memory`.
- O contexto do render fornece pasta `errors` e índice da página; o identificador da região é sanitizado antes de formar o nome do arquivo.
- Testes simulam stderr de subprocesso (incluindo cauda de 40 linhas), falha seguida de sucesso aceito pelos validadores, não-retry para memória do dispositivo, duas falhas sem terceira tentativa e continuidade do fallback aprendido existente.
- Validação focada atual: sete arquivos de teste da Fase 0 — 45 passed em 54,09 s.
- Ainda pendentes: REF-A Apenas Clean CLI para os 65 artefatos e razão do monitor; REF-A pago Tradução pronta, iniciado pelo dono, para revalidar p023; suíte completa.
