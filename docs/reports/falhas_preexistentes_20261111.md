# Falhas preexistentes — 2026-11-11

Das sete falhas originalmente registradas, seis permanecem nesta tabela como histórico: três casos de `download_gate` contaminados por PNGs externos e três testes dependentes do OpenCV. Os registros originais foram verificados no ponto de backup `cda3f90` e na `origin/dev`, conforme `%TEMP%\komyst-isolated-backup.log`. **Atualização F3.0 (2026-11-12):** o teste de borda, retirado da tabela de preexistentes, é uma regressão introduzida por `80f0620`, não uma falha antiga do produto. A correção aplicada passou no teste focado; a prova física REF-A ainda está pendente por erro de memória Vulkan no FLUX.

| Teste | Mensagem observada | Diagnóstico |
|---|---|---|
| `tests/test_art_reconstruction_quality.py::GlyphFootprintCoverage::test_punctuation_outside_the_polygon_is_still_covered` | `AssertionError: False is not true : GLYPH_ART_BOUNDARY_UNCERTAIN` | A reconstrução recusa a máscara por incerteza na fronteira entre glifo e arte. |
| `tests/test_art_reconstruction_quality.py::MaskGeometryDiagnostics::test_crossing_line_art_overlap_is_measured_for_follow_up` | `AssertionError: True is not false` | O teste espera rejeição, mas a implementação atual aceita a máscara neste fixture. |
| `tests/test_download_gate_partial_scope.py::PartialScopeDownloadGateTests::test_five_page_partial_passes_when_all_selected_present` | `AssertionError: False is not true : ['unreferenced_png_included']` | Ambiente: o fixture aponta para `C:\tmp`, e o gate também encontra o PNG externo `selo-raw.png`. |
| `tests/test_download_gate_partial_scope.py::PartialScopeDownloadGateTests::test_full_run_still_requires_every_page` | `AssertionError: False is not true : ['unreferenced_png_included']` | Mesmo PNG externo em `C:\tmp`; a validação de páginas completas não é a causa da falha. |
| `tests/test_download_gate_partial_scope.py::PartialScopeDownloadGateTests::test_scattered_partial_selection_passes` | `AssertionError: False is not true : ['unreferenced_png_included']` | Mesmo PNG externo em `C:\tmp`; a seleção parcial não é a causa da falha. |
| `tests/test_mask_fringe_and_glyph_filter.py::test_large_glyph_components_are_kept_and_background_shapes_dropped` | `assert not ob._component_is_background_shaped(...)` | O componente sintético unido `MW` é classificado como forma de fundo. |

## Verificação do PNG em `C:\tmp`

Os três casos de `download_gate` constroem caminhos sintéticos com pai `C:\tmp`. O teste usa `canonical_local_path` e `path`, habilitando a inspeção do diretório real; `_build_download_gate` lista todos os `*.png` nesse pai e compara com os caminhos canônicos do relatório. Na máquina havia um arquivo não referenciado, `selo-raw.png` (40.590 bytes, modificado em 2026-11-06), confirmando que essas três falhas são contaminação do ambiente de teste, não uma regressão do gate.

## Ambiente — resolvido movendo arquivos

