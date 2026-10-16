# Yomu — plano seguro de organização/arquivamento

**Estado:** plano, não execução. Nenhuma branch/worktree foi movida, arquivada ou removida. Toda limpeza física exige aprovação explícita posterior do owner.

## Checkout oficial recomendado

Usar `<LOCAL_PROJECTS>/Tradutor.Ia-main-consolidation-v1` como checkout oficial de desenvolvimento: branch `main`, SHA publicado `ec9ca9e4acd0849020eb13a089817c1c11aeab7a`. A documentação da CI já foi sincronizada localmente e será registrada em commit; os diretórios gerados `.agents/`, `.basinfy/`, `.codex/` e `.mcp.json` ficam fora do staging.

Manter `<LOCAL_PROJECTS>/Tradutor.Ia` isolado e protegido: é um checkout original em branch feature, com alterações rastreadas e centenas de arquivos não rastreados. Não usá-lo como checkout canônico nem sobrescrever seu conteúdo.

## Categorias operacionais

### KEEP_ACTIVE — 1

O worktree `main-consolidation-v1` é a única fonte recomendada para novo trabalho. Manter esse checkout em `main`; consultar o Kanban antes de iniciar tarefas e sincronizar documentação/board ao concluí-las.

### KEEP_EXPERIMENTAL — 56

Manter worktrees com commits não ancestrais de main. São protótipos, validações ou branches divergentes; a contagem de commits/paths não os aprova para produção. Não fazer cherry-pick automático. Preservar especialmente:

- Famílias de ownership/Clean, SFX, máscaras, OCR, segmentation e datasets: os resultados e dados continuam experimentais; fresh holdout/ground truth é gate em aberto.
- `research/gemini-vps-web-worker-v1` e overlays SAFE CLEAN: client/server e certificados não são contrato/deploy compatível comprovado; preservar como par de pesquisa. A matriz registra 26 divergências reais e seis incompatibilidades de replay, não como regressões da main.
- `research/gemini-hard-clean-fallback-v1`, `research/gemini-safe-fallback-v2-integration`, concorrência e Qwen: evidência parcial/review-only; não ativar provider/modelo.
- `feature/device-revocation-contract`, `fix/final-login-responsive-observability`, `fix/auth-login-startup-physical-v1`, `ui/login-loading-redesign`, `feat/output-modes-selective-pipeline-v1`, `fix/ocr-quality-order-flakes` e branches com diferença de árvore: revisar com os testes/casos da matriz antes de integrar ou arquivar.

### ARCHIVE_CANDIDATE — 44

Worktrees limpos cuja HEAD é ancestral de main não têm commits exclusivos na ponta e são candidatos a arquivamento *após* conferir dados locais. **SAFE_TO_ARCHIVE_NOW=0**: todos continuam registrados e não houve inventário semântico de cada arquivo ignorado/processo consumidor. O candidato mais forte por Git/arquivos ignorados é `Tradutor.Ia-old-download` (HEAD ancestral, árvore limpa, I=0); ainda requer confirmação do owner de que não há processo/estado transitório em uso.

Para cada futuro arquivamento: confirmar processo parado e ausência de submódulo/repositório embutido; validar que todos os HEADs estão recuperáveis no bundle; preservar arquivos ignorados relevantes; então usar mecanismo recuperável de archive. Nesta missão, nada foi arquivado.

### BLOCKED_DIRTY — 8

Não arquivar antes de revisão individual e proteção das alterações. Os oito overlays originais estão no backup externo verificado (IDs WT01–WT08); as mudanças documentais novas do checkout canônico serão salvas em commits locais. Os arquivos gerados não rastreados do checkout canônico permanecem preservados e fora do commit.

- Checkout original `<LOCAL_PROJECTS>/Tradutor.Ia`: preserva alterações no worker/UI/bridge/benchmark/CLAUDE e pesquisa não rastreada. A matriz marca auto-reseed de permissões revogadas como rejeitado por risco de reautorizar usuário e a exceção de variância da fonte como não comprovada.
- `full-ui-community-operation`: snapshots/testes de tooling local, sem caller de produção.
- `glyph-segmenter-v2`: checkpoint experimental (~46,7 MB), fora do runtime.
- `history-bulk-delete-artifact-cards-v1`: overlay e relatórios preservados; contratos seguros têm contraparte canônica, mas arquivos locais continuam sem descarte.
- SAFE CLEAN evidence/validated integration e Gemini VPS: conservar integralmente; equivalência parcial, contracts de provider/cache/progresso/receipts incompatíveis, sem promoção em bloco.
- `main-candidate-comix-ui-v1`: alteração ampla para rebaixar erro genérico de página não provou que OCR foi a causa; preservar rejeição na matriz.

### BLOCKED_UNKNOWN — 1 ocorrência externa ao worktree list

`<LOCAL_PROJECTS>/Tradutor.Ia-audit-baseline-tmp` não consta entre os 109 registrados; seu ponteiro `.git` referencia um gitdir ausente. Preservar e pedir revisão manual antes de qualquer reparo ou remoção. Os 127 diretórios YomuExperimental são snapshots/builds/evidências sem `.git` na raiz e também permanecem intocados.

## Regras antes de qualquer limpeza futura

1. Owner aprova explicitamente cada ID/caminho da lista.
2. Revalidar `git status --porcelain=v1 -uall`, ignored, submodules, processos e arquivos abertos imediatamente antes da ação.
3. Confirmar backup recuperável de código, untracked e artefatos ignorados relevantes; o bundle não substitui o backup desses arquivos.
4. Arquivar uma unidade por vez, verificar recuperação/integridade e só depois considerar a próxima.
5. Não excluir branches Git nesta etapa; qualquer política de branches é uma decisão separada.

**Resultado recomendado:** consolidar trabalho novo no checkout canônico `main-consolidation-v1`; manter os oito overlays originais dirty e as pesquisas; preparar candidatos ancestrais limpos para uma futura revisão por lote. Sem remoções físicas nesta missão.
