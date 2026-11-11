# Último job: desempenho, limpeza de SFX e tipografia

Atualização: a ativação aprovada, novas medições, correção do skip de SFX e
reparo da página 60 estão em [Ativação e gargalos](inpaint_activation_20261108.md).
As recusas da página 23 descritas abaixo pertencem à investigação anterior.

Data: 08/11/2026. Checkout: `C:\Projetos\Yomu-Sekai`, branch
`claude/inpaint-auto-repair-20261107`, base `cda3f90249c327c6ae1331097e6c222b909e9f0d`.
As alterações locais anteriores foram preservadas. Este trabalho não representa
integração em `main` nem publicação.

## Evidência examinada

Job `09925d38ee20449aa4ec3d432807fbe5`, run
`833e2624-2a8c-4994-90eb-8b58dc8d0a5c`, Hero Killer episódio 285.
Foram lidos `timing_report.json`, `quality_report.json`, `ocr_line_provenance.json`
e as imagens originais, limpas e traduzidas das páginas 23 e 34.

- Fila, do início ao término: **447,28 s / 7min27s**.
- Pipeline, medição interna: **442,84 s / 7min23s**.
- `quality_validation.translate_sfx_disabled=true`; 23 grupos de SFX preservados.
- 65 páginas, 58 grupos enviados à tradução. Duas páginas sem certificado CLEAN
  aprovado: 23 e 60. Isso não equivale a dizer que todo o restante tem fidelidade perfeita.

## Por que demora

| Etapa | Tempo registrado | Interpretação |
| --- | ---: | --- |
| Sweep residual Paddle | 84,06 s | Era executado depois de toda a análise, em uma passagem separada |
| Render | 136,67 s | Soma de trabalho por página; contém limpeza, tipografia e validação |
| Inpainting | 99,99 s | Subconjunto do render; não deve ser somado novamente |
| Download/coleta | 46,88 s | Inclui trabalho de coleta e transferência |
| Pré-tradução | 44,68 s | Tempo de parede da análise com dois workers |
| Smart split | 31,73 s | Preparação das 65 páginas a partir dos assets baixados |
| OCR inicial | 21,61 s | Um worker; a política de memória restringiu o paralelismo |
| Salvar imagens | 25,85 s | Soma dos salvamentos por página |
| Tradução | 5,36 s | Não é o principal gargalo observado |
| PDF | 2,69 s | Não é o principal gargalo observado |

O pipeline já tinha dois workers de página. Colocar todos os modelos em mais
processos não garante ganho: Paddle e LaMa têm custos de memória e inferências
compartilhadas/protegidas por lock. Os tempos de subetapas também não são todos
tempos de parede independentes.

### Mudanças implementadas

1. O sweep de cada página entra no executor de análise assim que aquela página
   termina sua análise. Ele pode se sobrepor ao processamento de outras páginas.
   O gateway do Paddle continua serializando as requisições em uma única instância;
   não foram criadas cópias adicionais do modelo. A ordem final das páginas e o
   recorder de proveniência de cada página são preservados.
2. A máscara é refinada antes do preenchimento, evitando produzir primeiro um
   preenchimento com máscara antiga e reconstruí-lo após o refinamento. O caminho
   CLEAN reutiliza o candidato que `_remove_text_for_group` já produziu e verificou.
   Os limites de área são reavaliados para a máscara final.
3. Acrescentadas medidas de parede de `layout_preflight` e `post_translation`.
   O preflight já faz uma renderização completa antes do settlement; o render
   final reutiliza esse resultado quando a assinatura continua compatível.
   Os novos campos tornam esse custo visível sem atribuí-lo incorretamente à API de tradução.
4. O passe dos grupos exclusivos de CLEAN agora registra sua duração nos contadores
   de limpeza/inpainting. O teste real com SFX desligado revelou que esse trabalho
   aparecia no render total, mas deixava esses dois contadores zerados.

Não há medição de um capítulo completo com este snapshot. A economia real depende
da sobreposição alcançada e do número de tentativas. Limpar SFX que antes eram
preservados em CLEAN também acrescenta trabalho; a nova opção não promete um
capítulo abaixo de cinco minutos.

## Página 23: caixa preta e reconstrução das cores

