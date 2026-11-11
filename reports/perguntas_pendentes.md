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

A medição CLI a 10 s ficou em 1,07%, abaixo da meta de 2%. O dono confirmou que o `.env` local contém uma única entrada `RESOURCE_MONITOR_INTERVAL_SECONDS` (linha 79) e vai alterá-la para `10.0`. O arquivo não foi alterado por nós. Depois, reiniciar app/worker e confirmar que o `timing_report.json` registra `interval_seconds: 10.0`.

## F0.8 pela interface

A comparação controlada contra `dev` `7879bad` resolveu a dúvida de regressão: ambas as versões reprovam p010 por `unresolved_clean_regions`, e a imagem final de p010 é pixel a pixel idêntica. Tratar como defeito preexistente para a Fase 3. Fase 0 tem 64 PASS e p010 em revisão; `dev` tem 63 PASS e p010+p023 em revisão. O teste pela interface e o cartão de histórico ainda aguardam o job Clean que o dono informou que vai iniciar.

## Jobs de interface aguardados

O dono informou que iniciará REF-A Apenas Clean primeiro e REF-A Tradução pronta depois. Não iniciar esses jobs por automação; acompanhar somente após cada aviso de início.
