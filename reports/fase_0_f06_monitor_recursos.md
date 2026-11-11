# F0.6 — Monitoramento de recursos

Data: 2026-11-11  
Escopo: coleta no runner, inclusão no `timing_report.json` e escrita dos artefatos de recursos.

## Implementado

- `RESOURCE_MONITORING` passa a iniciar como `True` quando não há override de ambiente.
- O `.env` local também tinha override explícito `False`; alterei somente essa chave para `True` para que os jobs desta máquina usem o novo padrão. O arquivo `.env` é ignorado pelo Git e não foi incluído no commit. `.env.example` documenta o novo padrão.
- `psutil` já consta em `requirements.txt`; nenhuma dependência foi adicionada.
- O pipeline já incluía o resumo retornado pelo monitor em `timing_report.json` sob `resource_monitoring`. O resumo registra pico da árvore do processo (pai + filhos), RSS do processo e filhos, uso/percentual de RAM do sistema e uso de swap.
- O monitor grava JSON e CSV por padrão. HTML agora é opt-in (`generate_html=True`), e seu caminho fica vazio no resumo quando desativado.
- Intervalo padrão mantido em 1 segundo; nenhuma alegação de custo de execução foi feita sem comparação física controlada.

## Evidência offline

Comandos executados:

```text
python -m pytest -q -p no:cacheprovider tests/test_resource_monitor.py tests/test_subprocess_ocr.py
14 passed in 2.55s

python -c "from yomu.config import settings; print({'resource_monitoring_enabled': settings.RESOURCE_MONITORING, 'interval_seconds': settings.RESOURCE_MONITOR_INTERVAL_SECONDS})"
{'resource_monitoring_enabled': True, 'interval_seconds': 1.0}
```

O teste valida pico de RSS combinado, uso máximo de RAM e swap, JSON/CSV padrão, ausência do HTML e geração HTML explicitamente solicitada. Isso é `TESTED_OFFLINE`, não comprova consumo/custo em job físico.

A suíte completa foi executada em 2026-11-11:

```text
4 failed, 6482 passed, 141 skipped, 1 xfailed, 8 warnings,
787 subtests passed in 949.18s
```

As quatro falhas foram as antigas de máscara/reconstrução já registradas em `reports/falhas_preexistentes_20261111.md`: pontuação fora do polígono (`GLYPH_ART_BOUNDARY_UNCERTAIN`), linha de arte cruzando glifos, componente unido `MW` classificado como fundo e texto tocando borda do balão. Nenhuma falha ocorreu nos testes de timeout ou monitor de recursos. A suíte não está verde.

## Pendente para a PAUSA 0

- Medir o pico de RAM em REF-A e REF-B com `tools/audit/job_metrics.py`.
- Comparar o tempo do monitor contra uma execução comparável sem monitor; o limite de 2% ainda não foi verificado fisicamente.
- Confirmar que o monitor captura a execução desde o início e não degrada a qualidade nem a conclusão do job.
- Aguardar HenriquePvAr entrar no painel local; a automação não digita senha. O painel foi aberto em `http://127.0.0.1:8080` e está parado na tela de login.
