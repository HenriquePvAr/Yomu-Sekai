# Decisões do agente

Registro das escolhas feitas pelo agente e por HenriquePvAr, com as alternativas não escolhidas.
Git é a evidência; este arquivo explica o porquê.

---

### D-20261101-1 · Configuração inicial do agente
- Card: — · Branch: dev · Data: 2026-11-01 · Decidido por: HenriquePvAr
- Regra de negócio? não
- Muda decisão anterior? não
- Escolha: branch de trabalho `dev`; sem co-autor em commits; modo autônomo; rodadas a cada 4 horas
- Por quê: HenriquePvAr quer acompanhar branches periodicamente sem PRs automáticos; sem co-autor
  para manter histórico limpo
- Outras opções:
  - A) Branches `claude/…` + PRs automáticos — mais rastreável, mais notificações de PR
  - B) Modo conservador — o agente para antes de qualquer regra de negócio nova
- Como trocar depois: editar `AGENTE.md` (seção "Limites" e "Quem decide") e atualizar o prompt
  da tarefa agendada em claude.ai/code → Routines
- Fácil de reverter? sim

### D-20261101-2 · Prioridade da fila
- Card: — · Branch: dev · Data: 2026-11-01 · Decidido por: agente
- Regra de negócio? não
- Muda decisão anterior? não
- Escolha: LANG-01 (multi-idioma) → GLOSSARY-01 (glossário) → DOCS-01 (documentação)
- Por quê: LANG-01 é o maior gargalo funcional (ja/ru/zh detectam 0 grupos); GLOSSARY-01 é
  pequeno e sem risco; DOCS-01 é documentação que acompanha as duas
- Outras opções:
  - A) GLOSSARY-01 primeiro — mais rápido, mas deixa o bug principal de detecção sem resolver
- Como trocar depois: mudar o campo `fila` nos cards do board.js
- Fácil de reverter? sim