Atualização complementar: novas opções e uma prévia melhor com FLUX foram
verificadas em [Opções para a página 23](page23_options_20261108.md). A prévia
continua sob revisão e não substituiu o job original.

O original tem `DAEMON LASERBLAST` em fonte serifada preta sobre efeitos roxos e
linhas de movimento. O job tentou preenchimentos e registrou
`local_background_color_mismatch`. Após recusar a reconstrução, o renderer usou
o fallback de legenda opaca por cima da arte. O arquivo limpo manteve o lettering
original na região; portanto, a caixa preta não era uma reconstrução das cores.

Há também uma classificação ambígua do fundo: ele tem gradiente e estrutura
desenhada. A implementação agora tenta o LaMa local quando há evidência espacial
`STRUCTURED_OR_TEXTURED`, antes de cair no Telea destinado a gradientes suaves.
Os gates continuam avaliando o resultado.

Foi executada uma tentativa local adicional com máscara de tinta serifada para
investigar a região. A inferência levou aproximadamente 15,6 s incluindo carga do
modelo. O candidato preservou a paleta roxa, mas ainda deixou partes de letras e
foi reprovado por `local_background_color_mismatch`. Os conflitos entre glifos e
linhas da arte também permanecem relevantes. **A página 23 ainda não está resolvida
nem PHYSICALLY_VERIFIED.** O candidato não substituiu os artefatos do job.

Próximo ajuste necessário: recuperar a geometria completa das letras cortadas nas
caixas OCR e distinguir o halo do texto das linhas de efeito, com evidência que
permita ao gate aprovar a reconstrução. Uma troca de cor ou caixa opaca não atende
essa fidelidade. A página 60 também permanece no conjunto de revisão do job.

## Tipografia das páginas 23 e 34

A extração antiga usava diferença absoluta de brilho em relação à borda. Na
página 23 ela misturava o brilho roxo com a tinta preta e classificava a serifa como
sans. A extração agora compara núcleos claros e escuros e componentes compatíveis
com a altura das letras. A análise das várias linhas passou a medir componentes e
ocupação por linha, evitando interpretar o bloco inteiro como glifos largos ou
fonte display pesada. Na reprodução da página 23, a família mudou para `serif` e a
seleção resultou em `serif_narration`/Georgia. Isso é aproximação de família, não
identificação exata da fonte original.

Na página 34, a tinta é clara e tem halo roxo sobre fundo preto. O detector só
permitia brilho associado a certas famílias de tinta colorida; o preset podia
apagar o halo ou introduzir um contorno azul. Agora um entorno comprovadamente
preto permite medir o anel cromático ligado à tinta clara. O render mantém esse
roxo medido e não acrescenta o contorno azul do preset. Largura de contorno zero
também passou a ser respeitada, em vez de voltar à largura padrão por causa de `or`.

Foi gerada uma prévia local da página 34 com as traduções congeladas do próprio
job, sem chamar provider. A fonte continua uma aproximação da biblioteca local;
o caráter desenhado à mão do original ainda não é reproduzido exatamente.

## Preferência de SFX

| Preferência | PDF/página traduzida | Pasta de páginas limpas |
| --- | --- | --- |
| Desligada, padrão | Mantém o SFX original | Tenta apagar o SFX |
| Ligada | Tenta colocar a tradução do SFX | Tenta apagar o SFX |

O card em Configurações explica o significado de SFX e a dependência do contexto
visual. A preferência é salva por usuário, enviada como booleano no novo job,
persistida na configuração e aplicada no ambiente do runner. Alterar o card não
muda jobs já criados. Saves parciais não apagam outras preferências do usuário.

O filtro de CLEAN deixou de depender da existência de uma tradução do efeito.
Continuam necessários OCR confiável, linhas de origem rastreáveis, máscara válida
e avaliação da reconstrução. Uma região recusada continua identificada para revisão.
Sons estilizados não precisam formar uma palavra de dicionário para esse passe:
na página 9, o OCR registrou `CRAdKVE` com confiança 0,6056. A seleção de CLEAN usa
o piso de detecção e a proveniência visual, em vez de exigir confiança 0,8 ou uma
palavra inglesa perfeita para apagar os glifos.

