// Dados do quadro de avanço. Só leitura: Claude atualiza a pedido ("atualiza o quadro").
// Regra: cada card cita a evidência (SHA, data) que sustenta a coluna. Git vence memória.
// `risk` separa medido de suposto com MEDIDO / NÃO MEDIDO / SEM FONTE / SUPOSIÇÃO.
window.BOARD = {
  title: 'Komyst · Quadro',
  subtitle: 'Komyst',
  updatedAt: '2026-11-11',
  repoUrl: 'https://github.com/HenriquePvAr/Yomu-Sekai',
  defaultBranch: 'main',
  columns: [
    { id: 'design', label: 'Na fila',           hint: 'Planejado, sem código. O agente pega daqui na ordem da fila.' },
    { id: 'dev',    label: 'Em andamento',       hint: 'Código em branch claude/…, incompleto ou aguardando integração.' },
    { id: 'qas',    label: 'Pronto p/ revisar',  hint: 'Branch claude/… com testes passando, aguardando merge.' },
    { id: 'prod',   label: 'Na main',            hint: 'Mergeado na branch principal.' },
    { id: 'blocked',label: 'Precisa de você',    hint: 'Conta, acesso, teste real, aprovação ou decisão.' },
  ],
  domains: [
    { id: 'pipeline', label: 'OCR · Tradução · Clean' },
    { id: 'ui',       label: 'Interface' },
    { id: 'infra',    label: 'Worker · Runtime · Infra' },
    { id: 'release',  label: 'Pacote · Beta · Release' },
  ],
  envs: {
    local:  'checkout local, sem commit/publicação',
    main:   'main da Komyst',
    branch: 'branch claude/… no GitHub',
    none:   'sem código',
  },
  cards: [
    {
      "id": "FASE0-JOBS-NAO-MORREM-20261111",
      "title": "Fase 0 — retenção, timeout OCR, PSDs e monitor de recursos",
      "domain": "infra",
      "column": "blocked",
      "env": "local",
      "updated": "2026-11-11",
      "summary": "F0.1–F0.6 implementados no branch fase-0-jobs-nao-morrem; commits locais 5cd168b, 39f84e5, d753c05, b53c170, 66b78d8 e 4d6faf5. F0.4 manteve ambas as saídas PSD após diagnóstico. Testes focados do timeout/monitor: 14 passaram. Suíte completa: 6482 passaram e 4 falhas antigas de máscara/reconstrução; não está verde.",
      "risk": "TESTED_OFFLINE. Monitor ligado no .env local e em settings; pico físico, comparação do custo ≤2%, jobs REF-A/REF-B e qualidade ainda não verificados nesta branch.",
      "blockedBy": "Precisa de: HenriquePvAr entrar no painel local (sem compartilhar senha) para iniciar e acompanhar REF-A/REF-B até a PAUSA 0; medir custo do monitor e conferir métricas/qualidade.",
      "delivered": [
        "Portão SFX validado por envio real ao provedor; falhar rápido por disco; retenção protege histórico e publicações",
        "Timeout real do subprocesso Paddle com reinício dentro do limite existente",
        "Diagnóstico F0.4 documenta que psd/ e result_path têm conteúdo próprio e ambos são preservados",
        "Monitor psutil ligado por padrão; timing_report recebe pico de árvore RSS, RAM do sistema e swap; JSON/CSV padrão, HTML opt-in",
        "A suíte completa executada: quatro falhas antigas coincidem com reports/falhas_preexistentes_20261111.md"
      ],
      "pending": [
        "PHYSICALLY_VERIFIED: iniciar REF-A e REF-B, validar saída/qualidade e usar tools/audit/job_metrics.py para pico de RAM",
        "Comparar tempo do monitor com execução equivalente sem monitor; manter custo até 2% ou aumentar o intervalo",
        "As quatro falhas conhecidas impedem o aceite de suíte completa verde; não foram corrigidas nesta tarefa"
      ],
      "links": [
        { "label": "Plano Fase 0", "path": "docs/plans/PLANO_EXECUCAO_KOMYST.md" },
        { "label": "Diagnóstico PSD F0.4", "path": "reports/fase_0_f04_psd_diagnostico.md" },
        { "label": "Monitor F0.6", "path": "reports/fase_0_f06_monitor_recursos.md" },
        { "label": "Falhas preexistentes", "path": "reports/falhas_preexistentes_20261111.md" }
      ]
    },
    {
      "id": "CLEAN-PARALLEL-20261108",
      "title": "Recuperar SFX omitidos e acelerar reconstrução sem mudar pixels",
      "domain": "pipeline",
      "column": "dev",
      "env": "local",
      "updated": "2026-11-08",
      "summary": "IMPLEMENTED / TESTED_FROZEN: v4 preservada; reparos de seleção, geometria e proveniência. Replay de 65 páginas: 196,43 s com 1 worker e 133,67 s com 2; 130/130 imagens idênticas. Configuração local em 2 workers, sem integração à main.",
      "risk": "MEDIDO somente preflight/render/escrita, sem download/OCR/sweep/provedor/PDF. RSS 8,24→8,65 GiB; margem de RAM pequena. Sem promessa de 100% dos SFX ou de menos de cinco minutos por capítulo.",
      "delivered": [
        "Caixas rejeitadas deixam de esconder SFX da sweep; promoção do glossário atualiza política e componentes menores exigem tinta/anel branco comprovados",
        "Correções verificadas em páginas 3/5/12; releituras reais de 6/10 reaplicadas com validação local, sem chamadas pagas",
        "Workers recebem fonte isolada da própria página; merge apenas de eventos novos; máscara v4 e gates preservados",
        "Páginas CLEAN sem alteração mantidas na sequência completa; escrita das 14 páginas iguais somou 4,90 s"
      ],
      "pending": [
        "PHYSICALLY_VERIFIED pendente para um novo job completo com configuração atual e inspeção dos artefatos canônicos",
        "Validar tempo total e consumo desde a partida; sem commit, main, publicação ou homologação de 4 workers"
      ],
      "links": [
        {
          "label": "Relatório e limites",
          "path": "reports/clean_parallel_20261108.md"
        },
        {
          "label": "Comparação A/B",
          "path": "reports/data/clean_parallel_20261108.json"
        }
      ]
    },
    {
      "id": "HARDWARE-PROFILE-20261108",
      "title": "Perfil medido de RAM, VRAM e tempo do capítulo 285",
      "domain": "infra",
      "column": "dev",
      "env": "local",
      "updated": "2026-11-08",
      "summary": "PHYSICALLY_VERIFIED para recursos/tempo do job f3de3bca: 65 páginas, 545,88 s, revisão necessária. Pico amostrado de 8,40 GiB RSS, 13,69 GiB privados, 4,70 GiB GPU dedicada e 4,49 GiB GPU compartilhada. Perfil documentado como referência testada, sem homologar mínimos.",
      "risk": "Coleta começou em 3min04s e cobriu FLUX/final: 182 amostras, zero falhas de GPU. Outros aplicativos abertos; sistema atingiu 100% de RAM. Pico amostrado não é máximo garantido. Memória compartilhada da GPU não deve ser somada ao RSS para inventar exigência de RAM.",
      "delivered": [
        "Ryzen 5 5600GT 6c/12t, 32 GB RAM instalada e RX 6600 8 GB; capacidade consultada via DXGI e consumo por PID/adaptador via contadores Windows",
        "Runner e descendentes monitorados, incluindo Paddle e FLUX; UI/supervisor fora do consumo do job. Arquivos públicos não incluem argumentos de processos ou credenciais",
        "Job terminou com 65 páginas CLEAN e traduzidas e PDF; 9min06s de parede / 539,54 s de pipeline. Recursos medidos não certificam qualidade visual",
        "Análise/sweep 149,28 s de parede, preflight 197,16 s, tradução registrada 6,28 s. Paddle efetivamente encerrado antes do FLUX",
        "Perfil público, resumo JSON e timeline CSV preparados localmente; README, guia de usuário e índice apontam para os limites da medição"
      ],
      "pending": [
        "Homologar mínimos de RAM/VRAM e CPU-only com ensaios controlados desde a partida, sem aplicativos pesados concorrentes, separando FLUX ligado/desligado",
        "Não anunciar 9min06s como promessa por capítulo nem 32 GB/8 GB como mínimo comprovado; sem commit/publicação nesta tarefa"
      ],
      "links": [
        {
          "label": "Perfil de hardware",
          "path": "docs/HARDWARE_PROFILE.md"
        },
        {
          "label": "Métricas agregadas",
          "path": "reports/data/job_f3de3bca_resources.json"
        },
        {
          "label": "Timeline CSV",
          "path": "reports/data/job_f3de3bca_resources.csv"
        }
      ]
    },
    {
      "id": "RUNTIME-HEADLESS-MEMORY-20261108",
      "title": "Consoles invisíveis, memória do job real e limpeza legada",
      "domain": "infra",
      "column": "dev",
      "env": "local",
      "updated": "2026-11-08",
      "summary": "IMPLEMENTED / TESTED_OFFLINE no checkout. FLUX, gateway OCR e Git da UI ocultam consoles; dependências são protegidas apenas no worker headless. Paddle é encerrado após análise/sweep. Timeout pós-boot preserva o painel. Job 457d265b observado até interrupção por ENOSPC em 51/65; sem PDF completo validado.",
      "risk": "RAM amostrada da árvore: 10,181 GiB residentes / 22,208 GiB privados; sistema chegou a 99% de RAM. Medição começou depois do início. Redução após liberação antecipada de Paddle ainda não medida em novo job. SFX da p3 foi removido em grande parte, mas deixou restos abaixo do quadro.",
      "delivered": [
        "Print identificou sd-cli.exe; chamadas usam CREATE_NO_WINDOW e SW_HIDE sem perder logs, pipes ou exit codes; filho controlado Windows confirmou GetConsoleWindow=0",
        "Gateway Paddle preserva reinício/protocolo e pode reabrir depois da liberação no fim da análise; heavy_ocr_release mede a duração; nenhuma máscara v4 alterada",
        "Frontend preserva painel após timeout de refresh: reconectando, sem voltar a boot_failed; teste executa a função real para boot inicial e refresh",
        "Job real 457d265b: análise/sweep ~125 s; tradução exibida ~133 s inclui preflight, enquanto chamadas provider somam 3,607 s; interrupção por No space left on device ao gravar progresso",
        "Exclusão permanente autorizada de USERPROFILE/YomuExperimental: 452.474 arquivos / 66,29 GiB lógicos; um link não percorrido, projeto atual e Git comum em C:/Projetos/Yomu-Sekai preservados; disco ~93,1 GiB livres ao terminar",
        "350 + 114 testes passaram, 403 subtestes, 1 ignorado; Node timeout e diff/syntax verificados; serviço recarregado sem job ativo"
      ],
      "pending": [
        "PHYSICALLY_VERIFIED: novo job completo para confirmar consoles invisíveis, queda do pico de memória e recuperação da saída autenticada",
        "Resíduos SFX p3 abaixo do quadro e validação de todas as páginas CLEAN/PDF; job interrompido não gerou a pasta canônica images/clean"
      ],
      "links": [
        {
          "label": "Job, RAM e limpeza autorizada",
          "path": "reports/job_457d265b_runtime_20261108.md"
        },
        {
          "label": "Política de processos",
          "path": "yomu/runtime/process_options.py"
        },
        {
          "label": "Testes de subprocessos",
          "path": "tests/test_subprocess_ocr.py"
        },
        {
          "label": "Regressão de timeout",
          "path": "tests/test_bootstrap_refresh_timeout.mjs"
        }
      ]
    },
    {
      "id": "INPAINT-FOLLOWUP-20261108",
      "title": "Reparo aprovado de legenda, CLEAN de SFX e gargalos medidos",
      "domain": "pipeline",
      "column": "dev",
      "env": "local",
      "updated": "2026-11-08",
      "summary": "IMPLEMENTED / TESTED_OFFLINE / TESTED_FROZEN no checkout. Reparo FLUX da legenda aprovado e ativado localmente; p23 sem caixa preta, fonte antiga não legível e zero mudanças fora da máscara. CLEAN também limpa SFX marcados ignored pela opção desligada; PDF mantém o original. Composição final reutiliza pixels aprovados. Máscara v4 preservada; p60 passa com fallback conservador quando a v4 reprova a área.",
      "risk": "Último job real: 447,28 s na fila / 442,84 s no pipeline. Tempo total deste snapshot e meta de cinco minutos ainda não medidos no app. FLUX local da p23: 19,93 s. CLEAN agora executa trabalho SFX que antes era ignorado; replay não prova economia total. Duas falhas da suíte mais ampla reproduzidas também no snapshot anterior.",
      "delivered": [
        "Preferência SFX por usuário sem apagar outras preferências; snapshot no job/runner, incluindo fila e origem local",
        "CLEAN seleciona SFX com linhas rastreáveis independentemente da opção de typesetting; o PDF preserva o original quando desligada",
        "Sweep executado no executor de análise, com uma instância Paddle serializada e proveniência por página; medidas de parede de layout_preflight e post_translation",
        "Refinamento antes do preenchimento e reuso do candidato local no CLEAN; _sfx_glyph_halo_mask v4 idêntica ao backup anterior (comparação exata do segmento de fonte da função)",
        "Tipografia distingue a tinta do brilho e mede glifos por linha; halo roxo de tinta branca sobre fundo preto preservado sem contorno azul do preset",
        "Ação nativa explore via os.startfile para diretórios; restauração da janela e handles Win32 tipados, mantendo ownership e escopo de output",
        "08/11: 416 testes + 404 subtestes passaram, 1 ignorado. Replay real do SFX da p9 com opção desligada: saída final idêntica ao original, CLEAN alterou 42.057 pixels; 17,51 s com carga dos modelos. Contadores CLEAN/inpainting agora incluem esse passe.",
        "P23 TESTED_FROZEN com FLUX real: 16 glifos, 19,933901 s de modelo, 193.747 pixels alterados dentro e zero fora; zero linhas brancas protegidas alteradas. Cor espacial mediana 3,0899 / p95 21,3311; negativos preto/roxo e fonte original remanescente recusados.",
        "Commit CLEAN reutiliza o candidato já aprovado sem nova inferência. Teste isolado da p23 com FLUX congelado: render 16,655 -> 1,093 s, incluindo remoção de uma carga fria de LaMA; não extrapolado para o capítulo.",
        "P60: v4 parcial excedia razão máscara/núcleo 3,2476. Fallback conservador existente passa com razão 1,2864, cobertura 100% e OCR residual não legível; final idêntico ao original com SFX desligado. Limites e função v4 não relaxados.",
        "Snapshot final: 382 testes + 393 subtestes passaram, 1 ignorado. Default distribuído do reparo de legenda False; configuração local True; FLUX geral e tradução SFX False. App recarregado idle, HTTP 200 e worker online.",
        "Processo Vulkan usa o DIRECTML_LOCK canônico de LaMA/RapidOCR; fila de GPU e categoria sanitizada de falha nativa medidas. Uma repetição anterior sem lock compartilhado falhou em entregar arquivo e ficou corretamente sob revisão.",
        "Replay final com fonte vinculada: 65 páginas / 84 grupos, 114,945 s na fase local com dois workers. 77 remoções locais passam; CRUSH p19 segue art_fidelity_uncertain. Não inclui download/OCR inicial/sweep/provider/PDF e não demonstra redução do job completo. PNG RLE medido mais lento; codec preservado."
      ],
      "pending": [
        "PHYSICALLY_VERIFIED: novo capítulo de referência com este snapshot, card no Chrome e abertura visível do Explorer; hosts de Computer Use/navegador indisponíveis nesta sessão",
        "Tempo total menor que cinco minutos e fidelidade perfeita ainda não comprovados; mais paralelismo de GPU requer medição de memória/contenda",
        "Duas falhas preexistentes em test_art_reconstruction_quality (pontuação e linha cruzando letras); CRUSH p19 com fidelidade incerta, FluCK p10 com OCR inseguro e source echo de RocK? p20; fonte desenhada à mão permanece aproximação por família"
      ],
      "links": [
        {
          "label": "Ativação e medições atuais",
          "path": "reports/inpaint_activation_20261108.md"
        },
        {
          "label": "Relatório completo",
          "path": "reports/inpaint_followup_20261108.md"
        },
        {
          "label": "Opções verificadas na p23",
          "path": "reports/page23_options_20261108.md"
        },
        {
          "label": "Contrato SFX PDF/CLEAN",
          "path": "tests/test_sfx_output_preference.py"
        },
        {
          "label": "Glow medido",
          "path": "tests/test_neutral_lettering_glow.py"
        },
        {
          "label": "Propriedade e cor do efeito",
          "path": "tests/test_lettering_effects.py"
        }
      ]
    },
    {
      "id": "RENDER-GPU",
      "title": "Reconstrução visual + GPU DirectML",
      "domain": "pipeline",
      "column": "prod",
      "env": "main",
      "updated": "2026-10-26",
      "summary": "Preenchimento de gradiente, máscara de resíduo de contorno, letreiamento fiel à fonte original, sem inglês residual. RapidOCR e LaMa na GPU via DirectML com fallback CPU.",
      "delivered": [
        "Gradient fill + outline residue mask + menos revisões (e15b22b3, 25/10)",
        "Letreiamento fiel à fonte; vote de variante; retry em inglês residual (4a2d084a, 25/10)",
        "Clean evidence-based; balloon-shaped typesetting (7a5d1abc, 24/10)",
        "RapidOCR + LaMa no DirectML; lock por GPU; fallback CPU (4defde25, 25/10)",
        "Lock restrito ao run DirectML; OCR paralelo por página (5139fb0b, 26/10)",
        "Crop de reconstrução; LaMa por worker; batches maiores (052c0d51, 25/10)",
        "Pré-aquecimento LaMa movido para depois do OCR (0d3c1a6c, 26/10)"
      ],
      "links": [
        {
          "label": "ocr_balloon.py",
          "path": "yomu/ocr/ocr_balloon.py"
        },
        {
          "label": "benchmark_pipeline.py",
          "path": "yomu/pipeline/benchmark_pipeline.py"
        },
        {
          "label": "ocr_engine.py",
          "path": "yomu/ocr/ocr_engine.py"
        }
      ]
    },
    {
      "id": "OCR-TRANS",
      "title": "Qualidade OCR + tradução (inglês)",
      "domain": "pipeline",
      "column": "prod",
      "env": "main",
      "updated": "2026-10-26",
      "summary": "Sem leituras invertidas (use_cls=False). Palavras frequentes não tratadas como dano OCR. Palavras coladas separadas por frequência. SFX grandes fora dos grupos de diálogo. Ep. 33 resolvido.",
      "delivered": [
        "use_cls=False: sem leituras de cabeça para baixo (ae3340c7, 26/10)",
        "SFX grandes fora de grupos; quantidades OCR intactas (7b3ef443, 25/10)",
        "Palavras coladas separadas por frequência; nomes com honorífico mantidos (c4b265b4, 26/10)",
        "Regiões remanescentes do ep. 33 resolvidas (482c7ea6, 25/10)",
        "Sem inglês na arte; nomes mantidos; sem flood no console (933ace7a, 26/10)",
        "Piso de fonte segue letras pequenas da página (c456537c, 26/10)"
      ],
      "links": [
        {
          "label": "ocr_engine.py",
          "path": "yomu/ocr/ocr_engine.py"
        },
        {
          "label": "ocr_balloon.py",
          "path": "yomu/ocr/ocr_balloon.py"
        },
        {
          "label": "sfx_glossary.py",
          "path": "yomu/translation/sfx_glossary.py"
        }
      ]
    },
    {
      "id": "WORKER-UX",
      "title": "Worker confiável + fila + UX (modais, source request, feedback)",
      "domain": "infra",
      "column": "prod",
      "env": "main",
      "updated": "2026-10-26",
      "summary": "Jobs não falham mais por design. Fila traduz como o formulário principal. Modais de confirmação (sem alert/confirm nativo). Botão \"Solicitar Fonte\" e feedback chegam por e-mail.",
      "delivered": [
        "Capítulos não falham por design; legendas quando arte não pode ser reconstruída (37820c91, 26/10)",
        "Fila traduz como formulário principal; Webtoon mais rápido (fc625378, 26/10)",
        "Worker jobs terminam em vez de falhar; modais de confirmação; source request; feedback (ae3340c7, 26/10)"
      ],
      "links": [
        {
          "label": "worker_service.py",
          "path": "yomu/runtime/worker_service.py"
        },
        {
          "label": "tradutor_ui.js",
          "path": "static/tradutor_ui.js"
        },
        {
          "label": "ui_shell.html",
          "path": "ui/ui_shell.html"
        }
      ]
    },
    {
      "id": "COMIX-OPT",
      "title": "Comix: uma abertura por job, sem smart split em mangá",
      "domain": "infra",
      "column": "prod",
      "env": "main",
      "updated": "2026-10-26",
      "summary": "Comix abre o browser uma só vez por job. Smart split desativado para páginas de mangá (proporção alta). LaMa pré-aquecido depois do OCR, não durante o download.",
      "delivered": [
        "open_comix_once + sem smart split em páginas de mangá + LaMa pós-OCR (0d3c1a6c, 26/10)"
      ],
      "links": [
        {
          "label": "chapter_source.py",
          "path": "yomu/download/sources/chapter_source.py"
        }
      ]
    },
    {
      "id": "UI-LOGIN",
      "title": "Login redesenhado + tema Lua Rubra",
      "domain": "ui",
      "column": "prod",
      "env": "main",
      "updated": "2026-10-30",
      "summary": "Novo visual de login com tema Lua Rubra. Capturas de tela e GIF de demonstração atualizados no README.",
      "delivered": [
        "Login redesenhado + tema Lua Rubra (c5766173, 27/10)",
        "Capturas de tela atualizadas + GIF do login (89185e3a, 30/10)"
      ],
      "links": [
        {
          "label": "auth_ui.js",
          "path": "static/auth_ui.js"
        },
        {
          "label": "login-lua-rubra.gif",
          "path": "docs/assets/videos/login-lua-rubra.gif"
        }
      ]
    },
    {
      "id": "LANG-01",
      "title": "Múltiplos idiomas de origem (ja, ko, zh, ru, es…)",
      "domain": "pipeline",
      "column": "prod",
      "env": "main",
      "updated": "2026-11-03",
      "summary": "Cadeia completa: UI (langSelect habilitado) → payload (source_lang) → ui_bridge → build_run_command(--ocr-lang) → run_webtoon → benchmark_pipeline (ocr_lang override) → OCREngine (PADDLE_LANG_BY_CHOICE). Gates: score_group_ocr_quality não penaliza CJK/Cirílico; split_glued_source_words early-return para não-Latin; weak_label_semantic_promotion_allowed bypassa léxico inglês para texto logográfico/cirílico. 22 testes passando.",
      "delivered": [
        "feat(lang): suporte a múltiplos idiomas de origem (7ed2e01, 01/11)",
        "Mergeado na main (1c52366, 03/11)"
      ],
      "links": [
        {
          "label": "ocr_models.py",
          "path": "yomu/ocr/ocr_models.py"
        },
        {
          "label": "ocr_engine.py",
          "path": "yomu/ocr/ocr_engine.py"
        },
        {
          "label": "ocr_balloon.py",
          "path": "yomu/ocr/ocr_balloon.py"
        },
        {
          "label": "ui_shell.html",
          "path": "ui/ui_shell.html"
        },
        {
          "label": "benchmark_pipeline.py",
          "path": "yomu/pipeline/benchmark_pipeline.py"
        }
      ]
    },
    {
      "id": "GLOSSARY-01",
      "title": "Glossário de nomes por série",
      "domain": "ui",
      "column": "prod",
      "env": "main",
      "updated": "2026-11-03",
      "summary": "Glossário de nomes por série integrado ao Yomu-Sekai: UI (textarea + localStorage por série), payload (ui_bridge._name_glossary), backend (YOMU_NAME_GLOSSARY via job_runner, benchmark_pipeline), e set_name_overrides/_apply_name_overrides nos dois provedores. 32 testes passando.",
      "delivered": [
        "ui_shell.html: #nameGlossaryField + #nameGlossaryInput adicionados (a4a28dd, 02/11)",
        "static/tradutor_ui.js: nameGlossaryPairs(), rememberNameGlossary(), loadNameGlossary(), formPayload integrado (a4a28dd, 02/11)",
        "yomu/ui/ui_bridge.py: _name_glossary(), _source_language() integrados (a4a28dd, 02/11)",
        "yomu/runtime/job_runner.py: YOMU_NAME_GLOSSARY propagado para subprocess (a4a28dd, 02/11)",
        "yomu/pipeline/benchmark_pipeline.py: set_name_overrides() chamado após set_detected_names (a4a28dd, 02/11)",
        "yomu/translation/providers/translator_deepl.py: set_name_overrides/_apply_name_overrides integrados (a4a28dd, 02/11)",
        "yomu/translation/providers/yomu_backend_provider.py: idem (a4a28dd, 02/11)",
        "tests/test_name_glossary.py: 32 testes hermético (a4a28dd, 02/11)",
        "Mergeado na main (1c52366, 03/11)"
      ],
      "links": [
        {
          "label": "ui_shell.html",
          "path": "ui/ui_shell.html"
        },
        {
          "label": "ui_bridge.py",
          "path": "yomu/ui/ui_bridge.py"
        },
        {
          "label": "honorific_names.py",
          "path": "yomu/translation/honorific_names.py"
        },
        {
          "label": "translator_deepl.py",
          "path": "yomu/translation/providers/translator_deepl.py"
        }
      ]
    },
    {
      "id": "DOCS-01",
      "title": "Documentação técnica + guia do usuário atualizados",
      "domain": "infra",
      "column": "prod",
      "env": "main",
      "updated": "2026-11-03",
      "summary": "Documentação técnica (§14, §15), CONFIGURATION.md e Guia do Usuário atualizados para cobrir multi-idioma OCR (feat/LANG-01) e glossário de nomes (feat/GLOSSARY-01). Features marcadas como PARCIAL com ref de commit. Base verificada atualizada em todos os arquivos tocados.",
      "delivered": [
        "DOCUMENTACAO_TECNICA.md §14: OCR multi-idioma — tabela idioma→motor, ocr_models.py, gates CJK/Cirílico, fluxo ponta a ponta (5460cae, 02/11)",
        "DOCUMENTACAO_TECNICA.md §15: glossário de nomes — set_name_overrides, _apply_name_overrides, YOMU_NAME_GLOSSARY, limites (5460cae, 02/11)",
        "CONFIGURATION.md: TRADUTOR_OCR_MODELS_DIR (OCR) e YOMU_NAME_GLOSSARY (Tradução) documentados (5460cae, 02/11)",
        "GUIA_DO_USUARIO.md §9: idioma original com opções e nota de disponibilidade; glossário de nomes com exemplos (5460cae, 02/11)",
        "Base verificada atualizada em todos os documentos tocados (5460cae, 02/11)",
        "Mergeado na main (1c52366, 03/11)"
      ],
      "links": [
        {
          "label": "DOCUMENTACAO_TECNICA.md",
          "path": "docs/technical/DOCUMENTACAO_TECNICA.md"
        },
        {
          "label": "GUIA_DO_USUARIO.md",
          "path": "docs/user/GUIA_DO_USUARIO.md"
        },
        {
          "label": "CONFIGURATION.md",
          "path": "docs/CONFIGURATION.md"
        }
      ]
    },
    {
      "id": "CLEAN-SWEEP-01",
      "title": "Reparo conservador de SFX encontrados pela sweep",
      "domain": "pipeline",
      "column": "dev",
      "env": "branch",
      "updated": "2026-11-07",
      "summary": "Implementação local na branch claude/inpaint-auto-repair-20261107. Tradução de SFX agora fica desligada por padrão e o .env local não a reativa. O job de ep. 285 usou a primeira versão das máscaras e sweep; a recuperação de caixas largas do BLAST e as métricas de máscara efetiva foram acrescentadas depois e ainda aguardam run físico.",
      "delivered": [
        "Ep. 285, run 2c00c0f4-83dd-4b40-8bf7-04a1530a7543: 65 páginas concluídas, 80/80 traduções, 0 falhas de validação visual, 54 CLEAN certificados e 3 páginas com falha no certificado CLEAN",
        "A sweep recuperou e renderizou 2 grupos; página 52 BLAST ficou sem grupo automático porque a caixa ampla (800×1753 px) foi recusada. A página 28 ficou em revisão de completude da fonte; isso não prova resíduo visual",
        "Ajuste offline na imagem real da p. 52 reduziu a caixa BLAST para (0,849,800,734) px e o classificador a reconheceu como SFX; a tentativa de provider/render/inpaint desse novo caminho ainda aguarda run físico",
        "Máscara final é reconstruída após o estreitamento proporcional; fundo complexo usa limite máscara/texto 2.0 e pode tentar LaMA com o candidato estreito; balões simples mantêm limite 3.0",
        "Relatório por página/região mede máscara base e efetiva, expansão, mudanças dentro/fora, método, tentativas e motivo da decisão; as métricas efetivas mais recentes ainda não foram exercitadas fisicamente",
        "27 testes focados passaram (4 subtestes) antes desta mudança de configuração; a edição do default SFX ainda não foi testada pela suíte",
        "Comparação ep. 285: run de 365,9 s sem etapa de residual_sweep; run de 632,8 s gastou 100,6 s em residual_sweep, 5,7 s em tradução e 94,7 s em inpainting. O download variou de 60,8 s a 89,9 s; tempos de etapas somam trabalho paralelo e não fecham a diferença de parede.",
        "TRANSLATE_SFX agora é False no default de settings, na configuração local e no fallback de settings da UI; worker reiniciado sem jobs ativos e configuração efetiva confirmada como False",
        "RapidOCR isolado não leu BLAST na página 52 nem na página completa nem no recorte ampliado 2x; trocar Paddle por RapidOCR sem fallback perderia esse ghost confirmado",
        "Máscara acoplada ao traço (_sfx_glyph_halo_mask) + proibição de _line_box_mask retangular em SFX + roteamento direto lama_large (>= 8000 px) + LAB boundary feathering em AdvancedArtInpainter: 7/7 páginas de SFX do ep. 285 (p. 03, 04, 08, 09, 13, 18, 49) aprovadas offline em lama_large sem borrões retangulares",
        "Correção xyxy -> xywh no subprocess_ocr_worker (PaddleOCR v3 rec_boxes) + pré-mascaramento de caixas conhecidas (_mask_known_boxes) na residual_sweep: redução medida de 35%-52% no tempo de CPU do PaddleOCR e recuperação do CLINK na metade inferior da p. 04; 17 testes focados passando"
      ],
      "pending": [
        "Reduzir o custo da residual_sweep sem perder a detecção de fantasmas; desligar só a tradução de SFX não elimina os 100,6 s da varredura",
        "Medir o próximo run com SFX preservado para quantificar a economia no CLEAN/redraw e verificar que os sons originais não gerem manchas",
        "Avaliar uma varredura híbrida rápida que mantenha Paddle para os casos de lettering artístico não recuperados pelo RapidOCR ampliado",
        "Novo run físico do ep. 285 na branch atual: validar provider/render e tentativa de inpaint do BLAST com caixa estreita; comparar máscara base/efetiva e inspecionar antes/depois",
        "Tratar THUNK truncado na página 52: segue report-only até OCR produzir leitura e caixa confiáveis",
        "Acompanhar a página 28, que ficou em revisão de completude da fonte, apesar da remoção de texto marcada como concluída/verificada",
        "Bateria art reconstruction quality/fidelity anterior: 64 passaram, 13 ignorados e 2 falharam; baseline não foi comparado"
      ],
      "links": [
        {
          "label": "residual_sweep.py",
          "path": "yomu/ocr/residual_sweep.py"
        },
        {
          "label": "ocr_balloon.py",
          "path": "yomu/ocr/ocr_balloon.py"
        },
        {
          "label": "benchmark_pipeline.py",
          "path": "yomu/pipeline/benchmark_pipeline.py"
        },
        {
          "label": "test_residual_sweep.py",
          "path": "tests/test_residual_sweep.py"
        },
        {
          "label": "test_inpaint_mask_scope.py",
          "path": "tests/test_inpaint_mask_scope.py"
        }
      ]
    },
    {
      "id": "BUGFIX-TRANS-01",
      "title": "Fix: translate_strict aceita kwargs de retry do OCR",
      "domain": "pipeline",
      "column": "prod",
      "env": "main",
      "updated": "2026-11-04",
      "summary": "~78 regiões terminavam sem tradução: translate_strict do YomuBackendTranslationProvider não aceitava os kwargs extra que ocr_balloon.py passa nos 3 caminhos de retry (allow_proper_names, proper_names, retry_origin, retry_attempt, source_context). TypeError era capturado em silêncio e produzia candidato vazio. Assinatura alinhada com DeepLTranslator.translate_strict.",
      "delivered": [
        "Assinatura de translate_strict corrigida; 1 novo teste hermético (4cdcc8f, 03/11)",
        "Documentação §17 atualizada com descrição do bug e da correção (4cdcc8f, 03/11)",
        "Mergeado na main (b64f34f, 04/11)"
      ],
      "links": [
        {
          "label": "yomu_backend_provider.py",
          "path": "yomu/translation/providers/yomu_backend_provider.py"
        },
        {
          "label": "test_yomu_backend_provider.py",
          "path": "tests/test_yomu_backend_provider.py"
        }
      ]
    },
    {
      "id": "BUGFIX-UI-01",
      "title": "Fix: testes de form payload e langSelect após LANG/GLOSSARY",
      "domain": "ui",
      "column": "prod",
      "env": "main",
      "updated": "2026-11-04",
      "summary": "formPayload chama nameGlossaryPairs (ausente nos harneses de teste em dois arquivos); langSelect lido com $ helper como os campos vizinhos. Dois testes corrigidos.",
      "delivered": [
        "nameGlossaryPairs adicionada nos harneses de teste; langSelect com $ helper (85f8416, 03/11)",
        "Mergeado na main (b64f34f, 04/11)"
      ],
      "links": [
        {
          "label": "tradutor_ui.js",
          "path": "static/tradutor_ui.js"
        },
        {
          "label": "test_new_translation_source_policy_state.py",
          "path": "tests/test_new_translation_source_policy_state.py"
        },
        {
          "label": "test_ui_translation_provider_selection.py",
          "path": "tests/test_ui_translation_provider_selection.py"
        }
      ]
    },
    {
      "id": "PIPELINE-REF-01",
      "title": "Pipeline: correções pós-medição no capítulo de referência (ep. 285)",
      "domain": "pipeline",
      "column": "prod",
      "env": "main",
      "updated": "2026-11-08",
      "summary": "Pacote de correções medidas no ep. 285 (Hero Killer). Download: pool HTTP paralelo com fallback serial; \"strip\" do Webtoons dispara smart split. OCR: página só de arte vira OCR_SUFFICIENT; pontuação neutra para scripts não-latinos. Validação: nomes próprios só por detecção do capítulo; frases em inglês não ficam sem traduzir. Limpeza: máscara estendida ao halo do lettering; achatamento de resíduo em fundo escuro. Tipografia: tamanho inicial derivado da altura de tinta da fonte (não SFX/display). Certificado: páginas sem alvo passam; SFX/arte preservados não contam como resíduo. Manifest: commit registrado no início do run. UI: rótulos de ETA e política de fonte sempre ativa.",
      "delivered": [
        "download, OCR, limpeza, tipografia, certificado, manifest, UI (56e5b85, 04/11)",
        "20 novos testes herméticos adicionados no mesmo commit",
        "Documentação técnica e guia do usuário atualizados",
        "alinhamento, cor de tinta, restauração de nomes, certificado e cache (d819f0e, 05/11)",
        "7 novos testes herméticos de regressão; docs §17 atualizados"
      ],
      "links": [
        {
          "label": "benchmark_pipeline.py",
          "path": "yomu/pipeline/benchmark_pipeline.py"
        },
        {
          "label": "ocr_balloon.py",
          "path": "yomu/ocr/ocr_balloon.py"
        },
        {
          "label": "down.py",
          "path": "yomu/download/down.py"
        }
      ]
    },
    {
      "id": "GEMINI-01",
      "title": "Gemini/VPS clean — integração real",
      "domain": "release",
      "column": "blocked",
      "env": "none",
      "updated": "2026-10-26",
      "summary": "Código integrado e testes offline passando. Sem prova física: nenhum capítulo gerado real, VPS não verificado.",
      "blockedBy": "Precisa de: túnel SSH ativo, VPS com API/worker compatíveis, sessão Gemini autorizada e aprovação explícita para run com custo real.",
      "delivered": [
        "Readiness check, request/certificate validation, transport integrados na main"
      ],
      "pending": [
        "Smoke test físico com capítulo autorizado e VPS disponível",
        "Validação de esquema par cliente/servidor antes de promover visual recovery"
      ],
      "links": [
        {
          "label": "remote_readiness.py",
          "path": "yomu/runtime/remote_readiness.py"
        }
      ]
    },
    {
      "id": "HARMONIC-01",
      "title": "Classificação de borda harmônica",
      "domain": "pipeline",
      "column": "blocked",
      "env": "none",
      "updated": "2026-10-24",
      "summary": "Sinais de revisão automática funcionam. Relaxação segura exige labels reais de textura natural, franja de glifo fora da máscara e estruturas sob lettering.",
      "blockedBy": "Precisa de: conjunto de labels reais independentes (positivos de textura natural e negativos de glifo). Sem eles, qualquer relaxação das regras atuais é SUPOSIÇÃO.",
      "delivered": [
        "Overlays de borda e evidência de distância/coordenada (CLN-HARMONIC-03D)",
        "CLEAN_HARMONIC_FILL permanece off por padrão"
      ],
      "pending": [
        "Labels reais → avaliação de classificador de topologia → promoção para LOCAL_SAFE"
      ],
      "links": [
        {
          "label": "harmonic_fill.py",
          "path": "yomu/clean/inpainting/harmonic_fill.py"
        }
      ]
    },
    {
      "id": "RELEASE-01",
      "title": "Beta release + instalador Windows",
      "domain": "release",
      "column": "blocked",
      "env": "none",
      "updated": "2026-10-30",
      "summary": "CI passa. Beta não publicado. Nenhum gate físico foi provado: UI/licença, frozen worker, VPS/provider, Discord por evento, Clean. Instalador Windows (Setup.exe) não tem spec nem builder.",
      "blockedBy": "Precisa de: (1) smoke de UI + login + licença Supabase real; (2) smoke do frozen worker com owner presente; (3) aprovação para run com custo real (Gemini/VPS); (4) entrega Discord por evento; (5) spec + builder do Setup.exe.",
      "delivered": [
        "CI Windows passou: 6013 Python, 141 skipped, 2 xfailed (run 38830606731)",
        "Updater implementado (update_manifest.py, update_transport.py, update_installer.py)",
        "Beta license gate implementado (beta_license.py, aplicado em UiBridge.start/resume)"
      ],
      "pending": [
        "Smoke físico de UI + login + licença Supabase real",
        "Protocolo frozen worker com owner presente",
        "Instalador Windows (Setup.exe) — spec e builder inexistentes",
        "Superfície de UI do updater (botão/indicador na UI)"
      ],
      "links": [
        {
          "label": "RELEASE_CHECKLIST.md",
          "path": "docs/RELEASE_CHECKLIST.md"
        },
        {
          "label": "INSTALLATION.md",
          "path": "docs/INSTALLATION.md"
        },
        {
          "label": "update_manifest.py",
          "path": "yomu/runtime/update_manifest.py"
        }
      ]
    },
    {
      "id": "RENDER-SFX-02",
      "title": "Roteamento SFX → LaMA por fidelidade de borda + refinamento de máscaras",
      "domain": "pipeline",
      "column": "prod",
      "env": "main",
      "updated": "2026-11-08",
      "summary": "Gate de continuidade de borda para rotear SFX complexos ao LaMA com evidência medida. Fidelidade por OR entre tentativas; fallback mask persistida; telemetria de rastreamento. SFX grandes de arte-sobre-arte: rota direta ao LaMA. Validação do composite LaMA contra seu contrato. Retry com variante cores-only. Refinamento de máscaras de lettering SFX.",
      "delivered": [
        "edge-continuity fidelity gate para SFX complexos (864bc7a, 05/11)",
        "compute gate mesmo com strategy mask inválida (b2a9a36, 05/11)",
        "review-state SFX roteados ao LaMA por evidência medida (c08ec39, 05/11)",
        "telemetria quando rota bloqueada; fallback block trace (9688035, f72fbc0, 05/11)",
        "OR fidelity entre tentativas; fallback mask; trace todos SFX (538f4bc, 05/11)",
        "NameError Path corrigido no trace de SFX render (b4cf583, 05/11)",
        "densidades de borda incluídas no trace de fallback (a7f8f7b, 05/11)",
        "medir edge-continuity ring no artwork original (3a663c0, 05/11)",
        "decisão LaMA no ponto de evidência direta (2eb0d3d, 05/11)",
        "bbox de máscara + densidade de anel no trace de fallback (54f90ad, 05/11)",
        "SFX grandes over-art roteados ao LaMA por risk profile (a3febba, 05/11)",
        "validar composite LaMA contra seu contrato (850bfd7, 05/11)",
        "straight-to-LaMA para splash SFX grande; residual sweep de página (65db8b9, 06/11)",
        "refinamento de máscaras SFX; retry cores-only no LaMA (cda3f90, 06/11)"
      ],
      "links": [
        {
          "label": "benchmark_pipeline.py",
          "path": "yomu/pipeline/benchmark_pipeline.py"
        },
        {
          "label": "ocr_balloon.py",
          "path": "yomu/ocr/ocr_balloon.py"
        }
      ]
    },
    {
      "id": "RENDER-GEN-01",
      "title": "Reconstrução generativa de segunda chance (FLUX.2 klein via sd.cpp)",
      "domain": "pipeline",
      "column": "prod",
      "env": "main",
      "updated": "2026-11-08",
      "summary": "Quando o LaMA-large rejeita o composite por evidência (métricas de arte avançada), o fallback oferece a mesma máscara ao FLUX.2 klein (modelo de instrução/edição que condiciona no artwork vizinho) via sd.cpp Vulkan em subprocess. Output passa pelos mesmos validadores; rejeição vai a revisão com motivos de ambos os motores. Opt-in: GENERATIVE_INPAINT_ENABLED. Modelos (~5 GB): FLUX.2-klein Q4_0 + flux2-vae + Qwen3-4B.",
      "delivered": [
        "flux_edit.py: gate de disponibilidade, troca de imagem/máscara em temp-dir, composição inside-mask, timeout 240s (0fedd95, 06/11)",
        "GENERATIVE_INPAINT_ENABLED adicionado a settings.py (0fedd95, 06/11)",
        "ocr_balloon.py: integração do fallback generativo (0fedd95, 06/11)"
      ],
      "links": [
        {
          "label": "flux_edit.py",
          "path": "yomu/clean/inpainting/flux_edit.py"
        },
        {
          "label": "benchmark_pipeline.py",
          "path": "yomu/pipeline/benchmark_pipeline.py"
        },
        {
          "label": "settings.py",
          "path": "yomu/config/settings.py"
        }
      ]
    },
    {
      "id": "OCR-SFX-01",
      "title": "Re-OCR de última chance para regiões SFX (RapidOCR + Paddle subprocess)",
      "domain": "pipeline",
      "column": "prod",
      "env": "main",
      "updated": "2026-11-08",
      "summary": "Re-OCR de última chance para regiões SFX com crop ajustado no RapidOCR. Guard de repair-vs-echo para evitar que a correção repita o erro do OCR original. Escalonamento opcional ao PaddleOCR via subprocess isolado (evita contaminação de memória GPU).",
      "delivered": [
        "last-chance SFX re-OCR: RapidOCR crop, opt-in Paddle escalation (2ad6c10, 05/11)",
        "crop ajustado e guard repair-vs-echo (9b78d83, 05/11)",
        "Paddle escalation em subprocess isolado (3ebbadc, 06/11)"
      ],
      "links": [
        {
          "label": "ocr_balloon.py",
          "path": "yomu/ocr/ocr_balloon.py"
        },
        {
          "label": "ocr_engine.py",
          "path": "yomu/ocr/ocr_engine.py"
        }
      ]
    },
    {
      "id": "PIPELINE-05-01",
      "title": "Pipeline 05-06/11: gargalos, glossário SFX, tipografia semântica, UI e PDF",
      "domain": "pipeline",
      "column": "prod",
      "env": "main",
      "updated": "2026-11-08",
      "summary": "Gargalos de revisão OCR/Clean resolvidos; promoção de legenda display documentada; contabilidade de timing por etapa. Glossário SFX tolerante a erros de OCR; termos de lore protegidos; métricas honestas. Quebra de linha semântica pt-BR (palavras funcionais não ficam sozinhas no fim). Pasta de saída abre em Explorer visível e em foco. Proteção de pixel em clean-rescue; verificação de resíduo com limite; splits de PDF seguros.",
      "delivered": [
        "gargalos OCR/Clean, promoção de legenda display, timing por etapa (f274feb, 05/11)",
        "glossário SFX tolerante a OCR, lore terms protegidos, métricas honestas (76c129f, 05/11)",
        "quebra de linha semântica pt-BR sem palavras funcionais órfãs (d93e813, 06/11)",
        "abrir pasta de saída em Explorer visível e em foco (d06e0fb, 05/11)",
        "pixel protection clean-rescue, residual check limitado, PDF splits seguros (03b57ec, 05/11)"
      ],
      "links": [
        {
          "label": "benchmark_pipeline.py",
          "path": "yomu/pipeline/benchmark_pipeline.py"
        },
        {
          "label": "sfx_glossary.py",
          "path": "yomu/translation/sfx_glossary.py"
        },
        {
          "label": "tradutor_ui.js",
          "path": "static/tradutor_ui.js"
        }
      ]
    }
  ],
};
