# Falhas preexistentes — 2026-11-11

As sete falhas da tabela já ocorriam no ponto de backup `cda3f90` e na `origin/dev`; nenhuma foi introduzida pelos ajustes desta sequência. Foram verificadas na execução isolada registrada em `%TEMP%\komyst-isolated-backup.log`. **Classificação atualizada em 11/11:** três dos quatro testes de máscara são dependentes da versão OpenCV (o dono confirma que passam no ambiente 5.0.0); resta uma falha real de código. A classificação detalhada ao final supersede a leitura inicial deste parágrafo.

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

## Rechecagem após a correção de F0.8 — 2026-11-11

Na suíte completa executada nesta checkout (`C:\Projetos\Yomu-Sekai`, `fase-0-jobs-nao-morrem`, commit `5427455`), as quatro falhas de máscara/reconstrução continuam reproduzíveis: **6.499 passed, 4 failed, 141 skipped, 1 xfailed, 8 warnings e 787 subtests passed**, em 917,27 s. Cada um dos quatro testes também falhou quando executado isoladamente em um processo pytest separado. O Python usado foi `C:\Users\henri\AppData\Local\Programs\Python\Python311\python.exe`, importando `yomu` de `C:\Projetos\Yomu-Sekai\yomu`; OpenCV 4.10.0, NumPy 2.3.5, sem `PYTHONPATH` ou `PYTHONHOME` configurados.

Esta evidência **não reproduz** o resumo externo de 6.502 aprovados/1 falho nem a alegação de que três dos quatro testes passaram isoladamente em `bc02f38`. Não é efeito da ordem: os quatro falham tanto isolados quanto na suíte completa. Não é contaminação pelos PNGs: os quatro fixtures que falham são sintéticos e não leem `dbg_hur_2x.png`, `flux_p9_test.png` ou `C:\tmp\selo-raw.png`. Também não há diferenças nos arquivos de máscara e nesses testes entre `bc02f38` e o HEAD atual (`git diff` vazio). A origem da divergência restante é compatível com ambiente/importação diferente no relatório externo, mas **não está comprovada** porque não veio acompanhado do executável Python, versões de NumPy/OpenCV e `yomu.__file__` usados naquele teste. Não registrar os três como resolvidos até repetir com esses dados.

Na F3.0, confirmar os três casos dependentes sob o runtime OpenCV 5.0.0 e bisectar a única falha real; não alterar resultados por ajuste de teste sem evidência de contrato desatualizado.

## Classificação após confirmar o OpenCV efetivo — 2026-11-11 (atualização conclusiva)

O dono confirmou que, usando OpenCV 5.0.0 do ambiente com `opencv-python-headless`, os três primeiros testes abaixo passam e resta uma falha real. Nesta sessão não foi instalado nem removido pacote. O comando solicitado retornou, tanto com `python` quanto com `python -s`:

```text
4.10.0 C:\Users\henri\AppData\Local\Programs\Python\Python311\Lib\site-packages\cv2\__init__.py
```

O executável da sessão é Python 3.11. A pasta `Roaming\Python311\site-packages` não contém `cv2`; os metadados globais desta sessão mostram `opencv-python 5.0.0.93` e `opencv-contrib-python 4.10.0.84` instalados lado a lado no mesmo `site-packages`, enquanto `opencv-python-headless` não está instalado aqui. O módulo efetivamente importado é 4.10.0. Isso confirma um conflito local entre distribuições que compartilham o diretório top-level `cv2`. A sessão não trocou nem removeu pacotes; a instalação/correção do ambiente aguarda decisão do dono. O resultado com OpenCV 5.0.0 citado abaixo é evidência fornecida pelo dono, não foi reproduzido nesta sessão.

| Teste | Resultado efetivo nesta sessão com OpenCV 4.10.0 | Classificação para F3.0 |
|---|---|---|
| `GlyphFootprintCoverage::test_punctuation_outside_the_polygon_is_still_covered` | Falha: `GLYPH_ART_BOUNDARY_UNCERTAIN`; reprovou no `python` normal e em `python -s` | Dependente do OpenCV; dono reporta que passa com 5.0.0. Não corrigir código antes de validar no runtime fixado. |
| `MaskGeometryDiagnostics::test_crossing_line_art_overlap_is_measured_for_follow_up` | Falha: esperava `mask_valid=False`, recebeu `True`; reprovou normal e `-s` | Dependente do OpenCV; dono reporta que passa com 5.0.0. Não corrigir código antes de validar no runtime fixado. |
| `test_large_glyph_components_are_kept_and_background_shapes_dropped` | Falha: componente `MW` classificado como forma de fundo; reprovou normal e `-s` | Dependente do OpenCV; dono reporta que passa com 5.0.0. Não corrigir código antes de validar no runtime fixado. |
| `test_text_touching_a_balloon_border_is_cleaned_without_erasing_the_border` | Falha: `residual_source_text_after_cleanup`/máscara toca a borda; o dono reporta que é a única falha restante com OpenCV 5.0.0 | Falha real de código a bisectar e corrigir em F3.0. |

Com esta classificação, três falhas são dependentes da versão do OpenCV e uma é falha real de código. A antiga interpretação de “quatro falhas de código” e os quatro resultados locais sob OpenCV 4.10.0 ficam supersedidos: medições de teste executadas nesta sessão com esse módulo não representam o ambiente fixado de 5.0.0. A F3.0 deve confirmar as três no runtime correto e bisectar/corrigir a quarta; aceite final continua sendo a suíte verde nesse ambiente.
