# Pendências conhecidas

Este registro reúne itens observados nas validações físicas recentes; não substitui os relatórios por job.

A instalação limpa em Windows foi validada por um beta tester com a `v0.9.1-beta.18` (data não registrada).

| Item | Evidência atual | Próximo passo |
| --- | --- | --- |
| FLUX pode falhar por `device_memory` na página 23 | Intermitente mesmo quando a GPU está livre no início do job; observado em execução física | Medir VRAM dedicada durante o job e avaliar liberação/repetição controlada na Fase 5 |
| Nome próprio “Seon-ho” pode sair como “Seen-ho” | Observado na validação física REF-B | Melhorar tratamento de nomes próprios na F3.2 |
| Varredura de resíduos tem custo próximo de 100 s por capítulo | Medido no REF-A com Paddle disponível | Avaliar varredura seletiva e estado `unavailable` na Fase 2 |
