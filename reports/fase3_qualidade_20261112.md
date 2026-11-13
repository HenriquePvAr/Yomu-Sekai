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

Na primeira tentativa, a regra promoveu texto decorativo com três ou mais palavras comuns, inclusive placas e metadados. Essa ampliação foi revertida após o REF-B físico mostrar uma regressão na página 20; veja a revisão abaixo. A tentativa inicial não será commitada.

**REF-A Apenas Clean CLI pós-F3.1** (`komyst_f3_1_refa_clean`): DirectML, 65 PNGs, 317,87 s, sweep 95,05 s, 54 certificados, 8 páginas sem texto comprovado e 3 em revisão (p10/p22/p23). Esta rodada não habilitou FLUX e não é comparável ao job físico de referência que teve p23 aprovada.

**Repetição Clean com FLUX no processo** (`komyst_f3_1_refa_clean_flux`): DirectML, 65 PNGs, 327,79 s, sweep 103,32 s, 54 certificados, 8 sem texto comprovado e 3 em revisão (p10/p22/p23). O `errors/flux_023_REGION_001.log` confirma falha de alocação Vulkan na RX 6600: tentou reservar buffers de 1,85 GB e recebeu `ErrorOutOfDeviceMemory` após 1,50 s. Esse resultado continua inconclusivo para a p23 e não é atribuído ao patch.

### Revisão da F3.1 após o REF-B físico (2026-11-13)

O dono informou o resultado do REF-B Completo, job `03f4314c…`, comparado com a base `c7ee941a…`: traduções subiram de 169 para 170, páginas em revisão de 15 para 16 e resíduos ficaram em 7. A única tradução adicional foi a placa de loja da página 20 (`POTATO — King of French…`), traduzida como “BATATA, a rainha da culinária francesa” em uma caixa preta sobre a arte. A limpeza local terminou `LOCAL_HARD` e não havia fallback remoto configurado; a página perdeu o certificado. Esse é um efeito visível indevido, então a promoção por texto isolado não será mantida.

**Contrato revisto:** no caminho novo `_legible_sentence_promotion_allowed`, a frase legível só é promovida se o vínculo estrutural (`inside_balloon_like_region`, `inside_narration_box_like_region` ou `parent_balloon_id`) concordar com o fundo local (`white_balloon`, `dark_balloon` ou `narration_box`). O job mostrou que uma flag de narração pode ser herdada incorretamente: na placa da p20 `inside_narration_box_like_region=true`, mas `background_type=textured_art` e as métricas locais de narração/enclosure eram falsas. Sem contêiner confirmado, esse caminho novo mantém o grupo em arte preservado. As rotas antigas de recuperação não foram alteradas, pois a tentativa de bloqueá-las também impediu o resgate legítimo da p70. A regra nova é genérica e não depende de página, texto nem série.

Após o primeiro teste físico, a correção foi estreitada: a exigência estrutural aplica-se somente ao novo caminho `_legible_sentence_promotion_allowed`, usado na política final e na checagem de autoridade para essa promoção. As rotas antigas de recuperação de frases em arte texturizada e legendas curtas permanecem inalteradas, pois bloqueá-las causou uma revisão nova na página 70. Testes da área: **288 passed, 1 skipped, 386 subtests**. Incluem letreiro sintético sem contêiner (com flag herdada, preservado) e frase em caixa de narração (promovida). A validação física subsequente e a suíte completa fecharam os critérios antes do commit da implementação.

**Validação física pós-correção, REF-B Completo pelo painel (13/11):** job `674078a0f47142d38d1f09742266752c`, run `dca7ca2b-f7c6-4cd7-a70e-6755bb29017c`, commit `1da3347`, OpenCV 5.0.0 e OCR/LaMa em DirectML. Terminou `review_required` em 533,57 s, com 169/177 traduções, 70/85 certificados (69 páginas certificadas + 1 sem texto comprovado), 15 páginas em revisão e 7 resíduos. O conjunto de revisão foi `[2,13,24,30,34,48,53,54,65,68,72,75,77,80,85]`, igual ao conjunto da base anotado na comparação anterior; nenhum novo certificado foi perdido. A pasta do run base `c7ee941a…` não está mais no diretório de saída, então não foi possível repetir `job_metrics.py --compare` contra os arquivos originais; a comparação usa os totais e a lista de páginas da base registrados anteriormente neste relatório/artefatos da sessão.

Na página 20, `BALAO_2` (`POTATO King ofFrench`) ficou `decorative`, sem tradução, com `preserved_original=true`; a imagem final mostra a placa intacta. A validação física satisfaz os critérios da F3.1: pelo menos 169 traduções, no máximo as 15 páginas em revisão da base e placa da p20 preservada. Ganho líquido medido nos capítulos de referência: **zero traduções adicionais**; REF-A manteve 57/58 e REF-B 169/177. O valor da F3.1 é não regredir a fidelidade e preparar a F3.2, não aumentar o recall nesta medição. Pico RSS da árvore: 3.216,45 MB; monitor: 53 amostras, 3,56 s/533,57 s (0,67%), intervalo 10 s. O job não passou o portão físico global, como a base: os mesmos 7 resíduos permanecem.

O dono informou que o REF-A Tradução pronta manteve 57/58 traduções, igual à base; a página 51 apareceu adicionalmente em revisão, sem mudança de tradução atribuída à F3.1. A p23 falhou no FLUX por `ErrorOutOfDeviceMemory` ao tentar alocar 814 MB mesmo com a GPU livre no início do job; medir VRAM dedicada e avaliar liberação/retry fica para as Fases 1/5. O erro de nome próprio “Seon-ho” → “Seen-ho”, presente nos dois jobs, fica para F3.2. A varredura de resíduos custa aproximadamente 100 s por capítulo; otimizar para páginas com sinal permanece na Fase 2.

## DOCUMENTATION IMPACT

- Plano e registro de falhas: atualizaram causa em `80f0620`, contrato, prova física e a nova referência de tempo saudável; os valores antigos estão identificados como ambiente degradado. O teste da borda e a suíte completa da versão final passaram.
- Fase 2: adicionada avaliação de varredura somente em páginas com sinal e telemetria explícita `residual_sweep: unavailable` se o Paddle não iniciar.
- Quadro: F3.0 fisicamente validada; suíte final aprovada, commit F3.0 isolado e F3.1 em andamento.
- F3.1: commit de código/testes `7933f64`; suíte completa **6.513 passed, 141 skipped, 1 xfailed, 8 warnings, 787 subtests**. Ganho líquido de traduções nos capítulos de referência: zero; o resultado preserva qualidade e prepara a F3.2. Validação REF-B pós-correção: 169/177, 70/85, mesmas 15 páginas em revisão e 7 resíduos; placas p20 e caso p70 em PASS.
- Pendências futuras: medir VRAM dedicada durante FLUX e avaliar liberação das sessões DirectML ou retry após intervalo (Fases 1/5); corrigir “Seon-ho” → “Seen-ho” na F3.2.
- Commits da F3.1 são separados: implementação/testes `7933f64`; documentação e quadro em commit posterior.
- Sem merge, push ou alteração de `.env`.
