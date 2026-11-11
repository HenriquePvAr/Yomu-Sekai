# Ativação do reparo aprovado e diagnóstico dos gargalos

08/11/2026 — checkout local `claude/inpaint-auto-repair-20261107`, base
`cda3f90249c327c6ae1331097e6c222b909e9f0d`. Alterações anteriores preservadas;
sem commit, push, merge em main ou publicação.

## O que foi ativado

`GENERATIVE_CAPTION_REPAIR_ENABLED=True` na configuração local. O padrão do
produto continua desligado. `GENERATIVE_INPAINT_ENABLED` e `TRANSLATE_SFX`
permanecem desligados: o reparo aprovado não liga tradução de efeitos sonoros.
O app foi recarregado sem jobs ativos; o worker voltou online e sem fila.

O novo passe `caption_effect` remove legendas grandes com brilho cromático
comprovado. Exige linhas rastreáveis, fonte completa, confiança OCR >=0,8,
geometria completa dos glifos e perfil de fonte serif/sans confiável. Reconstrói
um recorte de contexto usando FLUX.2 klein local; não há provedor pago nesse
passe. SFX, nomes preservados, logos e créditos ficam fora desse mecanismo.

## Por que a página 23 falhava

A máscara anterior não abrangia toda a tipografia e seu brilho. Apagar só a
tinta preta deixava letras roxas fantasmas; pintar a caixa inteira apagava arte.
A saída final acabava usando uma legenda sobre fundo preto. Havia também um
problema no adaptador: combinar máscara nativa com edição por referência no
binário instalado produzia uma região cinza/ruidosa. O A/B documentado em
[opções da página 23](page23_options_20261108.md) isolou esse comportamento.

O passe atual mede separadamente núcleo, brilho e envelope do efeito. Preenche
os contadores internos dos glifos, preserva linhas brancas fortes e mistura a
reconstrução com transição exclusivamente dentro da máscara. Não altera a v4
de SFX. A comparação espacial de cores usa pares próximos ao mesmo trecho de
borda, em vez de exigir a mediana global de um fundo naturalmente multicolorido.
O diagnóstico global anterior continua disponível. Não há exceção para número
de página, texto, hash aprovado ou episódio.

O verificador de manchas não confunde a remoção do brilho das próprias letras
com perda de arte clara: somente pixels cuja origem cromática foi comprovada
podem usar essa regra, condicionada à continuidade espacial e à integridade
dos traços protegidos. Os outros pixels mantêm os guardas anteriores.

## Evidência da página 23

- **IMPLEMENTED / TESTED_OFFLINE:** testes de cores, linhas protegidas, limites
  de máscara, troca de fonte/máscara, propriedade atual antes do cache,
  geometria de saída e separação entre a opção de legenda e FLUX geral.
- **TESTED_FROZEN com modelo local real:** 16 glifos verificados; chamada FLUX
  de **19,933901 s**. Nenhuma API de tradução chamada.
- Máscara de efeito de **195.892 pixels / 10,9266% da página**. Isso inclui o
  brilho da legenda; não corresponde a uma expansão da máscara SFX v4.
- **193.747 pixels alterados dentro**, **zero fora da máscara** e **zero
  alterações nos pixels brancos protegidos**.
- Cor espacial: mediana **3,0899**, percentil 95 **21,3311**, com 7.133 amostras.
  Limites: mediana <=12 e percentil 95 <=30, com suporte mínimo obrigatório.
- OCR residual estrito: texto antigo não legível, inclusive palavras que fonte
  e tradução compartilham. Na imagem original o mesmo controle lê DAEMON,
  LASER e BLAST. Preenchimentos preto e roxo chapado são recusados.
- Renderização aceita como `translated / ok`; remoção `VERIFIED`, reconstrução
  `clean`. O modelo é uma reconstrução plausível, não recuperação comprovada
  dos pixels que estavam escondidos pelas letras.

Arquivos locais de evidência em
`%LOCALAPPDATA%/TradutorIA/runtime/performance_validation/20261108_integration/`:
`live_page23.log`, `page23_negative_controls.json`, `page23_integrated_final.png`,
`page23_integrated_clean.png` e métricas por página do replay. O job original
`09925d38ee20449aa4ec3d432807fbe5` não foi sobrescrito.

