# Relatório final — Fases 0 a 6 (2026-11-13)

Base: `dev` @ `15e3f0b`. Máquina de medição: 31,4 GB de RAM, AMD Radeon RX 6600 (8 GB), Windows 10.
**Condição das medições:** a RAM do sistema ficou em 61–66% (o WSL/Docker da máquina estava em uso na mesma
máquina). Os tempos são, portanto, de uma máquina sob uso, não de uma máquina livre.

**Ressalva (descoberta depois do fechamento):** em todos os jobs de 2026-11-13 o LaMa grande e o FLUX
ficaram indisponíveis (`MODEL_UNAVAILABLE`, `caption_effect_model_unavailable`), porque o caminho padrão dos modelos
ainda apontava para `%LOCALAPPDATA%\Komyst\models` e os arquivos estão na pasta de dados do usuário. Os tempos são
comparáveis entre si, mas as métricas de qualidade e os tempos absolutos **não representam** o pipeline com os
modelos aprendidos ligados.

Capítulos de referência: REF-A (65 páginas lógicas, 58 balões) e REF-B (85 páginas lógicas, 177 regiões).

## 1. O que foi entregue

| Fase | Entrega | Estado |
|---|---|---|
| 0 | Medição de base: monitor de recursos, `job_metrics.py`, diagnóstico de PSD | feito |
| 1 | Guarda de memória antes de LaMa/FLUX, liberação de buffers de página, contadores `*_skipped_low_memory` | feito; **meta de −25% de RAM não demonstrada** (ver §3) |
| 2 | Observabilidade da varredura residual, comparação de preenchimentos só quando necessária, validação de página memorizada, teto de chamadas e timeout do FLUX | feito parcial (F2.3.1 e F2.4 não feitos) |
| 3 | Qualidade de tradução: `FOR` como subjuntivo, palavra comum isolada não é nome, comparação LaMa forçada só quando não trivial | feito parcial (ver §3) |
| 4 | Entrega enxuta por modo (`KEEP_WORK_FILES`, `traducao.txt`) | parcial |
| 5 | Perfis de hardware leve/equilibrado/qualidade, reportados no `timing_report.json` | seleção feita; medição parcial |
| 6 | Limpeza de nomes antigos e do quadro | feito |

Correções feitas nesta rodada final, achadas pela validação física:

- **VRAM lida errado.** O WMI trunca `AdapterRAM` em 4 GB, então a RX 6600 (8 GB) aparecia como 4 GB. Agora a
  leitura usa `nvidia-smi` ou o tamanho de 64 bits do registro de vídeo; o corte passou a tolerar os ~7,98 GiB que
  uma placa de 8 GB reporta. Efeito: o modo automático desta máquina passou de Equilibrado para Qualidade.
  Commit `134d0f2`.
- **Regressão do gate físico na REF-A.** Um balão de fala com palavra isolada mantida como letreiro original
  (`sfx_original_lettering_kept`) era contado como resíduo, derrubando o gate. Agora é tratado como preservação
  deliberada, igual ao eco de origem. Commit `134d0f2`, com teste.

## 2. Números medidos

| Medida | Antes | Agora |
|---|---|---|
| REF-A, Tradução pronta | 365–424 s | **300–338 s** |
| REF-B, Tradução pronta | 528 s | **402 s** |
| REF-A, pico de RAM do pipeline | 3 355 MB (Fase 0) / 2 791–2 846 MB | 2 743–2 777 MB |
| REF-B, pico de RAM do pipeline | 2 758 MB | 2 579 MB |
| REF-A, gate físico | verdadeiro (F2.2) | **verdadeiro**, 0 resíduos (após a correção acima) |
| REF-B, traduzido | 164/177 | 164/177 |
| REF-B, revisão manual | 10 | 8 |
| REF-B, resíduos físicos | 8 | 8 |
| REF-A, comparações LaMa puladas | — | 37 de 86 |

