# Perguntas e dependências pendentes — Fase 0

Atualizado: 2026-11-11 (noite)

Nenhuma pendência física aberta. As dependências anteriores foram fechadas pelo dono com o agente revisor, que iniciou os dois jobs pelo painel já autenticado.

## Resolvido — intervalo do monitor na instalação local

`.env` linha 79 alterado para `RESOURCE_MONITOR_INTERVAL_SECONDS=10.0` com autorização do dono. Os jobs pelo painel registram `interval_seconds: 10.0`.

## Resolvido — F0.8 pelo painel (Apenas Clean)

Causa: a exceção para página que fica em branco após limpeza certificada só existia em dois dos sete pontos que validam a página. No worker por página ela rodava antes do certificado existir (`imagem final invalida`); corrigida a ordem, as etapas seguintes ainda descartavam a página (`required_artifact_missing`). Correção em `6c4734b`: todas as etapas usam `_page_output_is_valid`.

Validação pelo painel, job `5731a21a89184e07b319041f1ee46aa2`: `review_required`, 65/65 imagens limpas no manifesto, cartão "concluído — revisão recomendada", DirectML, monitor 4,35 s de 404,26 s (1,08%). A página 10 segue em revisão (pré-existente na `dev`, vai para a Fase 3).

## Resolvido — REF-A `Tradução pronta` (job pago)

Job `abee15719bd346bc86197faaf9307d43`, pelo painel: `review_required`, 377,90 s, DirectML, 57/58 traduzidos, 62 páginas com certificado `verified` (igual à base: 54 + 8 sem texto), gate físico aprovado com 0 resíduos. Página 23: FLUX `ok` em 20,45 s, uma tentativa, sem log de erro. A nova tentativa da F0.9 não foi exercitada por falha real; segue coberta só por teste simulado.

## Para decidir (dono)

- Aprovar o merge da Fase 0 em `dev`.
- O botão do painel fica em "PROCESSANDO..." depois que um job falha, até recarregar a página. Observado em 11/11 após o job `7a538acf2e654069a262a72d3e221546`; não investigado.
- Suíte completa em `6c4734b`: 6.502 passaram, 1 falhou (`test_text_touching_a_balloon_border_is_cleaned_without_erasing_the_border`, antiga). As outras três falhas antigas de máscara passaram nesta rodada, isoladas e também em `bc02f38` numa worktree, então a mudança não vem do código desta correção. Causa não investigada; conferir antes da F3.0 se dependem do ambiente.