## Gargalos encontrados e mudanças

1. **Reconstrução repetida ao montar CLEAN.** `_apply_cleanup_mask` chamava um
   preenchimento novamente mesmo recebendo o candidato já aceito. Na página
   23 isso carregava LaMA depois do FLUX: o profiler mediu 15,63 s nessa função,
   dos quais 14,14 s em carga de modelo. Agora o commit copia apenas os pixels
   autorizados do candidato aprovado, preservando o buffer anterior fora da
   máscara. Evita inferência duplicada e também impede comprometer CLEAN com
   pixels diferentes dos que passaram pelos guardas.
2. **Custo antes oculto.** Foram acrescentadas medidas de
   `commit_accepted_clean` e `post_render_source_text_check`. São subetapas;
   não devem ser somadas novamente ao render para calcular tempo total.
3. **Sweep antes serial.** A mudança anterior sobrepõe o sweep de cada página
   à análise de outras páginas, mantendo o gateway de inferência único e a
   proveniência no worker certo. Teste de concorrência passou; economia total
   ainda depende do job completo.
4. **Reuso e limitação do FLUX.** Somente recortes de até 1.048.576 pixels,
   quatro passos, inferência serializada, cache local limitado e reutilização
   exata no mesmo grupo. Não se ativa FLUX em todo balão nem se criam modelos
   adicionais concorrendo pela GPU. O custo de aproximadamente 20 s permanece.
5. **SFX desativado também bloqueava CLEAN.** O classificador marca o grupo
   `ignored / sfx_translation_disabled`; a seleção de CLEAN antes obedecia
   indiscriminadamente a esse flag. Agora essa razão específica desliga somente
   o typesetting. A limpeza ainda exige linhas rastreáveis, OCR suficiente e
   passa pelas tentativas/guardas normais. Outras razões de proteção continuam
   protegidas. O teste inclui a política do classificador, além do renderer.
6. **SFX borrado da página 60.** A v4 encontrava somente 1.131 pixels de núcleo;
   máscara/núcleo =3,2476, acima do limite. Cinco estratégias repetiam a mesma
   recusa. Quando a v4 não passa por esse limite, agora se tenta o extrator de
   componentes existente, sem alterar a função v4 nem aumentar o limite. Esse
   candidato passa por todos os guardas e pela releitura. Na página 60 a nova
   máscara teve razão 1,2864, cobertura de fonte 100%, OCR residual não legível
   e reconstrução sem incerteza apontada pelos guardas. CLEAN mudou 19.086
   pixels; o final continuou exatamente igual ao original. O teste isolado
   levou 15,30 s com carga fria do modelo. Não é uma regra por página.
7. **Concorrência do FLUX com LaMA/RapidOCR.** Uma repetição do capítulo
   entregou `generative_output_missing` na p23, embora testes anteriores do
   mesmo reparo tivessem passado. O lock específico do FLUX não impedia outra
   página de usar DirectML durante o processo Vulkan. O adaptador agora usa o
   `DIRECTML_LOCK` canônico, mede a fila do dispositivo e registra retorno e
   categoria sanitizada de falha. O conflito de uso foi demonstrado no código;
   a causa exata daquela saída sem arquivo não estava registrada no binário
   anterior e não deve ser afirmada como OOM confirmado.

Desligar a **tradução** de SFX não elimina o custo de limpar os SFX na pasta
CLEAN, conforme o comportamento solicitado. No job antigo a tradução inteira
levava 5,36 s: desligar efeitos não poderia recuperar sozinho os minutos
perdidos em limpeza/sweep. O novo passe FLUX também tem custo real; qualidade
maior e tempo menor precisam ser avaliados separadamente.

No teste isolado com a mesma saída FLUX congelada, montar/renderizar a página
23 caiu de **16,655 s** para **1,093 s**. Esse teste exclui o custo do FLUX e o
ganho inclui uma carga fria de LaMA; não é economia garantida por página nem
medição de um capítulo completo.

## Limites de validação e próximos passos