Os cinco testes de `download_gate` abaixo falharam antes porque os seus fixtures habilitam a varredura de PNGs no diretório pai. Foram movidos, sem apagar, para `%TEMP%\komyst-png-soltos\`:

- `<repo>\dbg_hur_2x.png`
- `<repo>\flux_p9_test.png`
- `selo-raw.png`

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
| `tests/test_download_gate_ordering.py::DownloadGateOrderingTest::test_complete_in_order_passes` | `AssertionError: False is not true : ['unreferenced_png_included']` | `<repo>\dbg_hur_2x.png` e `<repo>\flux_p9_test.png` |
| `tests/test_download_gate_ordering.py::DownloadGateOrderingTest::test_sorting_by_order_makes_complete_download_pass` | `AssertionError: False is not true : ['unreferenced_png_included']` | Os mesmos dois PNGs na raiz do repositório. |

Os três testes de seleção parcial listados acima usavam `C:\tmp` e foram contaminados por `selo-raw.png`; estes dois testes de ordenação usavam o diretório corrente e foram contaminados pelos PNGs da raiz. Após mover os arquivos, os cinco passaram. Nenhum falhava por páginas ausentes ou por ordenação incorreta.

## Rechecagem após a correção de F0.8 — 2026-11-11

Na suíte completa executada no checkout da `fase-0-jobs-nao-morrem` (commit `5427455`), as quatro falhas de máscara/reconstrução continuam reproduzíveis: **6.499 passed, 4 failed, 141 skipped, 1 xfailed, 8 warnings e 787 subtests passed**, em 917,27 s. Cada um dos quatro testes também falhou quando executado isoladamente em um processo pytest separado. O Python usado foi `<python-3.11>\python.exe`, importando `Komyst` de `<repo>\Komyst`; OpenCV 4.10.0, NumPy 2.3.5, sem `PYTHONPATH` ou `PYTHONHOME` configurados.

Esta evidência **não reproduz** o resumo externo de 6.502 aprovados/1 falho nem a alegação de que três dos quatro testes passaram isoladamente em `bc02f38`. Não é efeito da ordem: os quatro falham tanto isolados quanto na suíte completa. Não é contaminação pelos PNGs: os quatro fixtures que falham são sintéticos e não leem `dbg_hur_2x.png`, `flux_p9_test.png` ou `selo-raw.png`. Também não há diferenças nos arquivos de máscara e nesses testes entre `bc02f38` e o HEAD atual (`git diff` vazio). A origem da divergência restante é compatível com ambiente/importação diferente no relatório externo, mas **não está comprovada** porque não veio acompanhado do executável Python, versões de NumPy/OpenCV e `Komyst.__file__` usados naquele teste. Não registrar os três como resolvidos até repetir com esses dados.

Na F3.0, confirmar os três casos dependentes sob o runtime OpenCV 5.0.0 e bisectar a única falha real; não alterar resultados por ajuste de teste sem evidência de contrato desatualizado.

## Classificação após confirmar o OpenCV efetivo — 2026-11-11 (atualização conclusiva)

Com OpenCV 5.0.0 do ambiente com `opencv-python-headless`, os três primeiros testes abaixo passam e resta uma falha real (confirmação externa, não reproduzida neste ambiente). Nenhum pacote foi instalado ou removido. O comando de verificação retornou, tanto com `python` quanto com `python -s`:

```text
4.10.0 <python-3.11>\Lib\site-packages\cv2\__init__.py
```

O executável usado é Python 3.11. A pasta `Roaming\Python311\site-packages` não contém `cv2`; os metadados globais mostram `opencv-python 5.0.0.93` e `opencv-contrib-python 4.10.0.84` instalados lado a lado no mesmo `site-packages`, enquanto `opencv-python-headless` não está instalado aqui. O módulo efetivamente importado é 4.10.0. Isso confirma um conflito local entre distribuições que compartilham o diretório top-level `cv2`. A instalação/correção do ambiente aguarda decisão do mantenedor. O resultado com OpenCV 5.0.0 citado abaixo é evidência externa, não reproduzida neste ambiente.

| Teste | Resultado efetivo com OpenCV 4.10.0 | Classificação para F3.0 |
|---|---|---|
| `GlyphFootprintCoverage::test_punctuation_outside_the_polygon_is_still_covered` | Falha: `GLYPH_ART_BOUNDARY_UNCERTAIN`; reprovou no `python` normal e em `python -s` | Dependente do OpenCV; reportado como passando com 5.0.0. Não corrigir código antes de validar no runtime fixado. |
| `MaskGeometryDiagnostics::test_crossing_line_art_overlap_is_measured_for_follow_up` | Falha: esperava `mask_valid=False`, recebeu `True`; reprovou normal e `-s` | Dependente do OpenCV; reportado como passando com 5.0.0. Não corrigir código antes de validar no runtime fixado. |
| `test_large_glyph_components_are_kept_and_background_shapes_dropped` | Falha: componente `MW` classificado como forma de fundo; reprovou normal e `-s` | Dependente do OpenCV; reportado como passando com 5.0.0. Não corrigir código antes de validar no runtime fixado. |
| `test_text_touching_a_balloon_border_is_cleaned_without_erasing_the_border` | Falha original: `residual_source_text_after_cleanup`; regressão introduzida por `80f0620` | **Removida da lista de preexistentes.** A dilatação cega de 2 px generalizada a todos os grupos aumentou a máscara de 7.285 para 9.940 px e tocou 18 px da borda. A correção F3.0 bloqueia halo novo sobre pixels tão escuros quanto a tinta em traços longos de mesma polaridade; pixels da máscara base permanecem intactos. O teste focado e a validação física REF-A/REF-B passaram conforme o relatório F3.0. |

Com esta classificação, três falhas são dependentes da versão do OpenCV; a falha da borda foi identificada como regressão de `80f0620` e corrigida em F3.0. `python` e `python -s` usam OpenCV 5.0.0 nesta validação. Os resultados históricos de 4.10.0 não representam o runtime fixado. O patch preserva a máscara base e impede halo novo sobre pixels de estrutura tão escuros quanto a tinta. A validação física confirma p23 PASS com FLUX no REF-A e REF-B em 70/85 certificados com os mesmos 7 resíduos. Suíte final da versão do patch: 6.504 passed, 141 skipped, 1 xfailed, 8 warnings e 787 subtests; o teste da borda passou.
