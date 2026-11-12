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