O replay usa as 65 imagens reais, linhas e traduções persistidas do último job,
dois workers e o renderer canônico. Reexecuta a classificação atual; não mede
download, OCR inicial, sweep, provider, settlement ou PDF. As primeiras
execuções de diagnóstico sem propagação do recorder para as threads foram
descartadas como evidência de fonte completa; seus arquivos foram preservados.
Somente execuções com recorder vinculado são usadas na comparação.

### Replay final com GPU coordenada

**65 páginas, 84 grupos, dois workers: 114,945 s / 1min55s**, incluindo leitura,
classificação, limpeza, typesetting e salvamento do harness. Saídas e
`summary.json` em `20261108_integration/chapter_gpu_coordinated/`. As páginas
23 e 60 passaram. Esse harness salva PNG com compressão explícita de nível 1;
não é o persistidor completo de artifacts do job e não emite certificado de
capítulo. A última alteração depois dessa medição apenas passou a transportar
as métricas generativas já calculadas para o resumo das tentativas aceitas;
a suíte de 382 testes foi repetida sobre esse snapshot final.

O replay anterior, com fonte vinculada e código de antes desta integração,
levou **63,641 s**. Não faz o mesmo trabalho: deixava os SFX desligados fora de
CLEAN e não reconstruía a legenda com o FLUX aprovado. Portanto, o novo replay
**não demonstra redução do tempo total**. A correção da composição elimina uma
inferência repetida, mas a limpeza dos SFX e o reparo visual acrescentam trabalho.
A repetição que revelou falha nativa antes do lock compartilhado levou
118,823 s; a diferença para 114,945 s não é tratada como ganho garantido, pois
há variabilidade do dispositivo e uma delas não entregou o reparo da p23.

77 grupos tiveram remoção local aprovada pelos verificadores; isso não equivale
a 77 reconstruções artisticamente perfeitas. **CRUSH da página 19 ainda tem
`art_fidelity_uncertain`** e continua revisão. **FluCK da página 10** está abaixo
do piso de confiança para apagar automaticamente. **RocK? da página 20** conserva
o original pela política de source echo com forma de nome; a leitura semântica
precisa ser decidida no contexto. Cinco outros grupos permanecem protegidos por
classificação decorativa/crédito, sem tratar essa preservação como limpeza.

Também foi medida a codificação PNG das 65 fontes, alternando a ordem para
reduzir viés de aquecimento: padrão 2,767 s / 109.199.663 bytes; opção RLE
explícita 4,500 s / 94.448.702 bytes. Decodificação confirmou pixels idênticos
em ambas. **Nenhuma troca de codec foi aplicada**, pois a opção experimentada
era mais lenta. Evidência: `png_encoding_benchmark.json`.

**EXTERNAL_GATE:** o host de Computer Use e o host do Chrome continuam
indisponíveis. Não foi possível iniciar pelo app um novo job autenticado nem
confirmar visualmente o card e o Explorer. Não foram extraídas credenciais ou
inventada identidade para contornar isso. A autorização do episódio 285 está
mantida; o impedimento é acesso à interface.

**DEFERRED:** tempo total menor que cinco minutos e fidelidade perfeita do
capítulo não estão comprovados. Mais paralelismo de GPU não foi liberado sem
evidência de memória/contenda. Fonte desenhada à mão continua sendo aproximada
por família; a reprodução exata não pode ser prometida a partir desses testes.

Suite focada no snapshot final: **382 testes e 393 subtestes passaram; 1 teste
ignorado**. Uma execução mais ampla encontrou duas falhas em
`test_art_reconstruction_quality.py`: pontuação fora do polígono e a expectativa
de recusa de uma linha cruzando letras. As duas foram reproduzidas carregando
o código de antes desta integração em processo isolado: não foram introduzidas
por esse reparo, mas permanecem pendentes. Os mocks de CLEAN que esperavam um
segundo preenchimento foram atualizados para retornar o candidato preenchido;
os testes antigos que exigiam fechar o espaço entre letras SFX foram alinhados
ao contrato de não expandir a v4 e não unir letras através da arte.

Impacto documental: configuração, contrato técnico de composição CLEAN e
quadro de status atualizados. O guia de usuário já documenta a diferença entre
PDF/SFX e pasta CLEAN; esta ativação técnica não adiciona outro controle visual.
