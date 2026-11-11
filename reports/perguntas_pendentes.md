# Perguntas e dependências pendentes — Fase 0

Atualizado: 2026-11-11

## REF-A `Tradução pronta` (job pago)

O job precisa ser iniciado pelo dono na interface autenticada, conforme a regra de não iniciar tradução paga por automação.

- URL: `https://www.webtoons.com/en/action/hero-killer/episode-285/viewer?title_no=2745&episode_no=285`
- App: `http://127.0.0.1:8080`
- Modo: `Tradução pronta`
- Opções: Qualidade; force ligado; cache desligado; traduzir SFX desligado.
- Depois de iniciar, avisar para acompanhar pelo banco de jobs e `job_metrics.py`; conferir `(GPU DirectML)`, p023 e eventual `errors/flux_<página>_<região>.log`.

## Aplicar intervalo de monitor medido na interface

A medição CLI a 10 s ficou em 1,07%, abaixo da meta de 2%. O `.env` local contém `RESOURCE_MONITOR_INTERVAL_SECONDS=5.0` em duas linhas. Não foi alterado. O dono precisa mudar ambas para `10.0` e reiniciar app/worker antes de usar essa configuração; confirmar que o `timing_report.json` do job registra `interval_seconds: 10.0`.

## F0.8 pela interface

A execução CLI terminou `review_required`, gerou 65 PNGs e manteve a página 10 em revisão; as duas rodadas Clean são pixel a pixel idênticas. Isso valida o pipeline offline/CLI, mas não prova o estado do cartão de histórico pela interface. Revalidar F0.8 pela interface ainda é necessário, sem iniciar tradução paga.
