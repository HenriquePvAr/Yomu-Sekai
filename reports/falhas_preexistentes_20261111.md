# Falhas preexistentes — 2026-11-11

As sete falhas da tabela já ocorriam no ponto de backup `cda3f90` e na `origin/dev`; nenhuma foi introduzida pelos ajustes desta sequência. Foram verificadas na execução isolada registrada em `%TEMP%\komyst-isolated-backup.log`. Depois da verificação ambiental abaixo, restam quatro falhas reais de código em máscara e reconstrução de arte.

| Teste | Mensagem observada | Diagnóstico |
|---|---|---|
| `tests/test_art_reconstruction_quality.py::GlyphFootprintCoverage::test_punctuation_outside_the_polygon_is_still_covered` | `AssertionError: False is not true : GLYPH_ART_BOUNDARY_UNCERTAIN` | A reconstrução recusa a máscara por incerteza na fronteira entre glifo e arte. |
| `tests/test_art_reconstruction_quality.py::MaskGeometryDiagnostics::test_crossing_line_art_overlap_is_measured_for_follow_up` | `AssertionError: True is not false` | O teste espera rejeição, mas a implementação atual aceita a máscara neste fixture. |
| `tests/test_download_gate_partial_scope.py::PartialScopeDownloadGateTests::test_five_page_partial_passes_when_all_selected_present` | `AssertionError: False is not true : ['unreferenced_png_included']` | Ambiente: o fixture aponta para `C:\tmp`, e o gate também encontra o PNG externo `C:\tmp\selo-raw.png`. |
| `tests/test_download_gate_partial_scope.py::PartialScopeDownloadGateTests::test_full_run_still_requires_every_page` | `AssertionError: False is not true : ['unreferenced_png_included']` | Mesmo PNG externo em `C:\tmp`; a validação de páginas completas não é a causa da falha. |
| `tests/test_download_gate_partial_scope.py::PartialScopeDownloadGateTests::test_scattered_partial_selection_passes` | `AssertionError: False is not true : ['unreferenced_png_included']` | Mesmo PNG externo em `C:\tmp`; a seleção parcial não é a causa da falha. |
| `tests/test_mask_fringe_and_glyph_filter.py::test_large_glyph_components_are_kept_and_background_shapes_dropped` | `assert not ob._component_is_background_shaped(...)` | O componente sintético unido `MW` é classificado como forma de fundo. |
| `tests/test_pipeline_candidate_page_fixes.py::test_text_touching_a_balloon_border_is_cleaned_without_erasing_the_border` | `AssertionError: residual_source_text_after_cleanup` | A validação detecta resíduo de texto após a limpeza do fixture junto à borda do balão. |

## Verificação do PNG em `C:\tmp`

Os três casos de `download_gate` constroem caminhos sintéticos com pai `C:\tmp`. O teste usa `canonical_local_path` e `path`, habilitando a inspeção do diretório real; `_build_download_gate` lista todos os `*.png` nesse pai e compara com os caminhos canônicos do relatório. Na máquina havia um arquivo não referenciado, `C:\tmp\selo-raw.png` (40.590 bytes, modificado em 2026-11-06), confirmando que essas três falhas são contaminação do ambiente de teste, não uma regressão do gate.

## Ambiente — resolvido movendo arquivos

Os cinco testes de `download_gate` abaixo falharam antes porque os seus fixtures habilitam a varredura de PNGs no diretório pai. Foram movidos, sem apagar, para `%TEMP%\komyst-png-soltos\`:

- `C:\Projetos\Yomu-Sekai\dbg_hur_2x.png`
- `C:\Projetos\Yomu-Sekai\flux_p9_test.png`
- `C:\tmp\selo-raw.png`

Depois da movimentação, os cinco testes passaram: **5 passed in 1.11s**. Os três testes de seleção parcial listados na tabela usam `C:\tmp`; esse caminho compartilhado não está isolado pelo fixture e deve ser substituído por um diretório temporário próprio numa correção futura.

Os dois testes de ordenação identificados na execução completa também passaram quando os PNGs da raiz do repositório foram movidos. Os nove registros de falha do baseline ficam assim separados: **cinco falhas ambientais resolvidas pela movimentação** e **quatro falhas de código ainda abertas**.

## Código — 4 falhas antigas ainda abertas

- `tests/test_art_reconstruction_quality.py::GlyphFootprintCoverage::test_punctuation_outside_the_polygon_is_still_covered` — `GLYPH_ART_BOUNDARY_UNCERTAIN`.
- `tests/test_art_reconstruction_quality.py::MaskGeometryDiagnostics::test_crossing_line_art_overlap_is_measured_for_follow_up` — espera `mask_valid=False`, mas recebe `True`.
- `tests/test_mask_fringe_and_glyph_filter.py::test_large_glyph_components_are_kept_and_background_shapes_dropped` — o componente unido `MW` é classificado como forma de fundo.
- `tests/test_pipeline_candidate_page_fixes.py::test_text_touching_a_balloon_border_is_cleaned_without_erasing_the_border` — a máscara invade a borda do balão.

## Falhas ambientais adicionais encontradas na suíte completa

Além das sete falhas do baseline isolado, a suíte completa encontrou dois testes de ordenação com a mesma causa ambiental (`unreferenced_png_included`). Eles também usam caminhos sintéticos sem caminho local; o gate resolve o diretório como a raiz do repositório e encontra PNGs sem relação com o fixture.

| Teste | Mensagem observada | Arquivo externo encontrado |
|---|---|---|
| `tests/test_download_gate_ordering.py::DownloadGateOrderingTest::test_complete_in_order_passes` | `AssertionError: False is not true : ['unreferenced_png_included']` | `C:\Projetos\Yomu-Sekai\dbg_hur_2x.png` e `C:\Projetos\Yomu-Sekai\flux_p9_test.png` |
| `tests/test_download_gate_ordering.py::DownloadGateOrderingTest::test_sorting_by_order_makes_complete_download_pass` | `AssertionError: False is not true : ['unreferenced_png_included']` | Os mesmos dois PNGs na raiz do repositório. |

Os três testes de seleção parcial listados acima usavam `C:\tmp` e foram contaminados por `C:\tmp\selo-raw.png`; estes dois testes de ordenação usavam o diretório corrente e foram contaminados pelos PNGs da raiz. Após mover os arquivos, os cinco passaram. Nenhum falhava por páginas ausentes ou por ordenação incorreta.
