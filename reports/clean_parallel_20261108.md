# CLEAN e paralelismo — 08/11/2026

Estado: IMPLEMENTED / TESTED_OFFLINE / TESTED_FROZEN no checkout local. Sem integração à main ou publicação. Referência: Hero Killer, episódio 285, último job concluído `f3de3bca6a8a479aa388b7a7c4fbff63`, saída `0fd7358a-8c5a-469a-9ee7-f7fef965682d`. Os arquivos desse job foram preservados; as imagens corrigidas são ensaios separados, não uma revisão publicada daquele capítulo.

## Resultado medido

Reexecutamos as 65 páginas com a mesma análise OCR, traduções congeladas, preflight e reconstrução canônicos, modelos locais reais e escrita de CLEAN/traduzidas. Não houve chamadas aos provedores pagos. Comparação em processos separados:

| Medida | 1 worker | 2 workers |
| --- | ---: | ---: |
| Preflight + reconstrução + escrita | 196,43 s | 133,67 s |
| Preflight dentro dessa medição | 165,30 s | 117,75 s |
| Pico amostrado RSS | 8,24 GiB | 8,65 GiB |
| Pico de memória privada | 13,51 GiB | 13,62 GiB |
| Menor RAM disponível no sistema | 2,09 GiB | 1,83 GiB |

Redução de **31,95%** no tempo dessa fase, aproximadamente 63 segundos. As **130/130 imagens foram idênticas pixel a pixel**, sem diferenças de disposição dos grupos e sem erros em ambas as variantes. Dados: [comparação JSON](data/clean_parallel_20261108.json).

Esta medição não inclui download, OCR, sweep, tradução externa ou PDF. Não permite anunciar 32% de redução no capítulo inteiro, nem garantir menos de cinco minutos. O job original levou 545,88 segundos; seu preflight foi 197,16 s e sua análise anterior à tradução, 149,28 s de parede. Tempos acumulados de regiões/páginas sobrepostas não devem ser somados como tempo de parede.

`PIPELINE_PAGE_WORKERS=2` foi configurado somente nesta instalação. O padrão distribuído continua `auto`. A inferência DirectML continua protegida pelo lock compartilhado: paralelizamos preparação e processamento das páginas sem duplicar modelos na GPU. Quatro workers não foram homologados. A margem de RAM observada ainda é pequena com outros aplicativos abertos.

## Por que sobravam SFX

- **Página 5, BLAZE:** a classificação já era SFX do glossário, mas carregava o veto antigo `weak_unknown_text`. A promoção agora atualiza a política. A seleção de CLEAN reconhece também esse estado antigo específico sem liberar nomes, créditos ou qualquer grupo desconhecido.
- **Página 12, CRACKLE:** uma caixa OCR enorme, rejeitada, ainda era tratada como texto resolvido pela sweep e escondia quase o painel inteiro da releitura. Caixas rejeitadas deixam de ocultar a região; o reparo exige uma nova detecção. A leitura Paddle real retornou CRACKLE com confiança 0,981. O refinamento também descartava o E menor por um piso de área alto; agora seleciona componentes menores mediante tinta preta e anel branco medidos, rejeitando os componentes de arte sem essa assinatura.
- **Página 3, RUMBLE:** o teto geométrico do polígono OCR inclinado cortava pontas das letras antes da máscara v4. O teto agora inclui as caixas das linhas pertencentes ao grupo, com margem limitada. Isso não transforma a caixa em máscara: a função v4 continua decidindo os pixels removíveis. As pontas foram removidas e a borda do quadro preservada.
- **Páginas 6 e 10:** a releitura real recuperou CRACKLE (0,941), PSHHH (0,970) e FLICK (0,999). Uma sequência repetida como PSHHH era descartada como ruído mesmo com leitura forte. A exceção agora exige origem Paddle da sweep, confiança mínima de 0,90, recuperação registrada e assinatura visual de glifos comprovada. Leituras comuns, fracas ou sem prova visual continuam rejeitadas. As três regiões passaram pela limpeza e validação locais no replay das detecções reais.

**A implementação de `_sfx_glyph_halo_mask` v4 não foi alterada.** Não removemos os validadores de fonte, máscara, cobertura ou arte. As correções recuperam candidatos e geometria antes desse contrato.

## Por que o paralelismo exigia correção

Workers de preflight/render criavam registradores de proveniência vazios. Aumentar concorrência sem corrigir isso podia perder a prova de origem necessária à limpeza. Cada worker agora recebe uma cópia isolada da fonte da sua página; o merge acrescenta apenas eventos novos, sem duplicar as linhas copiadas. Grupos recuperados pela sweep são registrados novamente após receberem seu ID definitivo. A promoção de texto decorativo também é serializada e restaurada no estado de revisão.

## Páginas CLEAN sem diferença

Foram encontradas 14 páginas idênticas ao original: 5, 11, 12, 17, 24, 44, 45, 46, 51, 53, 57, 61, 62 e 65. Isso mistura páginas sem remoção elegível, conteúdo protegido e os SFX perdidos descritos acima; não significa que todas sejam páginas vazias.

Essas páginas tiveram tempo de render registrado zero. Sua escrita somou 4,90 s, muito abaixo do preflight. A sequência completa de 65 arquivos é mantida para alinhar original/CLEAN/traduzido e os contratos de exportação; copiar uma página sem alteração não executa LaMA desnecessariamente. Excluir esses arquivos quebraria esse alinhamento sem resolver o principal gargalo.

Com SFX desligado, CLEAN remove o SFX elegível e aprovado, enquanto o final/PDF preserva o SFX original. A configuração continua controlando a tradução/composição final, não a existência da limpeza.

## Evidência e limites

Regressão no snapshot final: **470 passed, 1 skipped, 393 subtests passed**
(65,51 s), incluindo proveniência, completude da fonte, preferências SFX, sweep,
escopo de máscara, contratos de página, serialização, reconstrução seletiva e
replays locais de pipeline. `git diff --check` e sintaxe do quadro passaram.
Hash SHA-256 do trecho AST da função v4 antes/depois:
`b6398cbb839a6df4c36974130cc952aef2ec8263018cf55864781fddda7bdb22`.

Ensaios e imagens completas ficam em `%LOCALAPPDATA%/TradutorIA/runtime/performance_validation/clean_speed_20261108/`: `final_full/workers_1`, `final_full/workers_2`, `comparison.json`, `uncertain_resweep_final.json` e `page_006_recovered_clean.png` / `page_010_recovered_clean.png`. O primeiro ensaio anterior ao ajuste do E não é a evidência final. A comparação final usa `states_final.pkl`; quatro linhas sem cache de polígono usam a geometria retangular do snapshot. A promoção decorativa omitida no debug antigo foi reconstruída somente quando o predicado canônico aceitou a fonte/contexto.

A recuperação adicional das páginas 6/10 foi medida separadamente do A/B de 65 páginas e pode acrescentar trabalho ao próximo job. Não há promessa de limpar 100% dos SFX desconhecidos: regiões sem fonte confiável ou com reconstrução reprovada continuam em revisão.

Impacto documental: estratégia CLEAN, configuração e quadro local atualizados. Gate físico pendente: novo job completo no capítulo de referência com o código/configuração atuais para medir tempo total e conferir os artefatos canônicos. Os ensaios congelados não substituem essa validação ponta a ponta.
