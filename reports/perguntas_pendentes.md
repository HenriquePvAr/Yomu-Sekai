# Perguntas e dependências pendentes — Fase 0

Atualizado: 2026-11-11 (reconciliação final)

Estado atual: a prova física final de F0.8 está fechada pelo job `5dae49f7` no commit `8791609`. As notas anteriores abaixo são checkpoints históricos; a seção “Atualização após confirmar OpenCV e job físico F0.8” contém a conclusão vigente e supersede os resultados anteriores do Clean `5731a21a` e da suíte nesta sessão.

## Resolvido — intervalo do monitor na instalação local

`.env` linha 79 alterado para `RESOURCE_MONITOR_INTERVAL_SECONDS=10.0` com autorização do dono. Os jobs pelo painel registram `interval_seconds: 10.0`.

## Checkpoint histórico — F0.8 pelo painel (Apenas Clean; supersedido)

Causa: a exceção para página que fica em branco após limpeza certificada só existia em dois dos sete pontos que validam a página. No worker por página ela rodava antes do certificado existir (`imagem final invalida`); corrigida a ordem, as etapas seguintes ainda descartavam a página (`required_artifact_missing`). Correção em `6c4734b`: todas as etapas usam `_page_output_is_valid`.

Job `5731a21a89184e07b319041f1ee46aa2`: `review_required`, 65/65 imagens, cartão "concluído — revisão recomendada", DirectML, monitor 4,35 s de 404,26 s (1,08%). O banco e o `run_manifest.json` registram `bc02f38`, anterior a `6c4734b`; portanto o resultado é observado, mas não valida fisicamente o fix final. A página 10 segue em revisão (preexistente na `dev`, para a Fase 3).

## Resolvido — REF-A `Tradução pronta` (job pago)

Job `abee15719bd346bc86197faaf9307d43`, pelo painel: `review_required`, 377,90 s, DirectML, 57/58 traduzidos, 62 páginas com certificado `verified` (igual à base: 54 + 8 sem texto), gate físico aprovado com 0 resíduos. Página 23: FLUX `ok` em 20,45 s, uma tentativa, sem log de erro. A nova tentativa da F0.9 não foi exercitada por falha real; segue coberta só por teste simulado.

## Itens observados no checkpoint anterior

- Aprovar o merge da Fase 0 em `dev`.
- O botão do painel ficou em "PROCESSANDO..." depois de job falho (observação de 11/11). Fica registrado como item de interface fora do gate da PAUSA 0; não investigado.
- A suíte desta checkout foi reexecutada: 6.499 passaram e 4 falharam (as quatro antigas de máscara/reconstrução). As quatro falham também isoladamente; a diferença frente ao resumo externo 6.502/1 não foi explicada. Seguem para F3.0 e não devem ser marcadas resolvidas sem reproduzir as versões/runtime do relatório externo.


## Reconciliação anterior da PAUSA 0 — supersedida pela atualização OpenCV abaixo

Os jobs físicos informados foram rechecados no banco/artefatos. O Apenas Clean `5731a21a…` terminou `review_required` com 65/65 imagens e monitor a 10 s, mas sua proveniência é `bc02f38`, anterior ao fix `6c4734b`; não comprova o F0.8 no snapshot final. O REF-A `Tradução pronta` `abee1571…` é de `6c4734b`, passou o gate físico com zero resíduos, 57/58 traduzidas e 62/65 certificados; p023 teve FLUX `ok` em 20,45 s.

A nova extração do REF-B corrigiu divergência nos relatórios: base `278c2486` e novo `432b35af` têm 70/85 certificados, 169/177 traduções e 7 resíduos. Os status são `failed` → `review_required`; tempos 641,260 s → 599,511 s.

A suíte completa nesta checkout em Python 3.11/OpenCV 4.10.0/NumPy 2.3.5 deu 6.499 passed e 4 falhas, em 917,27 s. As quatro falhas antigas foram reproduzidas isoladamente; fixtures são sintéticos e não leem PNGs soltos, e nenhuma depende da ordem da suíte. Os arquivos de código/teste correspondentes são idênticos entre `bc02f38` e HEAD. O relato externo de 3 aprovadas/1 falha não foi reproduzido; ambiente/import diferente é hipótese sem evidência comparativa. A F3.0 permanece aberta.

**Decisão pendente do dono:** autorizar ou não merge da Fase 0 em `dev`. Nenhum merge/push foi feito.


## Atualização após confirmar OpenCV e job físico F0.8 — 2026-11-11

- A prova física final de F0.8 é o REF-A Apenas Clean pelo painel `5dae49f7326b4c56b0c0e0731ec6b253`, commit `8791609`: 65/65 imagens e DirectML. O status `review_required` decorre de revisão de qualidade, não falha do job.
- `python` e `python -s` da sessão carregam OpenCV 4.10.0 em `C:\Users\henri\AppData\Local\Programs\Python\Python311\Lib\site-packages\cv2\__init__.py`. O worker registrado nesse job foi PID 36048, executável `pythonw.exe` do mesmo Python311. O artefato original não gravou a versão; a conclusão do worker deriva do mesmo executável/ambiente. A nova telemetria registra essa proveniência nos próximos jobs.
- O dono confirma que três falhas antigas passam com OpenCV 5.0.0 e uma falha real continua para F3.0. A sessão não instalou/removeu pacotes; a decisão de corrigir o ambiente global continua do dono.
- As medições de limpeza por CLI desta sessão rodaram pelo Python311/OpenCV 4.10.0 e devem ser tratadas como feitas no runtime divergente.
- Não há dúvida técnica pendente para concluir a Fase 0: o único passo externo é aguardar aprovação explícita antes de qualquer merge em `dev`. Não houve merge ou push.

