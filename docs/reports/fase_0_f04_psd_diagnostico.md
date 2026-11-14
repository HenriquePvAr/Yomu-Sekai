# F0.4 — Diagnóstico das saídas PSD

Data: 2026-11-11  
Execução analisada: REF-A `f181a17e-281d-40a8-bd7e-41b4bbdcdca1`, página 1.  
Escopo: inspeção somente leitura. Nenhum PSD foi alterado.

## Comparação dos arquivos

| Caminho relativo à execução | Tamanho | Camadas (nome — tipo) |
|---|---:|---|
| `psd/001.psd` | 5.329.162 bytes | `ORIGINAL` — grupo; `ORIGINAL_ART` — imagem; `CLEAN` — grupo; `CLEAN_ARTWORK` — imagem; `TEXT` — grupo; `TEXT_001_REVIEW` — texto nativo; `TEXT_002` — texto nativo |
| `hero_killer_episode_285/0001.psd` (`result_path`) | 5.445.774 bytes | `Original` — imagem; `Cleaned` — imagem; `Text/Region 001` — texto nativo; `Translated Preview` — imagem |

Os tipos foram lidos recursivamente pelo `psd-tools`; os objetos `kind=type` contêm texto extraível e são camadas de texto editáveis. Na página analisada, `psd/` contém `HERO KILLER` na camada `TEXT_001_REVIEW` e o crédito em `TEXT_002`. O PSD de `result_path` contém o crédito em `Text/Region 001` e acrescenta a prévia rasterizada traduzida. Portanto, as saídas compartilham algumas camadas, mas não são duplicatas: cada uma tem conteúdo próprio.

## Consumidores confirmados

- **Interface — pasta `psd/`:** a ação “PSDs editáveis” usa `UiBridge.open_artifact_for_owner(..., "psd_folder")`, resolve `output_folder / "psd"` e valida a existência de PSDs. A tela habilita a ação com a disponibilidade do artefato `editable_psd`.
- **Manifesto de artefatos — pasta `psd/`:** `ArtifactType.EDITABLE_PSD` usa o caminho canônico `psd/NNN.psd`; o pipeline registra cobertura, páginas produzidas e bytes em `artifact_manifest.json`.
- **Interface/histórico — `result_path`:** o job runner grava o `psd_path` retornado pelo exportador profissional como `result_path` e `psd_path` do manifesto de execução. O histórico e o resumo do job usam esse caminho para o resultado do formato `psd`.
- **Testes:** `tests/test_artifact_contract.py` fixa o contrato `psd/001.psd`; `tests/test_editable_psd_writer.py` valida o PSD nativo e a produção de camadas; `tests/test_professional_psd.py` e `tests/test_professional_psd_quality_e2e.py` cobrem a saída do exportador profissional; `tests/test_job_completion_summary.py` verifica a ação da interface.

## Conclusão

A premissa de “uma cópia PSD escrita duas vezes” não se confirma. São duas saídas PSD com contratos e consumidores diferentes, e ambas contêm texto editável nativo. A F0.4 não remove nem redireciona uma delas; qualquer consolidação exigirá primeiro uma decisão de produto sobre preservar as diferenças de conteúdo. Critérios de bytes por página foram removidos da PAUSA 0 até essa decisão.