Reprodução congelada da região SFX da página 9, com a opção desligada: a página
final ficou idêntica ao original, enquanto o candidato CLEAN alterou 42.057 pixels
e passou na validação local de remoção. A função v4 permaneceu intacta. Esse replay
foi limitado ao grupo SFX; a fala fora do grupo foi mantida deliberadamente e não
representa um capítulo/página inteiramente processado. O custo incluiu carga dos
modelos e não deve ser multiplicado por página para estimar o capítulo.

A função `_sfx_glyph_halo_mask` v4 foi preservada byte a byte:
`6ee5d19fbb3df3adabda2c20cf06a8c9f0631ca8dbad5790ba29c0296b247563`.
Uma cópia dos arquivos anteriores está no runtime em
`performance_validation/20261108_followup/before/`.

## Botão de pasta

Os diagnósticos registravam que `/api/ui/open` recebia a ação e retornava
`opened`; isso descarta a hipótese de que nenhum clique chegava ao backend, mas
não prova que uma janela ficava visível. O caminho anterior criava um processo
`explorer.exe`, cujo handoff podia terminar sem comprovação de janela visível.

A abertura de diretório passou a usar a ação registrada do Windows
`os.startfile(path, 'explore')`. A tentativa de foco restaura uma janela minimizada
e usa tipos de handle corretos nas chamadas Win32. O frontend agora confirma que
a solicitação foi enviada ao Explorer. A resolução continua vinculada ao dono do
job e ao diretório de saída autorizado.

O teste offline verifica a ação de shell e os testes existentes verificam o escopo
dos artefatos. **A causa nativa exata e a abertura visível ainda precisam de
validação física:** o host de Computer Use e o host de acesso ao navegador estão
indisponíveis nesta sessão. Aceitação pelo shell não prova janela em primeiro plano.

## Validação e limites

IMPLEMENTED: preferência SFX, limpeza independente do alvo, sobreposição do sweep,
refinamento antes de preencher, métricas de parede, extração tipográfica e glow,
abertura de pasta pelo shell.

TESTED_OFFLINE: testes de roteamento PDF/CLEAN, persistência sem apagar preferências,
snapshot booleano, propriedade das linhas, sobreposição do sweep com análise,
preservação do halo e regressões de OCR/render/runtime/interface.
Na execução final: **416 testes passaram, 1 foi ignorado e 404 subtestes passaram**
(20,41 s). Inclui `test_sfx_output_preference`, `test_neutral_lettering_glow`,
regressões de OCR, glyph style, tipografia, escopo de máscara, sweep, sanitização
do runner, community API, workers de página, forense de runtime e UI por dono.
`node --check` passou no frontend e no board; IDs, estado e links do novo card
foram verificados. `git diff --check` passou após normalização de espaços finais.
O serviço foi reiniciado sem jobs ativos; HTTP 200 e card SFX presente no HTML
foram confirmados. Isso não substitui a validação visual do frontend.

TESTED_FROZEN: extração e prévias locais das páginas 23 e 34, usando os originais,
geometria OCR e traduções persistidas do run analisado. Não foi uma repetição do
capítulo completo nem uma chamada física ao provider.
Também executado o caminho real de CLEAN para o SFX da página 9 com SFX desligado,
com prova de identidade dos pixels da página final e remoção separada no limpo.
A execução final desse replay levou 17,51 s incluindo carga dos modelos, dos quais
17,50 s passaram a aparecer corretamente em cleanup/inpainting.

DEFERRED / gates restantes: reconstrução satisfatória da página 23; revisão da
página 60; fonte exata/desenhada à mão; validação do card e do Explorer no Chrome;
novo run completo do capítulo de referência para medir o tempo de parede e a
limpeza dos SFX sob a opção desligada. Nenhum certificado foi promovido apenas
com base nas prévias.

Evidências visuais locais ficam no runtime em
`performance_validation/20261108_followup/`: `comparison_page023.png`,
`comparison_page034.png`, `frozen_candidates.json` e
`frozen_typography34_final.json`, além de `frozen_sfx_off_page009.json` e
`page009_clean_SFX_OFF_FROZEN.png`. As páginas do job original foram preservadas.

Impacto documental: configuração, guia de usuário, estratégia de CLEAN e quadro
de status atualizados. Sem commit, push, merge ou release.