## Ambiente OpenCV corrigido e revalidação (2026-11-11, noite)

Causa: a pasta global do Python tinha `opencv-contrib-python` 4.10.0 por cima do `opencv-python` 5.0.0, e a pasta do usuário tinha `opencv-python-headless` 5.0.0. Sessões com a pasta do usuário carregavam 5.0.0; sessões sem ela (Codex, e o app iniciado a partir dela) carregavam 4.10.0. É o caso `OPENCV-VARIANT-SHADOWING-001`.

Correção aplicada com autorização do dono, no Python global:

1. `pip uninstall -y opencv-contrib-python opencv-python-headless`
2. `pip install --no-deps opencv-contrib-python==4.10.0.84` (o Paddle recusa iniciar sem esse pacote registrado)
3. `pip install --force-reinstall --no-deps opencv-python==5.0.0.93` (por último, para o `cv2` efetivo ser 5.0.0)

Conferido: `cv2` 5.0.0 com e sem a pasta do usuário; `DmlExecutionProvider` disponível; `easyocr` reclama a falta do headless no `pip check` (não é usado no perfil atual). A ordem dos passos 2 e 3 importa: qualquer reinstalação do contrib volta o `cv2` para 4.10.0. Lista de pacotes anterior salva fora do repositório.

Revalidação do REF-A pelo painel, commit `286d588`, OpenCV 5.0.0 gravado no `timing_report.json`, DirectML:

| Job | Modo | Tempo | Resultado |
|---|---|---:|---|
| `c3c75411b8c24333b442c6fbff74cca3` | Apenas Clean | 288,69 s (suíte rodando em paralelo) | `review_required`, 65/65 imagens limpas, 63 certificados `verified`, monitor 0,98% |
| `72e75ab5c514472bb11d78618066a0d2` | Tradução pronta | 278,16 s (máquina livre) | `review_required`, 57/58 traduzidos, gate físico aprovado com 0 resíduos, 61 certificados `verified`, monitor 0,75% |

Abertos para a Fase 3:

- Tradução pronta ficou com 61 certificados contra 62 da base: uma página saiu com `source_completeness_unproven`. Não investigado.
- Suíte completa com OpenCV 5.0.0: 6.501 passaram, 2 falharam. Uma era o Paddle sem o contrib (corrigida no passo 2, teste passa); resta `test_text_touching_a_balloon_border_is_cleaned_without_erasing_the_border`. A suíte completa não foi repetida depois do passo 2.
- Todas as medições feitas hoje com OpenCV 4.10.0 (jobs `5731a21a`, `abee1571`, `5dae49f7` e as execuções por linha de comando) não servem de comparação com as desta seção.

## Investigação do certificado a menos e linha de base do REF-B (2026-11-12)

**Página 22 (REF-A):** com OpenCV 5.0.0 o OCR enxerga um balão (`BALAO_1`) que com 4.10.0 não aparecia, e a página fica `REVIEW_REQUIRED` por `page_ocr_review_required_for_clean_verification` (reason `source_completeness_unproven`). Isso **não é regressão da Fase 0**: Apenas Clean por linha de comando no código da `dev` (`7879bad`), também com OpenCV 5.0.0, deixa a página 22 em revisão pelo mesmo motivo. Resultado da `dev` com 5.0.0: 62 PASS e revisão em p10, p22 e p23 (371,2 s). Fase 0 com 5.0.0: revisão em p10 e p22 no Apenas Clean (63 PASS); a p23 passa. A Tradução pronta teve revisão adicional em p52 e p60 (`target_or_ownership_incomplete`) na rodada com 5.0.0, mesma causa de variação de OCR entre execuções; não investigado.

**REF-B em Completo pelo painel**, commit `58230f4`, OpenCV 5.0.0, DirectML, job `a9a1339d8157423eacb561d402d24494`:

| Métrica | Base | Fase 0, OpenCV 4.10.0 | Fase 0, OpenCV 5.0.0 |
|---|---:|---:|---:|
| Tempo total | 641,26 s | 599,51 s | 518,77 s |
| Traduzidas | 169/177 | 169/177 | 169/177 (168 `ok` + 1 caixa de legenda) |
| Certificados `verified` | 70/85 | 70/85 | 70/85 |
| Gate físico | reprovado, 7 resíduos | reprovado, os mesmos 7 | reprovado, 7 resíduos |
| Estado | `failed` | `review_required` | `review_required` |
| Artefatos | | | PDF, 85 imagens traduzidas, 85 limpas, 85 PSD, relatório e manifesto de revisão, todos produzidos |
| Monitor | | | 2,94 s de amostragem em 518,8 s (0,57%) |

Os 7 resíduos do REF-B e os 15 `target_or_ownership_incomplete` seguem para a Fase 3.