Perfis na REF-A: Equilibrado 338 s, Qualidade 308 s (e 300 s no run final). A diferença está dentro da variação entre
execuções. **Leve não foi medido** (ver §3). Detalhes em `docs/HARDWARE_PROFILE.md`.

## 3. O que NÃO está pronto ou não foi provado

- **F1 (−25% de RAM):** o pico do pipeline ficou em ~2,7 GB contra ~2,8 GB antes da Fase 1 e 3,4 GB na Fase 0. A
  queda frente à Fase 0 existe, mas a meta da Fase 1 isolada não foi demonstrada.
- **REF-B não atinge a meta de qualidade** (≥174/177 e gate verdadeiro): 164/177, 8 resíduos físicos, gate falso,
  e 24 páginas com `clean_certificate_not_pass`. Os 5 casos de cobertura incompleta (páginas 2, 13, 18, 38, 72) são
  limite de reconhecimento de texto, não corrigido.
- **Perfil Leve não medido.** A variável `HARDWARE_PROFILE=leve` exportada no shell não chegou ao worker supervisionado;
  o `timing_report.json` mostrou o perfil automático. O canal pelo `.env` não foi verificado. Requisitos de RAM/VRAM
  seguem ESTIMADOS / NÃO HOMOLOGADOS; nada foi medido em hardware fraco.
- **Pico de VRAM** não é capturado pelo monitor de recursos.
- **Não feitos:** F1.4 (gerador de PDF não se aplica ao Pillow 12.3.0), F2.3.1 (cache de progresso), F2.4 (rótulo de
  etapa). Fase 4 parcial: o nome `translation.json` foi mantido e faltam as checagens de saldo/MB por página.
- **FLUX:** `device_memory` sem memória na página 23 da REF-A continua sem resolver.
- **Cobrança (auditoria A1):** uma reserva paga traduções ilimitadas. Não corrigido; fica como dívida registrada.
- **Evidence mode** foi avaliado e rejeitado com dados.

## 4. Como validar

```powershell
python -m pytest -q
python start_tradutor.py status
python -c "from komyst.runtime import hardware_profile as h; print(h.resolve())"
```

## 5. Release

Nenhuma tag, release, instalador ou manifesto foi criado ou publicado. A beta validada continua sendo a
`v0.9.1-beta.18`.
## 6. Medição com os modelos aprendidos ligados (2026-11-14)

Depois de corrigir o caminho dos modelos (`models_root()`), o LaMa grande passou a ser encontrado (`MODEL_UNAVAILABLE`: 0).
A RAM do sistema voltou a ficar em 93–99% (contêineres em uso), então **os tempos abaixo não são comparáveis** com os
anteriores; a comparação válida é a de qualidade.

| REF-B | Sem modelos | Com modelos |
|---|---|---|
| Traduzidas | 164/177 | **169/177** |
| Revisão manual | 8 | **4** |
| Resíduos físicos | 8 | **1** (`SIMPLE`, letreiro que depende de heurística não implementada) |
| Páginas Clean certificadas | 60/85 | **68/85** |
| Gate físico | falso | falso (1 resíduo; 16 páginas sem certificado) |
| Pico de RAM do pipeline | 2 579 MB | 3 489 MB |
| Tempo | 402 s | 793 s (RAM do sistema em 93%) |

REF-A com modelos: 56/58, gate físico verdadeiro, 0 resíduos, 750 s (RAM do sistema em 99,5%). O guard de memória negou o
FLUX em 53 consultas na REF-A e 145 na REF-B por falta de RAM livre (o contador conta consultas de disponibilidade, uma por grupo, não regiões distintas; o FLUX não rodou nenhuma vez); com a máquina livre esse número deve cair, mas isso não foi medido.
O custo de RAM dos modelos aprendidos (~+900 MB de pico) conta contra a meta de redução de RAM da Fase 1.
