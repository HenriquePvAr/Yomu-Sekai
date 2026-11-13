# Perfil de hardware medido

Medição física em 08/11/2026, entre 13:04 e 13:13, fuso America/Manaus.
Este documento registra uma configuração testada e o consumo observado;
**não estabelece requisitos mínimos homologados**.

## Configuração de referência

| Componente | Configuração usada |
| --- | --- |
| Sistema | Windows 64 bits, Python 3.11 |
| CPU | AMD Ryzen 5 5600GT, 6 núcleos / 12 threads |
| RAM instalada | 32 GB, aproximadamente 31,37 GiB utilizáveis pelo Windows |
| GPU principal | AMD Radeon RX 6600, capacidade comercial de 8 GB |
| GPU integrada | AMD Radeon Graphics; também inventariada nos contadores |
| Execução | Qualidade, PDF, force ligado, tradução de SFX desligada |
| Motores observados | RapidOCR, Paddle isolado, LaMA/DirectML e FLUX/Vulkan |
| Workers de página efetivos | 1, conforme relatório final do pipeline |

Para uma ficha técnica pública, apresentar **32 GB de RAM e RX 6600 de 8 GB
como configuração de referência testada para este fluxo com FLUX**, sem chamar
esses valores de mínimo. Ainda falta validar máquinas com menos RAM/VRAM,
CPU-only e o fluxo sem reparo generativo em condições controladas.

## Consumo observado no capítulo de referência

Hero Killer, episódio 285: 65 páginas lógicas, processamento completo com saída
PDF e 65 imagens CLEAN + 65 traduzidas. O job terminou com **revisão necessária**;
a coleta de recursos não certifica a qualidade visual da tradução.

| Recurso da árvore do job | Pico amostrado | Mediana das amostras |
| --- | ---: | ---: |
| RAM residente, soma dos working sets dos processos | **8,40 GiB** | 3,55 GiB |
| Memória privada comprometida | **13,69 GiB** | 5,62 GiB |
| GPU: memória dedicada reportada pelo Windows | **4,70 GiB** | 2,75 GiB |
| GPU: memória compartilhada reportada pelo Windows | **4,49 GiB** | 0,21 GiB |

Memória comprometida não equivale a RAM física: parte pode estar paginada.
Memória compartilhada da GPU utiliza memória do sistema; **não somar 4,49 GiB
aos 8,40 GiB para inventar uma exigência adicional de RAM**. As métricas medem
coisas diferentes, com máximos que podem ocorrer em momentos distintos.
Somar RSS de processos também pode contar páginas compartilhadas entre eles;
esse número não é uma medição de memória física única proporcional.

Os valores de GPU são filtrados pelos PIDs do runner e descendentes. Não são
o uso total da placa por navegadores, desktop e outros aplicativos. Os 8 GB da
placa não significam que toda essa capacidade estava disponível exclusivamente
ao Komyst. A capacidade foi consultada por DXGI; `AdapterRAM` do inventário WMI
não foi usado para inferir capacidade de placas maiores.

CPU: pico amostrado de aproximadamente **67% da capacidade total dos 12
processadores lógicos**, calculado por diferença de tempo de CPU dos processos.
Contadores de motores GPU são independentes e sobrepostos; não há um percentual
único de GPU obtido pela soma deles. Um valor bruto fora de faixa (101) foi
preservado na evidência e não publicado como porcentagem válida de utilização.

## Tempo e armazenamento

| Medida | Resultado |
| --- | ---: |
| Job, início até término | **545,88 s — 9min06s** |
| Tempo interno do pipeline | 539,54 s — 8min59,5s |
| Download/coleta | 48,02 s |
| Preparação/split | 29,34 s |
| OCR inicial, parede | 33,57 s |
| Análise/classificação/sweep, parede | 149,28 s |
| Preflight de layout/limpeza, parede | 197,16 s |
| Chamadas/contabilidade de tradução registradas | 6,28 s |
| Pós-tradução, parede | 43,20 s |
| Geração do PDF | 2,64 s |
| Arquivos persistidos na pasta completa deste run | 621.066.624 bytes, aproximadamente 592,3 MiB |
| PDF deste run | 13.103.135 bytes, aproximadamente 12,5 MiB |

Tempos de subetapas se sobrepõem: não somar essa tabela para reconstruir o
total. O custo local do preflight não deve ser atribuído à API de tradução.
Os tempos incluem rede, serviços externos, modelos e a carga concorrente da
máquina; **9min06s não é promessa de desempenho por capítulo**.

O tamanho da saída não é o espaço necessário para instalar/operar o produto:
modelos, caches, temporários e paginação do Windows precisam de espaço adicional.

## Condições e limites da medição

- Job `f3de3bca6a8a479aa388b7a7c4fbff63`, run
  `0fd7358a-8c5a-469a-9ee7-f7fef965682d`, checkout local `cda3f902` com alterações
  não publicadas. Não representa validação de um instalador ou release.
- 182 amostras com intervalo nominal de dois segundos. A coleta começou em
  **3min04s de job** e pegou o FLUX e o fim da execução; não cobre a partida
  nem garante que não houve pico maior antes ou entre amostras.
- Escopo de RAM/CPU: runner e descendentes, incluindo Paddle e FLUX. UI,
  supervisor e monitor externo ficam fora. Carga global do sistema inclui todos.
- GPU obtida por contadores Windows WMI de memória por processo/adaptador;
  inventário de capacidade via DXGI. Nenhuma das 182 amostras falhou na coleta
  de GPU. Consultas duraram mediana de 0,11 s e máximo de 0,78 s; a medição
  não foi um benchmark isolado da instrumentação.
- Havia aplicativos pesados abertos. O sistema chegou a **100% de RAM** e
  aproximadamente **11 MiB disponíveis** em uma amostra. Isso limita a validade
  do tempo como benchmark e mostra que hardware instalado não é recurso livre.
- O Paddle foi efetivamente encerrado antes do FLUX neste job. Comparado ao
  job anterior interrompido, os picos observados caíram de 10,18 para 8,40 GiB
  residentes e de 22,21 para 13,69 GiB comprometidos. São execuções diferentes;
  não tratar a diferença como economia garantida para qualquer capítulo.

## Evidência e próximos ensaios

[Métricas agregadas em JSON](../reports/data/job_f3de3bca_resources.json) e
[linha do tempo em CSV](../reports/data/job_f3de3bca_resources.csv).
Logs e artefatos originais estão em `%LOCALAPPDATA%/Komyst`; os dados de
processos detalhados não foram incluídos na documentação pública.

Antes de anunciar mínimo de RAM/VRAM: repetir com captura desde o início,
máquina sem aplicativos pesados concorrentes, mesma entrada/configuração,
separando FLUX ligado/desligado; depois testar limites menores de hardware.
Não reduzir os gates de qualidade para apresentar um consumo menor.
