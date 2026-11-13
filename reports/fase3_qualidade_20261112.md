# Fase 3 — qualidade (atualizado em 2026-11-13)

Branch: `fase-3-qualidade`, base `dev`/`origin/dev` `631afac`. OpenCV 5.0.0 foi confirmado por `python` e `python -s`; ONNX Runtime lista `DmlExecutionProvider`.

## F3.0 — texto tocando a borda do balão

### Patch validado pelo dono — validação física concluída

- Guardei as duas tentativas anteriores com `git stash push -m "f3.0-tentativas-contorno" -- tests/test_pipeline_candidate_page_fixes.py yomu/ocr/ocr_balloon.py`; o stash foi preservado. Apliquei `reports/f3_0_patch_validado.diff` e removi o diff depois de aplicar.
- O patch implementa `_long_stroke_halo_barrier`, reutilizando `_balloon_border_mask`: impede que o halo novo passe por traços longos de mesma polaridade e nunca reduz pixels da máscara base. O teste de área passou: `tests/test_pipeline_candidate_page_fixes.py` — 39 passed. Ambiente confirmado: OpenCV 5.0.0 em `python` e `python -s`; ONNX Runtime oferece DirectML.
- O dono confirmou pelo painel que o REF-A Apenas Clean saudável (job `39a41cbb…` e anteriores, GPU livre, OpenCV 5.0.0) certifica p23 com FLUX; somente p10 e p22 ficam em revisão. São 65/65 páginas produzidas. A execução saudável do medidor mais recente registra 329,43 s, com Paddle funcional.
- O REF-B Completo físico `c7ee941a073945db82a225d48a435c48` terminou em `review_required` em 480,62 s: 169/177 traduzidas, 70/85 certificadas e 7 resíduos, sem queda contra a base `278c2486`.
- As execuções anteriores com p23 em revisão e erro Vulkan (`ErrorOutOfDeviceMemory`) permanecem como histórico de falha transitória do FLUX, substituídas pela validação física posterior em que p23 passou. Não alteraram `.env` nem o patch.
- A linha de base antiga de REF-A Apenas Clean (288,7 s) e Tradução pronta (278,2 s) foi medida em ambiente degradado: Paddle não iniciou, `residual_sweep` levou 2,7 s, houve 0 correções automáticas e 217 linhas OCR contra 225 com Paddle funcional. A nova referência saudável é aproximadamente 330 s para Apenas Clean, com sweep em torno de 100 s. Job REF-B validado pelo medidor: 480,62 s; `residual_sweep` foi 68,25 s neste run específico.
- A suíte completa da versão final do patch, em OpenCV 5.0.0 e DirectML disponível, terminou com **6.504 passed, 141 skipped, 1 xfailed, 8 warnings e 787 subtests**, em 883,71 s. O teste `test_text_touching_a_balloon_border_is_cleaned_without_erasing_the_border` passou isoladamente: **1 passed**.

### Bisect corrigido

O bisect anterior era inválido: `git -C` aplicou o cwd apenas ao comando Git, e o pytest importava `yomu` de `C:\Projetos\Yomu-Sekai` em todos os pontos. Um runner novo imprimiu `yomu.__file__` em cada revisão e forçou o caminho da worktree `C:\Users\henri\AppData\Local\Temp\komyst-f3-bisect-20261112\yomu`. Com esse isolamento, `d819f0e` passa, `cda3f90` passa e o bisect válido entre `d819f0e` e `631afac` aponta `80f0620` como primeiro commit ruim. Portanto `_refine_lettering_mask` em `cda3f90` não explica o caso speech; ele retorna sem alterar não-SFX e o commit passa no teste isolado quando importado corretamente. A causa foi delimitada: `80f0620` generalizou `_refine_lettering_mask` de SFX para todo grupo, e sua dilatação cega de 2 px invadiu o arco.

### Contrato escolhido e tentativas

Contrato: a máscara nunca inclui o contorno detectado de balão fechado. A tinta OCR que coincide com a faixa estreita do contorno é intencionalmente preservada; a validação de resíduo a exclui somente quando também coincide com uma aresta original nessa faixa. Resíduo fora dela continua reprovando. A escolha preserva estrutura já existente; reconstruir uma curva encoberta exigiria estimar arte que não está observável.

- Tentativa 1: permitir detecção de enclosure fechado também para fala. O inset de 1 px ainda deixava 18 pixels da máscara sobre a borda. Falhou.
- Tentativa 2: inset proporcional maior e exclusão localizada de resíduo no contorno. O teste passa os requisitos de máscara sem interseção e arco preservado, mas falha no residual: 80 pixels residuais, maior componente 76 (mesmo com pixels de borda protegidos reportados). 1 falha, 3 testes focados adjacentes passaram.
- As duas tentativas iniciais falharam e foram preservadas em stash. O patch validado posterior substitui essas tentativas; o diff de origem foi aplicado e removido. Consulte a subseção de validação física acima para os gates ainda pendentes.

