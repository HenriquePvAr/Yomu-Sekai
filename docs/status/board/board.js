// Dados do quadro de avanço. Só leitura: Claude atualiza a pedido ("atualiza o quadro").
// Regra: cada card cita a evidência (SHA, data) que sustenta a coluna. Git vence memória.
// `risk` separa medido de suposto com MEDIDO / NÃO MEDIDO / SEM FONTE / SUPOSIÇÃO.
window.BOARD = {
  title: 'YomuSekai · Quadro',
  subtitle: 'HenriquePvAr/Yomu-Sekai',
  updatedAt: '2026-11-01',
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
    main:   'main do Yomu-Sekai',
    branch: 'branch claude/… no GitHub',
    none:   'sem código',
  },
  cards: [

    // ───────────────────────── PROD ─────────────────────────

    {
      id: 'RENDER-GPU',
      title: 'Reconstrução visual + GPU DirectML',
      domain: 'pipeline', column: 'prod', env: 'main',
      updated: '2026-10-26',
      summary: 'Preenchimento de gradiente, máscara de resíduo de contorno, letreiamento fiel à fonte original, sem inglês residual. RapidOCR e LaMa na GPU via DirectML com fallback CPU.',
      delivered: [
        'Gradient fill + outline residue mask + menos revisões (e15b22b3, 25/10)',
        'Letreiamento fiel à fonte; vote de variante; retry em inglês residual (4a2d084a, 25/10)',
        'Clean evidence-based; balloon-shaped typesetting (7a5d1abc, 24/10)',
        'RapidOCR + LaMa no DirectML; lock por GPU; fallback CPU (4defde25, 25/10)',
        'Lock restrito ao run DirectML; OCR paralelo por página (5139fb0b, 26/10)',
        'Crop de reconstrução; LaMa por worker; batches maiores (052c0d51, 25/10)',
        'Pré-aquecimento LaMa movido para depois do OCR (0d3c1a6c, 26/10)',
      ],
      links: [
        { label: 'ocr_balloon.py',        path: 'yomu/ocr/ocr_balloon.py' },
        { label: 'benchmark_pipeline.py', path: 'yomu/pipeline/benchmark_pipeline.py' },
        { label: 'ocr_engine.py',         path: 'yomu/ocr/ocr_engine.py' },
      ],
    },

    {
      id: 'OCR-TRANS',
      title: 'Qualidade OCR + tradução (inglês)',
      domain: 'pipeline', column: 'prod', env: 'main',
      updated: '2026-10-26',
      summary: 'Sem leituras invertidas (use_cls=False). Palavras frequentes não tratadas como dano OCR. Palavras coladas separadas por frequência. SFX grandes fora dos grupos de diálogo. Ep. 33 resolvido.',
      delivered: [
        'use_cls=False: sem leituras de cabeça para baixo (ae3340c7, 26/10)',
        'SFX grandes fora de grupos; quantidades OCR intactas (7b3ef443, 25/10)',
        'Palavras coladas separadas por frequência; nomes com honorífico mantidos (c4b265b4, 26/10)',
        'Regiões remanescentes do ep. 33 resolvidas (482c7ea6, 25/10)',
        'Sem inglês na arte; nomes mantidos; sem flood no console (933ace7a, 26/10)',
        'Piso de fonte segue letras pequenas da página (c456537c, 26/10)',
      ],
      links: [
        { label: 'ocr_engine.py',    path: 'yomu/ocr/ocr_engine.py' },
        { label: 'ocr_balloon.py',   path: 'yomu/ocr/ocr_balloon.py' },
        { label: 'sfx_glossary.py',  path: 'yomu/translation/sfx_glossary.py' },
      ],
    },

    {
      id: 'WORKER-UX',
      title: 'Worker confiável + fila + UX (modais, source request, feedback)',
      domain: 'infra', column: 'prod', env: 'main',
      updated: '2026-10-26',
      summary: 'Jobs não falham mais por design. Fila traduz como o formulário principal. Modais de confirmação (sem alert/confirm nativo). Botão "Solicitar Fonte" e feedback chegam por e-mail.',
      delivered: [
        'Capítulos não falham por design; legendas quando arte não pode ser reconstruída (37820c91, 26/10)',
        'Fila traduz como formulário principal; Webtoon mais rápido (fc625378, 26/10)',
        'Worker jobs terminam em vez de falhar; modais de confirmação; source request; feedback (ae3340c7, 26/10)',
      ],
      links: [
        { label: 'worker_service.py', path: 'yomu/runtime/worker_service.py' },
        { label: 'tradutor_ui.js',    path: 'static/tradutor_ui.js' },
        { label: 'ui_shell.html',     path: 'ui/ui_shell.html' },
      ],
    },

    {
      id: 'COMIX-OPT',
      title: 'Comix: uma abertura por job, sem smart split em mangá',
      domain: 'infra', column: 'prod', env: 'main',
      updated: '2026-10-26',
      summary: 'Comix abre o browser uma só vez por job. Smart split desativado para páginas de mangá (proporção alta). LaMa pré-aquecido depois do OCR, não durante o download.',
      delivered: [
        'open_comix_once + sem smart split em páginas de mangá + LaMa pós-OCR (0d3c1a6c, 26/10)',
      ],
      links: [
        { label: 'chapter_source.py', path: 'yomu/download/sources/chapter_source.py' },
      ],
    },

    {
      id: 'UI-LOGIN',
      title: 'Login redesenhado + tema Lua Rubra',
      domain: 'ui', column: 'prod', env: 'main',
      updated: '2026-10-30',
      summary: 'Novo visual de login com tema Lua Rubra. Capturas de tela e GIF de demonstração atualizados no README.',
      delivered: [
        'Login redesenhado + tema Lua Rubra (c5766173, 27/10)',
        'Capturas de tela atualizadas + GIF do login (89185e3a, 30/10)',
      ],
      links: [
        { label: 'auth_ui.js',            path: 'static/auth_ui.js' },
        { label: 'login-lua-rubra.gif',   path: 'docs/assets/videos/login-lua-rubra.gif' },
      ],
    },

    // ───────────────────────── DEV ─────────────────────────

    {
      id: 'LANG-01',
      title: 'Múltiplos idiomas de origem (ja, ko, zh, ru, es…)',
      domain: 'pipeline', column: 'dev', env: 'branch',
      fila: 1,
      updated: '2026-11-01',
      summary: 'Fila do agente: 1º. Seletor de idioma (#langSelect) existe na UI. ocr_models.py (download de modelos pp-ocr por idioma com verificação SHA), gates de não-inglês e lógica de detecção existem no branch de trabalho, mas ainda não foram integrados ao Yomu-Sekai. Problema ativo: ja/ru detectam 0 grupos; zh traduz 0 grupos.',
      pending: [
        'Integrar yomu/ocr/ocr_models.py (MODEL_BASE_URL, REC_MODELS com SHA, rec_model_for(), models_dir())',
        'Integrar source_is_english()/source_is_cjk() em ocr_engine.py',
        'Gates de não-inglês em ocr_balloon.py: score_group_ocr_quality, split_glued_source_words, reading_order CJK, _promote_glossary_sounds',
        'Gates em region_taxonomy.py: weak_label_semantic_promotion_allowed para não-inglês (2+ palavras ou 4+ CJK)',
        'Investigar 0 grupos em ja/ru: verificar no_text_precheck, detector de balão (assume latim?), filtros de ruído',
        'Testar com páginas sintéticas e/ou capítulo real em ru, ko, zh, ja',
      ],
      links: [
        { label: 'ocr_engine.py',    path: 'yomu/ocr/ocr_engine.py' },
        { label: 'ocr_balloon.py',   path: 'yomu/ocr/ocr_balloon.py' },
        { label: 'ui_shell.html',    path: 'ui/ui_shell.html' },
        { label: 'job_runner.py',    path: 'yomu/runtime/job_runner.py' },
      ],
    },

    {
      id: 'GLOSSARY-01',
      title: 'Glossário de nomes por série',
      domain: 'ui', column: 'dev', env: 'branch',
      fila: 2,
      updated: '2026-11-01',
      summary: 'Fila do agente: 2º. Campo #nameGlossaryInput (localStorage por série, ex.: "Sunless = Sunny") existe no branch de trabalho do Tradutor.Ia. Precisa ser integrado ao Yomu-Sekai: UI, payload, backend (name_glossary no job config → YOMU_NAME_GLOSSARY env).',
      pending: [
        'Adicionar #nameGlossaryField + #nameGlossaryInput à ui_shell.html',
        'Integrar nameGlossaryPairs(), rememberNameGlossary(), loadNameGlossary() no tradutor_ui.js',
        'Integrar _name_glossary() e _source_language() no ui_bridge.py (validação, limite 50 pares)',
        'Propagar YOMU_NAME_GLOSSARY → job_runner.py e benchmark_pipeline.py',
        'Integrar set_name_overrides() no translator_deepl.py e yomu_backend_provider.py',
      ],
      links: [
        { label: 'ui_shell.html',         path: 'ui/ui_shell.html' },
        { label: 'ui_bridge.py',          path: 'yomu/ui/ui_bridge.py' },
        { label: 'honorific_names.py',    path: 'yomu/translation/honorific_names.py' },
        { label: 'translator_deepl.py',   path: 'yomu/translation/providers/translator_deepl.py' },
      ],
    },

    {
      id: 'DOCS-01',
      title: 'Documentação técnica + guia do usuário atualizados',
      domain: 'infra', column: 'dev', env: 'branch',
      fila: 3,
      updated: '2026-11-01',
      summary: 'Fila do agente: 3º. Tech doc e guia do usuário precisam de seções sobre idioma original, glossário de nomes, modelos OCR (download automático, TRADUTOR_OCR_MODELS_DIR) e métricas de desempenho da GPU.',
      pending: [
        'Tech doc §18+: OCR multi-idioma, YOMU_SOURCE_LANG, ocr_models.py, gates, leitura vertical CJK',
        'CONFIGURATION.md: TRADUTOR_OCR_MODELS_DIR, YOMU_SOURCE_LANG',
        'Guia do usuário: "Idioma original", primeiro uso (download de modelo), status honesto por idioma',
        'Bump de "Base verificada" nos metadados de verificação',
      ],
      links: [
        { label: 'DOCUMENTACAO_TECNICA.md', path: 'docs/technical/DOCUMENTACAO_TECNICA.md' },
        { label: 'GUIA_DO_USUARIO.md',      path: 'docs/user/GUIA_DO_USUARIO.md' },
        { label: 'CONFIGURATION.md',        path: 'docs/CONFIGURATION.md' },
      ],
    },

    // ───────────────────────── BLOCKED ─────────────────────────

    {
      id: 'GEMINI-01',
      title: 'Gemini/VPS clean — integração real',
      domain: 'release', column: 'blocked', env: 'none',
      updated: '2026-10-26',
      summary: 'Código integrado e testes offline passando. Sem prova física: nenhum capítulo gerado real, VPS não verificado.',
      blockedBy: 'Precisa de: túnel SSH ativo, VPS com API/worker compatíveis, sessão Gemini autorizada e aprovação explícita para run com custo real.',
      delivered: [
        'Readiness check, request/certificate validation, transport integrados na main',
      ],
      pending: [
        'Smoke test físico com capítulo autorizado e VPS disponível',
        'Validação de esquema par cliente/servidor antes de promover visual recovery',
      ],
      links: [
        { label: 'remote_readiness.py', path: 'yomu/runtime/remote_readiness.py' },
      ],
    },

    {
      id: 'HARMONIC-01',
      title: 'Classificação de borda harmônica',
      domain: 'pipeline', column: 'blocked', env: 'none',
      updated: '2026-10-24',
      summary: 'Sinais de revisão automática funcionam. Relaxação segura exige labels reais de textura natural, franja de glifo fora da máscara e estruturas sob lettering.',
      blockedBy: 'Precisa de: conjunto de labels reais independentes (positivos de textura natural e negativos de glifo). Sem eles, qualquer relaxação das regras atuais é SUPOSIÇÃO.',
      delivered: [
        'Overlays de borda e evidência de distância/coordenada (CLN-HARMONIC-03D)',
        'CLEAN_HARMONIC_FILL permanece off por padrão',
      ],
      pending: [
        'Labels reais → avaliação de classificador de topologia → promoção para LOCAL_SAFE',
      ],
      links: [
        { label: 'harmonic_fill.py', path: 'yomu/clean/inpainting/harmonic_fill.py' },
      ],
    },

    {
      id: 'RELEASE-01',
      title: 'Beta release + instalador Windows',
      domain: 'release', column: 'blocked', env: 'none',
      updated: '2026-10-30',
      summary: 'CI passa. Beta não publicado. Nenhum gate físico foi provado: UI/licença, frozen worker, VPS/provider, Discord por evento, Clean. Instalador Windows (Setup.exe) não tem spec nem builder.',
      blockedBy: 'Precisa de: (1) smoke de UI + login + licença Supabase real; (2) smoke do frozen worker com owner presente; (3) aprovação para run com custo real (Gemini/VPS); (4) entrega Discord por evento; (5) spec + builder do Setup.exe.',
      delivered: [
        'CI Windows passou: 6013 Python, 141 skipped, 2 xfailed (run 38830606731)',
        'Updater implementado (update_manifest.py, update_transport.py, update_installer.py)',
        'Beta license gate implementado (beta_license.py, aplicado em UiBridge.start/resume)',
      ],
      pending: [
        'Smoke físico de UI + login + licença Supabase real',
        'Protocolo frozen worker com owner presente',
        'Instalador Windows (Setup.exe) — spec e builder inexistentes',
        'Superfície de UI do updater (botão/indicador na UI)',
      ],
      links: [
        { label: 'RELEASE_CHECKLIST.md', path: 'docs/RELEASE_CHECKLIST.md' },
        { label: 'INSTALLATION.md',      path: 'docs/INSTALLATION.md' },
        { label: 'update_manifest.py',   path: 'yomu/runtime/update_manifest.py' },
      ],
    },

  ],
};
