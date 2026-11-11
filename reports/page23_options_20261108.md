# Opções verificadas para a página 23

08/11/2026 — experimentos locais sobre a página congelada do run
`833e2624-2a8c-4994-90eb-8b58dc8d0a5c`. Não foi executado outro capítulo nem
chamado provider de tradução. Nenhum artefato do job original foi substituído.

## Resultado e recomendação

A alternativa visualmente mais promissora foi **FLUX.2 Klein por recorte, em edição
por referência, seguido de composição com máscara do efeito tipográfico completo**:
tinta, espaços internos das letras e brilho roxo, com borda suavizada. As linhas
brancas fortes do original foram explicitamente preservadas.

A prévia remove a caixa preta e o lettering antigo e mantém o fundo violeta com
raios. A fonte traduzida usa a família serifada aproximada detectada no original.
Ela permanece **candidata para revisão**: os gates atuais de cor e de manchas
escuras a recusam. A máscara mais ampla também precisa de um contrato explícito
de propriedade do halo para entrar no pipeline. Não foi promovida automaticamente.

Recomendo um caminho de fidelidade máxima **por região difícil**, preservando a v4
para SFX. Não recomendo executar FLUX em todas as regiões: cada edição local por
recorte custou aproximadamente 20 s, incluindo carga do modelo.

## Evidências e comparação

