# Fase 3 — diagnóstico inicial (2026-11-12)

Branch: `fase-3-qualidade`, base `dev`/`origin/dev` `631afac`. OpenCV 5.0.0 foi confirmado por `python` e `python -s`; ONNX Runtime lista `DmlExecutionProvider`.

## F3.0 — texto tocando a borda do balão

### Bisect corrigido

O bisect anterior era inválido: `git -C` aplicou o cwd apenas ao comando Git, e o pytest importava `yomu` de `C:\Projetos\Yomu-Sekai` em todos os pontos. Um runner novo imprimiu `yomu.__file__` em cada revisão e forçou o caminho da worktree `C:\Users\henri\AppData\Local\Temp\komyst-f3-bisect-20261112\yomu`. Com esse isolamento, `d819f0e` passa, `cda3f90` passa e o bisect válido entre `d819f0e` e `631afac` aponta `80f0620` como primeiro commit ruim. Portanto `_refine_lettering_mask` em `cda3f90` não explica o caso speech; ele retorna sem alterar não-SFX e o commit passa no teste isolado quando importado corretamente. `80f0620` é um commit abrangente (+2058/-300, 28 arquivos, incluindo 1064 linhas alteradas em `ocr_balloon.py`); o hunk preciso ainda precisa ser delimitado.

### Contrato escolhido e tentativas

Contrato: a máscara nunca inclui o contorno detectado de balão fechado. A tinta OCR que coincide com a faixa estreita do contorno é intencionalmente preservada; a validação de resíduo a exclui somente quando também coincide com uma aresta original nessa faixa. Resíduo fora dela continua reprovando. A escolha preserva estrutura já existente; reconstruir uma curva encoberta exigiria estimar arte que não está observável.

- Tentativa 1: permitir detecção de enclosure fechado também para fala. O inset de 1 px ainda deixava 18 pixels da máscara sobre a borda. Falhou.
- Tentativa 2: inset proporcional maior e exclusão localizada de resíduo no contorno. O teste passa os requisitos de máscara sem interseção e arco preservado, mas falha no residual: 80 pixels residuais, maior componente 76 (mesmo com pixels de borda protegidos reportados). 1 falha, 3 testes focados adjacentes passaram.
- Encerradas as tentativas de correção nesta rodada conforme limite de duas. Mantive o diff não commitado para inspeção; suíte completa e REF-A Apenas Clean não foram rodados após essa alteração. Critério do Clean continua comparar certificados com a base OpenCV 5.0.0 de 288,7 s.

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

A evidência mostra que F3.1 depende de F3.2 para palavras coladas e de separar SFX de frase mista nas páginas 24 e 65. A regra estrita não promoveria automaticamente nenhum dos seis itens sem essas distinções. Não alterei comportamento de classificação nem iniciei tradução paga. A próxima tarefa de código mais independente é F3.2, respeitando as restrições de segmentação e completude do plano.