## F3.1 — auditoria do REF-B existente, sem job novo

Fonte: `progress.json` do job `a9a1339d8157423eacb561d402d24494` / run `e125e16c-698e-480b-86fd-37d458c46fb3`, REF-B Completo em `review_required`, OpenCV 5.0.0, DirectML. Entre itens com `ignore_reason` `decorative_text` ou `weak_unknown_text`, a extração encontrou:

| Página | Região | Texto OCR | Confiança | Fundo | Palavras de dicionário / total | Elegibilidade preliminar da regra F3.1 |
|---:|---|---|---:|---|---:|---|
| 18 | BALAO_2 | `CLUNK-.` | 0,890 | narration_box | 1/1 | Uma palavra/onomatopeia; não promover como frase.
| 20 | BALAO_2 | `POTATO King ofFrench` | 0,955 | textured_art | 2/3 antes de split | Precisa F3.2 separar `ofFrench`; não tem pontuação, depois da separação terá 4 palavras e poderá cumprir regra. Revisar contexto de título/placa.
| 24 | BALAO_4 | `PFFT. HOW CUTE,` | 0,907 | unknown | 2/3 | `PFFT` não é palavra comum; a promoção integral falha a regra. Separar efeito e frase antes de decidir, sem converter o SFX em fala.
| 28 | BALAO_2 | `FROWN` | 0,992 | narration_box | 1/1 | Uma palavra; não promover.
| 41 | BALAO_2 | `CALLING THECEO` | 0,988 | textured_art | 1/2 | Precisa F3.2 separar `THECEO`; duas palavras sem pontuação ainda não satisfazem o limiar de frase.
| 65 | BALAO_2 | `LOL! GOOD LUCK.` | 0,878 | textured_art | 2/3 | Confiança abaixo de 0,90; `LOL` precisa tratamento semântico próprio, não pode ser incluído por exceção implícita.

A evidência mostra que F3.1 depende de F3.2 para palavras coladas e de separar SFX de frase mista nas páginas 24 e 65. A implementação local de F3.1 já foi iniciada, sem tradução paga. A regra exige confiança ≥0,90, duas ou mais palavras, palavras de três ou mais letras no dicionário, pontuação ou pelo menos três palavras e exclusões para SFX, créditos, URL, marca da série e entidades preservadas. O helper segmenta palavras coladas antes da avaliação.

Testes de F3.1 e regressão da área: **287 passed, 1 skipped, 386 subtests**. Quatro testes antigos de classificação foram atualizados para refletir a promoção intencional de texto decorativo legível com três ou mais palavras comuns (inclusive pequenos letreiros e metadados). A escolha foi registrada porque a nova regra aumenta recall de texto em arte; permanece pendente validação visual paga, que depende de ação do dono.

**REF-A Apenas Clean CLI pós-F3.1** (`komyst_f3_1_refa_clean`): DirectML, 65 PNGs, 317,87 s, sweep 95,05 s, 54 certificados, 8 páginas sem texto comprovado e 3 em revisão (p10/p22/p23). Esta rodada não habilitou FLUX e não é comparável ao job físico de referência que teve p23 aprovada.

**Repetição Clean com FLUX no processo** (`komyst_f3_1_refa_clean_flux`): DirectML, 65 PNGs, 327,79 s, sweep 103,32 s, 54 certificados, 8 sem texto comprovado e 3 em revisão (p10/p22/p23). O `errors/flux_023_REGION_001.log` confirma falha de alocação Vulkan na RX 6600: tentou reservar buffers de 1,85 GB e recebeu `ErrorOutOfDeviceMemory` após 1,50 s. Assim, o resultado com um certificado a menos que a execução anterior informada pelo dono (p10/p22 apenas em revisão, FLUX aceito na p23) está **inconclusivo e bloqueia o aceite físico da F3.1**; não atribuir a diferença ao código sem FLUX concluído. Pico RSS da árvore 6.758,5 MB; amostragem 2,15 s/327,79 s (0,66%), intervalo 10 s. Nenhuma tradução paga foi iniciada.

## DOCUMENTATION IMPACT

- Plano e registro de falhas: atualizaram causa em `80f0620`, contrato, prova física e a nova referência de tempo saudável; os valores antigos estão identificados como ambiente degradado. O teste da borda e a suíte completa da versão final passaram.
- Fase 2: adicionada avaliação de varredura somente em páginas com sinal e telemetria explícita `residual_sweep: unavailable` se o Paddle não iniciar.
- Quadro: F3.0 fisicamente validada; suíte final aprovada, commit F3.0 isolado e F3.1 em andamento.
- F3.1: helper e testes estão no working tree, sem commit. O teste da área passou; validação Clean com FLUX ficou inconclusiva por `ErrorOutOfDeviceMemory` na p23. Sem tradução paga.
- Sem merge, push ou alteração de `.env`.