Diretório local:
`%LOCALAPPDATA%\TradutorIA\runtime\performance_validation\20261108_page23_options\`.

- `best_translated_comparison.png`: original, último job e melhor prévia traduzida.
- `effect_mask_comparison.png`: composição com três extensões do halo.
- `comparison.png`: LaMa e caminho inicial de FLUX, incluindo tentativas reprovadas.
- `results.json`, `effect_mask_results.json` e `independent_gate_diagnostics.json`:
  medidas e motivos de recusa.
- `flux_mask_controlled_ab.json` e logs do CLI: comparação controlada da chamada.
- Os scripts usados estão nesse mesmo diretório para permitir inspeção/reprodução.

O OCR de referência leu `DAEMON` e `LASERBLAST` no original. Na melhor composição,
ele retornou somente traços/pontuação dos raios; nenhuma dessas palavras foi lida.
Isso é evidência de remoção, não prova da fidelidade de uma arte que estava oculta.

## 1. Completar as letras antes de reconstruir

A máscara anterior cortava partes do N e do T nas bordas do OCR. Uma extração
diagnóstica de tinta escura, com busca além dessas bordas e seleção de componentes
com altura de letra, recuperou **6/6 componentes em DAEMON e 10/10 em LASERBLAST**.
Não foram usados componentes claros entre letras como se fossem a tinta preta.

Essa correção é necessária, mas não basta. O efeito não contém apenas tinta:
há brilho roxo bem mais largo e também brilho dentro dos espaços de A/O/B/R.
Deixar esses espaços fora da máscara mantém a silhueta das palavras no limpo.

Os parâmetros deste experimento foram escolhidos para essa imagem. Para generalizar,
é necessário estimar o núcleo e a extensão do efeito a partir da escala/cor do texto,
sem fixar página, palavras, coordenadas ou um corte de cinza universal.

## 2. O que aconteceu com LaMa

O checkpoint atual já é `anime_manga_lama_large_jit`, com integridade verificada;
não é apenas o LaMa genérico sem adaptação para esse domínio.

| Tentativa | Área da máscara | Tempo | Resultado |
| --- | ---: | ---: | --- |
| Tinta completa + halo 3 px | 50.340 px | 13,91 s, incluindo carga inicial | Tinta removida, brilho das palavras permanece |
| Tinta completa + halo 8 px | 86.284 px | 0,59 s, modelo carregado | Persistem silhuetas e borrões |
| Tinta completa + halo 14 px | 122.305 px | 0,60 s, modelo carregado | Ainda deixa sombras do lettering |

As três tentativas não alteraram pixels fora da respectiva máscara e foram
reprovadas por `local_background_color_mismatch`. O OCR não leu as palavras, mas
a inspeção visual ainda encontra fantasmas. Portanto, repetir apenas o OCR ou
aumentar um pouco a dilatação não resolve esse caso.

## 3. Chamada de FLUX: edição por referência versus máscara nativa

O adaptador atual combina `-r` com `--mask`. A documentação oficial apresenta
FLUX.2 Klein como edição por imagem de referência e mostra chamadas com `-r`:
[guia oficial de FLUX.2](https://github.com/leejet/stable-diffusion.cpp/blob/master/docs/flux2.md)
e [modos de referência](https://github.com/leejet/stable-diffusion.cpp/blob/master/docs/edit.md).

Foi feita uma comparação controlada no binário instalado: mesmo modelo, referência,
prompt, seed 42, resolução 800×384, quatro passos e sampler Euler. A variável foi
adicionar ou retirar a máscara nativa.

- Com `--mask`, a saída bruta apresentou regiões cinzas e ruído; o caminho inicial
  também produziu resíduos de lettering. Não serve como reconstrução pronta.
- Sem `--mask`, a edição por referência removeu o texto e produziu um recorte
  coerente em violeta/magenta. Custou **20,20 s**; a comparação com máscara nativa,
  **19,79 s**. Um teste com pré-preenchimento LaMa custou **19,41 s** no FLUX e não
  mostrou vantagem visual suficiente para justificar esse passo adicional.

Isso demonstra um problema de adequação dessa combinação de argumentos neste
binário/caso. Não estabelece que todo modelo/versão de FLUX seja incapaz de usar
máscaras. O caminho proposto é editar o recorte por referência e compor externamente
somente a região autorizada, com verificação de pixels fora dela.

## 4. A composição também precisa incluir o brilho

Colar a imagem gerada somente dentro do núcleo das letras cria emendas no formato
das letras: a geração remove o brilho, mas o original ainda o mantém logo fora da
máscara. Isso explica por que uma saída bruta boa pode virar uma composição ruim.

Foram testadas máscaras com espaços internos preenchidos e extensões de 20, 28 e
36 px, com transição de 10 px estritamente interna e proteção dos raios brancos.
Essa é uma legenda com brilho amplo; não é uma alteração da máscara v4 sobre cabelo
e roupa. Os valores são variantes de diagnóstico, não novos defaults.

A variante de 36 px foi a melhor visualmente. Ela autorizou 196.068 pixels,
**10,94% da página**, e modificou 193.921. **Zero pixels mudaram fora da máscara.**
Ainda é uma área significativa e precisa ser justificada pela propriedade do efeito
tipográfico, não simplesmente por uma caixa de OCR ampliada.

## 5. Por que a melhor prévia ainda é recusada

Há duas questões diferentes de validação:

1. O gate de cor compara a mediana de toda a região preenchida com uma mediana de
   fundo registrada anteriormente. Para esse fundo com vários tons, o erro foi
   **31,33**, acima do limite **30**, mesmo com o campo diagnóstico
   `local_background_gradient_consistent=true`. Há indício de que essa comparação
   global é inadequada para avaliar espacialmente o gradiente.
2. O gate de manchas escuras também recusa o candidato. Ele encontra pixels que
   eram claros no original e ficaram escuros na reconstrução. Parte desse brilho
   pode pertencer à tipografia removida, mas isso exige evidência de propriedade
   da camada de glow; não é motivo para ignorar o gate.

Os demais diagnósticos independentes deram:

- sem fantasma de contorno segundo o detector;
- sem costura suspeita pelo verificador composto;
- sem rejeição de área chapada;
- razão de textura reconstrução/anel de **0,938**, que é uma medida estatística,
  não uma porcentagem de arte original recuperada;
- deslocamento de nível de textura de −6 contra limite de aproximadamente 20.

Foi prototipada, somente em diagnóstico, uma comparação de cor entre pares locais
na borda, excluindo raios brancos. Foram usados os mesmos 6.716 pixels pareados:

| Imagem | Erro local mediano | Percentil 95 |
| --- | ---: | ---: |
| Melhor candidato | 3,01 | 14,36 |
| Controle negativo: preencher tudo de preto | 67,42 | 145,74 |
| Controle negativo: preencher tudo da mediana roxa | 35,46 | 90,45 |

O preenchimento roxo chapado tem erro global zero por construção, apesar de ser
visualmente errado; os gates de textura/costura o rejeitam. A comparação local
distinguiu o candidato desses dois controles, mas um caso e dois negativos ainda
não validam uma substituição geral do gate.

## Próximo passo técnico

1. Corrigir a extração da geometria completa do texto e separar `glyph_mask`,
   `outline_mask` e `glow_mask`, com proveniência e limites próprios.
2. Usar a chamada de edição por referência adequada para o FLUX local, com recorte
   e composição restrita. Evitar uma inferência por página inteira.
3. Avaliar cor por suporte espacial local nos fundos não uniformes. Conservar
   os testes negativos de chapas pretas/roxas, vazamento, emendas, apagamento de
   linhas e resíduos; não resolver aumentando o limite global de 30 para 42.
4. Fazer o gate de manchas distinguir remoção de glow comprovadamente pertencente
   ao texto de apagamento de um detalhe claro da arte. A proteção dos raios deve
   continuar verificável pixel a pixel.
5. Rodar esses contratos em mais regiões congeladas, incluindo falsos positivos,
   antes de integrar uma aceitação automática. Para uma correção pontual, a prévia
   e a máscara já estão concretas e disponíveis para revisão.

## Estado e limites

**TESTED_FROZEN:** três variantes LaMa; edição FLUX direta e com pré-preenchimento;
comparação controlada da máscara nativa; três composições de efeito; OCR de referência
e de saída; diagnósticos de cor, textura, costura e manchas; dois controles negativos.

**DEFERRED:** integração automática e confirmação visual pelo usuário. Não foram
alterados limites dos gates, configuração padrão do FLUX, código de produção ou
artefatos finais do job. A função v4 permanece preservada. Os processos locais de
inferência terminaram; não ficou servidor de modelo aberto.

Impacto documental: este relatório, referência no relatório anterior e evidência
adicional no card `INPAINT-FOLLOWUP-20261108`. Sem commit, push ou publicação.
# Atualização da opção aprovada

A implementação e a chamada real do modelo passaram pelos guardas; o recurso
foi ativado localmente. Consulte [Ativação e gargalos](inpaint_activation_20261108.md)
para as medições atuais. As recusas abaixo registram os experimentos anteriores.

