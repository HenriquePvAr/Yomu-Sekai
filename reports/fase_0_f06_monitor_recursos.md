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

## Pendente para a PAUSA 0

- Rodar REF-B fisicamente depois de restaurar DirectML e medir seus recursos; nenhum resultado novo de REF-B foi obtido nesta rodada.
- Comparar o tempo do monitor contra uma execução comparável sem monitor; o limite de 2% ainda não foi verificado fisicamente após o intervalo de 5 segundos.
- Resolver/revisar os itens de qualidade que mantiveram o job em `review_required`; a aprovação do gate físico não equivale a aprovação geral.
- Testar Apenas Clean pela interface: execuções anteriores por CLI terminaram com erro na etapa de PDF; este job foi Tradução pronta e não valida esse modo.
