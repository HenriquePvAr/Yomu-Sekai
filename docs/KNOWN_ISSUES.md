# Pendências conhecidas

Este registro reúne itens observados nas validações físicas recentes; não substitui os relatórios por job.

| Item | Evidência atual | Próximo passo |
| --- | --- | --- |
| FLUX pode falhar por `device_memory` na página 23 | Intermitente mesmo quando a GPU está livre no início do job; execução física informada pelo dono | Medir VRAM dedicada durante o job e avaliar liberação/repetição controlada na Fase 5 |
| Nome próprio “Seon-ho” pode sair como “Seen-ho” | Observado na validação REF-B informada pelo dono | Melhorar tratamento de nomes próprios na F3.2 |
| Varredura de resíduos tem custo próximo de 100 s por capítulo | Medido no REF-A com Paddle disponível | Avaliar varredura seletiva e estado `unavailable` na Fase 2 |

A validação do instalador, da licença Beta e da instalação limpa da `v0.9.1-beta.18` foi **validada por beta tester, informado pelo dono**; a data não foi informada.
