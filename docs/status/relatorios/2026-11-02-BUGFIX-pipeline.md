# Relatório — investigação de bugs de pipeline (2026-11-02)

**Branch:** dev · **Base:** `6efb8df` · **Resultado:** 0 bugs corrigidos, 0 arquivos de código alterados.

Esta rodada foi só de leitura de código. Não havia imagem de capítulo, log de job nem
evidência dos balões afetados, e a pipeline não pôde ser executada (sem providers reais,
sem GPU/DirectML, sem modelos). Uma correção sem reprodução em uma pipeline de ~6160
testes herméticos pode regredir gates de qualidade, então nenhuma foi feita.

## Sintoma 1 — Balões não traduzidos

Verificado e **sem defeito encontrado**:

- `yomu/translation/providers/provider_execution.py:259` e
  `yomu_backend_provider.py:470,830`: o provider casa resultados por `item_id` e rejeita
  contagem divergente. Um item perdido no meio não desloca as traduções seguintes.
- `yomu/ocr/ocr_balloon.py:1866-1895` (`apply_group_translations`): tradução vazia vira
  `missing_translation_candidate` com estado terminal. Não passa em silêncio.
- `yomu/ocr/ocr_balloon.py:5035-5077` (`_should_translate_group`): grupos podem ficar de
  fora do envio por `ocr_quality_blocked`, `_ocr_unintelligible_source_text`, `ignored`,
  `preserve_as_name`, falta de autoridade de história e fundo decorativo texturizado. Todos
  são gates intencionais e viram `review_required`, não perda silenciosa.

Hipótese mais provável, **não confirmada**: o balão foi descartado em um desses gates
(principalmente OCR de baixa qualidade ou classificação `decorative`/`unknown`).

## Sintoma 2 — Limpeza incompleta

Pontos lidos, sem defeito comprovado:

- `yomu/ocr/ocr_balloon.py:11332-11334` (`_mask_padding`): padding por linha =
  `max(1, min(MAX_MASK_EXPANSION, TEXT_MASK_PADDING, int(h*0.16)))`. Com os padrões (3 e 8)
  o teto efetivo é 3 px. `11337-11342` ainda dilata 3x3 antes do TELEA.
  Candidato a causa: texto com contorno/brilho largo pode ficar além de 3 px. Calibrar isso
  exige ver o resultado físico.
- `yomu/clean/inpainting/art_text_inpainting.py:520-560`: a máscara de glifos depende de
  limiares de contraste (`delta >= 50/24`, `saturation <= 72`). Texto colorido ou de baixo
  contraste pode ficar fora da máscara.

## Sintoma 3 — Artefatos na limpeza

- `yomu/clean/inpainting/advanced_art_inpainting.py:214`: composição com máscara binária,
  sem feather. É o contrato do projeto (`outside_mask_changed_pixels == 0`, ver
  `yomu/clean/orchestrator.py`). Suavizar a borda violaria esse contrato.
- A hipótese de "steps/guidance" não se aplica: o LaMa aqui é ONNX/TorchScript de passada
  única (`yomu/clean/inpainting/lama_onnx.py`) e não tem esses parâmetros.

## O que ficou em aberto

1. Os três sintomas dependem de dados físicos: capítulo, página e balão afetados, mais o
   relatório de qualidade do job (`translation_final_state`, `translation_final_reason`).
2. O estado `translation_final_reason` por região do job afetado indicaria em qual gate
   cada balão não traduzido caiu. Com isso a correção deixa de ser chute.
3. Padding máximo de 3 px e feather ficam como candidatos de calibração, só com A/B em
   imagens reais.

## Status (política de evidência)

Nada aqui altera o estado `IMPLEMENTED`/`TESTED`/`PHYSICALLY_VERIFIED` de nenhum recurso.

DOC IMPACT: NONE
WHY: relatório de investigação; nenhum código, comportamento, config ou UI foi alterado.
