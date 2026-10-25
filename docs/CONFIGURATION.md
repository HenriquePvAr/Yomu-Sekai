# Configuração

Esta referência descreve as opções reais do `.env.example` e as poucas variáveis adicionais consumidas diretamente pelo código atual.

> **Base verificada:** `5f482ce1` (branch `main`) · **Revisado em:** 2026-10-24
>
> [Voltar ao README](../README.md)

## Como a configuração é carregada

`yomu/runtime/local_environment.py` carrega exclusivamente o `.env` localizado na raiz real
do projeto, sem procurar arquivos em diretórios pais, e depois o `.env.local` opcional (também
não versionado), que pode sobrescrever valores do `.env`. Variáveis já presentes no ambiente
do processo antes do carregamento sempre têm precedência; valores ausentes ou vazios usam o
default do código (`yomu/config/settings.py`, que chama esse helper ao ser importado). Em
testes herméticos (`TRADUTOR_IA_HERMETIC_TEST_ENV=1`) nenhum arquivo é carregado.

Valores booleanos verdadeiros aceitos: `1`, `true`, `yes` e `on`, sem distinção de caixa. Qualquer outro valor não vazio é interpretado como falso.

## Neste guia

- [Tradução](#tradução)
- [OCR e classificação](#ocr-e-classificação)
- [Downloader e Selenium](#downloader-e-selenium)
- [Máscara, texto e reconstrução](#máscara-texto-e-reconstrução)
- [Validação visual](#validação-visual)
- [Cache e resume](#cache-e-resume)
- [Paralelismo e recursos](#paralelismo-e-recursos)
- [Precheck, observabilidade e debug](#precheck-observabilidade-e-debug)
- [Páginas lógicas e PDF](#páginas-lógicas-e-pdf)
- [Contexto e UI](#contexto-e-ui)
- [Auth, licença, raízes e navegador](#auth-licença-raízes-e-navegador)

Comece sempre pelo template:

```powershell
Copy-Item .env.example .env
```

Não versione o `.env` e nunca use uma chave real em exemplos, issues ou logs.

## Tradução

Todo job com tradução habilitada usa o provider interno `yomu_backend`
(`yomu/translation/providers/yomu_backend_provider.py`), autenticado pelo JWT do usuário, que
chama o motor remoto **DeepL** no servidor (Edge Function
`supabase/functions/translation-execute`). O cliente nunca chama a DeepL diretamente e
`--translation-provider`/`DEFAULT_TRANSLATION_PROVIDER = "deepl"` (`yomu/ui/ui_helpers.py`)
são apenas metadado/guard: pedir `riva` ou `nemotron` num job habilitado falha fechado
(`provider_mismatch`). A base do backend é `YOMU_BACKEND_URL` ou, sem ela, `SUPABASE_URL`
(`YOMU_BACKEND_URL` não está no template). Com `YOMU_ENV=local`/`test` e `YOMU_TEST_BACKEND`
vazio/`mock`, um backend mock é usado.

As variáveis abaixo existem no template e em `yomu/config/settings.py`, mas as de DeepL/NVIDIA
só são lidas por caminhos legados/experimentais do cliente; `DEEPL_API_KEY` é, na prática,
segredo do servidor (Edge Function).

| Variável | Default do template | Obrigatória? | Finalidade |
| --- | --- | --- | --- |
| `DEEPL_API_KEY` | `sua_chave_aqui` | Não no cliente | Segredo do servidor de tradução; não necessário para jobs habilitados do cliente |
| `DEEPL_API_BASE_URL` | `https://api-free.deepl.com` | Não | Endpoint DeepL do caminho legado local |
| `DEEPL_MODEL_TYPE` | `quality_optimized` | Não | Tipo de modelo DeepL do caminho legado local |
| `NVIDIA_API_KEY` | `sua_chave_aqui` | Não | Credencial NVIDIA para caminhos legados (Riva/Nemotron) e OCR NVIDIA opcional |
| `NVIDIA_BASE_URL` | `https://integrate.api.nvidia.com/v1` | Não | Endpoint compatível com OpenAI |
| `NVIDIA_TRANSLATION_MODEL` | `nvidia/nemotron-3-super-120b-a12b` | Não | Modelo usado nas requisições |
| `NVIDIA_TRANSLATION_BATCH_SIZE` | `20` | Não | Quantidade máxima de grupos por lote |
| `NVIDIA_MAX_REQUESTS_PER_MINUTE` | `20` | Não | Limite global aplicado pelo cliente |
| `TRANSLATION_MODE` | `nvidia` | Não | Eixo legado de família de tradução (factory `get_translator`); não seleciona o provider de um job habilitado |
| `TRANSLATE_SFX` | `True` | Não | Traduz SFX (glossário pt-BR de onomatopeias em `assets/lexicon/sfx_en_pt.json`, depois o provider; sons desconhecidos mantêm o lettering); `False` preserva os grupos classificados como SFX |

O seletor de provider da UI (`#translationProviderField`) está oculto; o único fluxo de produto é o backend autenticado com DeepL. Os modos Google/NLLB/NVIDIA permanecem como compatibilidade legada, sem o contrato de validação end-to-end auditado.

## OCR e classificação

| Variável | Default | Finalidade |
| --- | --- | --- |
| `OCR_ENGINE` | `paddle` (código: `rapidocr`) | Valor cru do módulo; `_configure_mode` (`yomu/commands/run_webtoon.py`) o substitui por `effective_ocr_engine()` — RapidOCR nos dois modos — então definir esta variável não muda a engine de um job |
| `TRADUTOR_OCR_ENGINE_OVERRIDE` | vazio (fora do template) | Override por ambiente lido por `effective_ocr_engine()`; no Beta só `rapidocr` é aceito (`BETA_OCR_ENGINES`), qualquer outro valor é ignorado. O guard falha fechado se o engine não estiver instalado |
| `OCR_FALLBACK_ENGINE` | `paddle` (código: vazio) | Forçado para vazio pela CLI: fallback entre engines não faz parte do contrato Beta |
| `OCR_HYBRID_FALLBACK` | `True` (código: `False`) | Forçado para `False` pela CLI |
| `RAPIDOCR_ENABLED` | `False` (código: `True`) | Forçado para `True` pela CLI quando o engine é RapidOCR (sempre, no Beta) |
| `OCR_LEGACY_PADDLE_FALLBACK` | fora do template (código: `False`) | Opt-in de compatibilidade legacy do Paddle; não instalado no perfil Beta |
| `RAPIDOCR_MIN_CONFIDENCE` | `0.55` | Confidence mínima usada nos sinais de suspeita |
| `RAPIDOCR_SUSPICIOUS_TEXT_FALLBACK` | `True` | Aciona fallback diante de texto estruturalmente suspeito |
| `RAPIDOCR_PAGE_FALLBACK` | `True` | Recuperação de página no modo `quality`; a CLI a desliga no modo `fast` |
| `FAST_OCR_HEAVY_FALLBACK` | `False` | Opt-in para fallbacks nativos pesados no modo `fast`; o padrão preserva previsibilidade |
| `FAST_OCR_PAGE_TIMEOUT_SECONDS` | `45` | Limite de uma tentativa pesada por página no modo `fast` |
| `FAST_OCR_REGION_TIMEOUT_SECONDS` | `12` | Limite de uma tentativa pesada por região no modo `fast` |
| `FAST_OCR_FULL_FALLBACK_MAX_PAGES` | `0` | Máximo de páginas que podem usar Paddle completo no modo `fast` |
| `FAST_OCR_FULL_FALLBACK_MAX_REGIONS` | `4` | Máximo de regiões que podem usar Paddle completo no modo `fast` |
| `FAST_OCR_TOTAL_FALLBACK_BUDGET_SECONDS` | `60` | Orçamento total de fallback pesado por execução `fast` |
| `OCR_TEXT_REPAIR` | `True` | Habilita reparos conservadores de OCR |
| `OCR_TEXT_REPAIR_MODE` | `conservative` | Modo implementado para os reparos; outros valores desativam esse caminho |
| `OCR_QUALITY_CONTROL` | `True` | Calcula score e motivos de qualidade dos grupos |
| `OCR_REGION_SELECTIVE_FALLBACK` | `True` | Reprocessa apenas regiões suspeitas quando possível |
| `OCR_GROUP_FALLBACK_MAX_GROUPS` | `8` | Máximo de grupos regionais por página |
| `OCR_GROUP_FALLBACK_PADDING` | `34` | Padding, em pixels, ao redor do crop de fallback |
| `OCR_GROUP_MIN_QUALITY_SCORE` | `0.62` | Limiar base para seleção regional |
| `PRIORITIZE_ENCLOSED_TEXT` | `True` | Dá prioridade a evidências de texto em containers |

O fallback não substitui palavras por regras fixas. Ele pede novas leituras e compara candidatos. Ajustar thresholds pode aumentar custo, falsos positivos ou risco visual; mantenha os defaults até ter uma regressão reproduzível.

## Downloader e Selenium

| Variável | Default | Finalidade |
| --- | --- | --- |
| `SELENIUM_QUIT_TIMEOUT_SECONDS` | `20` | Limite para o encerramento normal do driver, restrito internamente a 1–300 s |
| `SELENIUM_CLEANUP_TIMEOUT_SECONDS` | `3` | Janela do cleanup seletivo, restrita a 0,25–30 s |

`CHROMEDRIVER_PATH` é suportada pelo código, mas não aparece no template. Se estiver vazia,
o código procura `chromedriver`/`chromedriver.exe` já presentes no `PATH` e, quando nenhum
driver local existe, deixa o Selenium Manager oficial resolver um driver compatível de
forma cacheada. Em testes herméticos (`TRADUTOR_IA_HERMETIC_TEST_ENV=1`) essa resolução
permanece desligada por padrão; defina `TRADUTOR_ALLOW_DRIVER_DOWNLOAD=1` apenas quando
quiser permitir explicitamente a resolução no ambiente de teste.

## Máscara, texto e reconstrução

| Variável | Default | Finalidade |
| --- | --- | --- |
| `TEXT_MASK_PADDING` | `3` | Expansão inicial da máscara do texto |
| `MAX_MASK_EXPANSION` | `8` | Limite de expansão durante tentativas visuais |
| `STRICT_MASK_BOUNDS` | `True` | Restringe a máscara à região segura |
| `MASK_COMPONENT_BASED` | `True` | Constrói máscaras a partir de componentes conectados |
| `WHITE_BALLOON_FLAT_FILL` | `True` | Permite preenchimento uniforme em balões brancos compatíveis |
| `ALLOW_LARGE_RECTANGLE_MASK` | `False` | Bloqueia por padrão retângulos amplos de limpeza |
| `TEXT_SAFE_PADDING` | `12` | Margem interna reservada para o texto traduzido |
| `MIN_FONT_SIZE` | `12` | Menor fonte permitida, com piso interno de 6 |
| `MAX_FONT_SIZE` | `42` | Maior fonte permitida |
| `MAX_TEXT_OVERFLOW_RATIO` | `0.01` | Overflow máximo antes de reprovação |
| `AUTO_LINE_WRAP` | `True` | Habilita quebra automática de linha |
| `AUTO_FONT_SHRINK` | `True` | Reduz a fonte quando necessário para caber |
| `TEXTURED_CAPTION_OVERLAY` | `True` | Usa overlay controlado em captions texturizadas |
| `CAPTION_OVERLAY_OPACITY` | `0.94` | Opacidade do overlay, limitada internamente a 0,35–0,95 |

Duas flags de tipografia existem só no código (fora do template, como os demais ajustes
finos de CLEAN/render), ambas com default `True`: `RENDER_FIT_BALLOON_SHAPE` quebra a tradução
seguindo o formato do balão fechado quando isso permite uma fonte maior, e
`RENDER_MATCH_SOURCE_SLANT` inclina o texto como o lettering original quando a fonte escolhida
é reta. Também só no código: `CLEAN_SURFACE_FILL` (default `True`) acrescenta o preenchimento
de degradê suave como candidato da limpeza (ver Documentação Técnica §16).

`PIPELINE_PAGE_WORKERS` (só no código, default `auto`): quantas páginas são analisadas,
pré-renderizadas e renderizadas ao mesmo tempo. `auto` usa um terço dos núcleos lógicos e uma
página por ~3 GB de memória livre, no máximo 4; valores explícitos de `1` a `4` são aceitos.

`FONT_PATH` também é suportada fora do template. Quando vazia, o código usa a resolução de fonte existente; quando definida, deve apontar para um arquivo local válido.

## Validação visual

| Variável | Default | Finalidade |
| --- | --- | --- |
| `VISUAL_DIFF_VALIDATION` | `True` | Compara página original e reconstruída |
| `VISUAL_QA_STRICT` | `True` | Aplica o contrato visual estrito |
| `MAX_OUTSIDE_CHANGE_RATIO` | `0.002` | Mudança máxima fora da região permitida |
| `MAX_OUTSIDE_COMPONENT_AREA` | `120` | Área máxima de um componente externo novo |
| `MAX_MASK_TO_TEXT_AREA_RATIO` | `3.0` | Relação máxima entre máscara e texto original |
| `REJECT_BALLOON_BORDER_DAMAGE` | `True` | Rejeita dano detectado na borda do container |
| `REJECT_TEXT_OVERFLOW` | `True` | Rejeita texto fora da safe area |
| `WHITE_BACKGROUND_MIN_BRIGHTNESS` | `205` | Brilho mínimo para fundo branco |
| `WHITE_BACKGROUND_MAX_STD` | `38` | Desvio-padrão máximo para fundo branco |
| `WHITE_BACKGROUND_MAX_SATURATION` | `42` | Saturação máxima para fundo branco |
| `WHITE_BACKGROUND_MIN_RATIO` | `0.70` | Proporção mínima de pixels compatíveis |
| `WHITE_BACKGROUND_MAX_TEXTURE` | `10` | Textura máxima aceita como fundo plano |
| `WHITE_BACKGROUND_MAX_EDGE_DENSITY` | `0.12` | Densidade máxima de bordas |
| `WHITE_BACKGROUND_MAX_DIAGONAL_LINES` | `2` | Máximo de linhas diagonais detectadas |
| `WHITE_ENCLOSURE_MIN_BRIGHTNESS` | `195` | Brilho mínimo de enclosure branco comum |
| `WHITE_ENCLOSURE_MIN_RATIO` | `0.70` | Proporção branca mínima do enclosure |
| `WHITE_ENCLOSURE_MAX_DARK_RATIO` | `0.20` | Proporção escura máxima |
| `WHITE_ENCLOSURE_MAX_SATURATION` | `28` | Saturação máxima |
| `WHITE_STYLIZED_ENCLOSURE_MIN_BRIGHTNESS` | `130` | Brilho mínimo para enclosure estilizado |
| `WHITE_STYLIZED_ENCLOSURE_MIN_RATIO` | `0.28` | Proporção clara mínima no modo estilizado |
| `WHITE_STYLIZED_ENCLOSURE_MAX_DARK_RATIO` | `0.45` | Proporção escura máxima no modo estilizado |
| `WHITE_STYLIZED_ENCLOSURE_MAX_SATURATION` | `8` | Saturação máxima no modo estilizado |
| `MAX_TEXTURED_MASK_GROUP_RATIO` | `0.18` | Fração máxima mascarada em grupo texturizado |
| `MAX_TEXTURED_MASK_COMPONENT_RATIO` | `0.10` | Fração máxima por componente texturizado |
| `REJECT_WHITE_PATCH_OUTSIDE_BALLOON` | `True` | Rejeita manchas brancas fora de balões |
| `REJECT_DARK_BLOTCH_ON_TEXTURED_ART` | `True` | Rejeita manchas escuras novas sobre arte |
| `MAX_NEW_DARK_COMPONENT_AREA` | `120` | Área máxima de componente escuro novo |
| `MAX_NEW_DARK_PIXEL_RATIO` | `0.04` | Proporção máxima de pixels escuros novos |
| `MAX_FLAT_FILL_RING_SPREAD` | `30.0` (fora do template, como as demais linhas desta tabela a partir daqui) | Spread de luminância (p5–p95) do anel limpo em volta da máscara acima do qual o fundo **não** é considerado plano; sem essa prova, preenchimento de cor única e máscara de quadrilátero OCR ficam proibidos. Balões reais medem até ~24, fumaça/tecido/ilustração a partir de ~43 |
| `FLAT_FILL_RING_RADIUS` | `12` | Raio do anel de contexto usado nessa medição |
| `MIN_FLAT_FILL_RING_PIXELS` | `64` | Pixels mínimos de anel para a medição valer |
| `REJECT_FLAT_PATCH_ON_TEXTURED_ART` | `True` | Rejeita reconstrução que virou bloco chapado sobre arte texturizada |
| `MAX_FLAT_PATCH_TEXTURE_RATIO` | `0.25` | Fração da textura do anel abaixo da qual o interior reconstruído é suspeito |
| `MAX_FLAT_PATCH_ABSOLUTE_TEXTURE` | `1.0` | Energia Laplaciana interna absoluta abaixo da qual a reconstrução é chapada de fato. Exigido **junto** com a razão: inpainting sempre suaviza, então só a razão condenaria reconstrução legítima de arte granulada (~2,8–3,8) |
| `MIN_FLAT_PATCH_COMPONENT_AREA` | `400` | Área mínima de componente sólido para o patch chapado ser condenado |
| `DETECT_RECONSTRUCTION_SEAMS` | `True` | Liga o detector de costura (`ART-SEAM-DETECTOR-001`): reprova reconstrução que criou uma borda visível onde a arte não tinha nenhuma |
| `SEAM_BAND_RADIUS` | `4` | Largura, em pixels, das bandas interna/externa comparadas em volta da borda da máscara |
| `MIN_SEAM_BAND_PIXELS` | `48` | Pixels mínimos por banda para a medição de costura valer |
| `MAX_SEAM_LUMINANCE_STEP` | `12.0` | Quanto a luminância pode saltar através da borda **além** do que ela já se move na mesma distância na arte intocada ao lado. Gradiente reconstruído suavemente marca ~0; bloco chapado no mesmo gradiente ~23 |
| `MIN_SEAM_TEXTURE_RATIO` | `0.35` | Energia de textura logo dentro da borda como fração do contexto intocado; abaixo disso a textura parou no limite da máscara. Suprimido quando o contexto é comprovadamente plano, para não condenar balões |
| `MAX_SEAM_BOUNDARY_HALO_DELTA` | `18.0` | Desvio de luminância de um anel que acompanha o contorno e diverge dos **dois** lados — halo de inpaint. Um contorno de origem diverge de apenas um lado |
| `SEAM_HIGH_CONFIDENCE_SCORE` | `1.0` | Um sinal isolado só retém a reconstrução ao atingir o dobro do próprio limite; abaixo disso é preciso um segundo sinal corroborando. Existe porque #81 provou que uma razão de textura ingênua gera falsos positivos |

`POST_RENDER_OCR_VALIDATION=False` no template, mas `_configure_mode` o liga automaticamente sempre que o engine é RapidOCR — ou seja, nos dois modos — para procurar texto-fonte que ainda permaneça visível depois do redraw.

## Cache e resume

| Variável | Default | Finalidade |
| --- | --- | --- |
| `FULL_FAST_MODE` | `True` | Flag de compatibilidade carregada pelo config; não controla diretamente uma etapa no fluxo atual |
| `ENABLE_OCR_CACHE` | `True` | Reutiliza leituras de OCR compatíveis |
| `ENABLE_TRANSLATION_CACHE` | `True` | Reutiliza traduções por texto e configuração |
| `ENABLE_IMAGE_PROCESS_CACHE` | `True` | Reutiliza páginas renderizadas compatíveis |
| `ENABLE_DOWNLOAD_CACHE` | `True` | Reutiliza o manifest e imagens de download válidos |

O diretório padrão é `%LOCALAPPDATA%\TradutorIA\cache` (`yomu/runtime/runtime_paths.py`), configurável por `CACHE_ROOT` (presente no template, vazio por padrão). As chaves incluem hashes e versões internas. Não edite manifests nem apague todo o cache como primeira tentativa de diagnóstico; prefira `--force` quando precisar de reprocessamento controlado.

## Paralelismo e recursos

| Variável | Default | Finalidade |
| --- | --- | --- |
| `OCR_PARALLEL` | `True` | Permite OCR com workers |
| `OCR_WORKERS` | `2` | Quantidade inicial de workers, sempre pelo menos 1 |
| `ADAPTIVE_PARALLELISM` | `False` | Permite ao scheduler ajustar concorrência |
| `RESOURCE_MONITORING` | `False` | Grava amostras e relatórios de recursos |
| `RESOURCE_MONITOR_INTERVAL_SECONDS` | `1.0` | Intervalo entre amostras |
| `MIN_OCR_WORKERS` | `1` | Piso do scheduler adaptativo |
| `MAX_OCR_WORKERS` | `2` | Teto do scheduler adaptativo |
| `OCR_WORKER_INITIAL_PEAK_MB` | `1800` | Estimativa inicial de pico por worker |
| `MEMORY_SAFETY_MARGIN_PERCENT` | `20` | Margem aplicada ao cálculo de capacidade |
| `MIN_SYSTEM_RESERVE_GB` | `4` | RAM reservada ao sistema |
| `PIPELINE_MEMORY_RESERVE_GB` | `1` | Reserva adicional do pipeline |
| `MEMORY_PRESSURE_ELEVATED_PERCENT` | `72` | Limiar de pressão elevada |
| `MEMORY_PRESSURE_HIGH_PERCENT` | `82` | Limiar de pressão alta |
| `MEMORY_PRESSURE_CRITICAL_PERCENT` | `90` | Limiar de pressão crítica |
| `CPU_PRESSURE_HIGH_PERCENT` | `92` | Limiar de CPU alta |
| `WORKER_SCALE_UP_COOLDOWN_SECONDS` | `20` | Cooldown para aumentar workers |
| `WORKER_SCALE_DOWN_COOLDOWN_SECONDS` | `8` | Cooldown para reduzir workers |
| `OCR_QUEUE_MULTIPLIER` | `10` | Multiplicador do limite da fila |
| `TRANSLATION_PARALLEL` | `True` | Permite lotes de tradução concorrentes |
| `TRANSLATION_WORKERS` | `2` | Quantidade máxima de workers de tradução |

Em máquinas com pouca memória, reduza primeiro `OCR_WORKERS` e `TRANSLATION_WORKERS`. Não diminua reservas do sistema apenas para forçar uma execução.

## Precheck, observabilidade e debug

| Variável | Default | Finalidade |
| --- | --- | --- |
| `SKIP_NO_TEXT_IMAGES` | `True` | Evita OCR completo em páginas sem sinais de texto |
| `NO_TEXT_SKIP_CONSERVATIVE` | `True` | Mantém o precheck deliberadamente conservador |
| `CLASSIFICATION_PROFILING` | `False` | Produz perfil JSON/CSV/HTML da classificação |
| `DEBUG_VISUAL` | `False` | Ativa visualizações de diagnóstico |
| `SAVE_FULL_DEBUG` | `False` | Persiste debug completo por página |
| `SAVE_COMPARE_SAMPLES` | `True` | Gera amostras comparativas |
| `SAVE_DEBUG_ONLY_ERRORS` | `True` | Limita debug detalhado a erros |
| `POST_RENDER_OCR_VALIDATION` | `False` | Valida texto residual depois do redraw |

Ativar debug completo aumenta uso de disco e tempo. Os arquivos gerados podem conter páginas processadas e não devem ser publicados automaticamente.

## Páginas lógicas e PDF

| Variável | Default | Finalidade |
| --- | --- | --- |
| `SMART_WEBTOON_PDF_SPLIT` | `True` | Reconstrói fatias do viewer em páginas lógicas |
| `SMART_PDF_TARGET_HEIGHT` | `1800` | Altura-alvo da página lógica |
| `SMART_PDF_MIN_HEIGHT` | `1050` | Altura mínima |
| `SMART_PDF_MAX_HEIGHT` | `2400` | Altura máxima |

O código aplica pisos internos aos três tamanhos e garante que o máximo seja maior que o mínimo.

## Contexto e UI

O contexto do capítulo é controlado por flags da CLI, não por variáveis do template:

- padrão: mantém `session_context.json`;
- `--no-context`: não usa contexto;
- `--delete-context-after`: remove o contexto somente depois que o PDF existe;
- `--keep-context`: explicita o comportamento padrão.

A porta da UI pode ser alterada com uma variável lida por `yomu/ui/app.py` (e pelo shell desktop `yomu/desktop/app.py`):

```dotenv
TRADUTOR_UI_PORT=8080
```

## Variáveis avançadas fora do template

Estas opções existem no código, mas foram omitidas do `.env.example` para manter o caminho principal menor:

| Variável | Default | Uso |
| --- | --- | --- |
| `CHROMEDRIVER_PATH` | vazio | Driver explícito quando a descoberta automática falha |
| `TESSERACT_CMD` | caminho convencional do Windows | Executável opcional de Tesseract; não é necessário no fluxo principal |
| `FONT_PATH` | vazio | Fonte local opcional para redraw |
| `MAX_RETRIES_DOWNLOAD` | `5` | Tentativas por download |
| `OCR_CONF_THRESHOLD` | `15` | Threshold legado usado por caminhos compatíveis |
| `TRANSLATION_VALIDATION` | `True` | Habilita o validator textual |
| `TRANSLATION_RETRY_ON_MIXED_LANGUAGE` | `True` | Solicita retry quando há mistura detectada |
| `TRANSLATION_MAX_RETRIES` | `2` | Máximo de retries de validação |
| `VISUAL_DIFF_THRESHOLD` | `26` | Threshold de diferença visual |
| `TRADUTOR_UI_PORT` | `8080` | Porta do servidor local |

Evite configurar opções legadas ou avançadas sem uma razão reproduzível. Mudanças em thresholds alteram o contrato do cache e podem dificultar comparações.

## Auth, licença, raízes e navegador

Seções do template não detalhadas acima (consumidores em `yomu/`):

| Variável | Default do template | Finalidade |
| --- | --- | --- |
| `COMMUNITY_AUTH_PROVIDER` | `local` (código: `supabase`) | `local` (sessão loopback de desenvolvimento) ou `supabase` (JWT verificado por JWKS) |
| `SUPABASE_URL`, `SUPABASE_PUBLISHABLE_KEY` | vazio | Configuração **pública** do projeto Supabase; usada pelo login, licença e backend de tradução |
| `SUPABASE_SECRET_KEY` | vazio | Somente scripts administrativos locais; **nunca** no cliente distribuído, no frontend ou no Git |
| `SUPABASE_JWKS_URL`, `SUPABASE_EXPECTED_ISSUER`, `SUPABASE_EXPECTED_AUDIENCE` | vazio / `authenticated` | Verificação do JWT; derivadas de `SUPABASE_URL` quando vazias |
| `SUPABASE_SITE_URL`, `SUPABASE_REDIRECT_URL` | `http://127.0.0.1:8080`, `…/auth/callback` | URLs de retorno do fluxo de e-mail |
| `BETA_LICENSE_PROVIDER` | `local_development` | `local_development` (dev) ou `supabase` (Beta). Num runtime empacotado/desktop sem provider remoto o gate falha fechado; nunca faz downgrade silencioso |
| `TRADUTOR_UI_HOST`, `TRADUTOR_ALLOW_EXTERNAL_BIND` | `127.0.0.1`, `0` | Servidor permanece em loopback salvo opt-in explícito |
| `COMMUNITY_STORAGE_PROVIDER` | `filesystem` | `filesystem` ou `google_drive` para PDFs publicados |
| `TRADUTOR_USER_DATA_ROOT`, `TRADUTOR_RUNTIME_ROOT`, `TRADUTOR_OUTPUT_ROOT` | vazio | Overrides das raízes mutáveis; vazio = `%LOCALAPPDATA%\TradutorIA\{runtime,output}` |
| `SOURCE_BROWSER_ENGINE`, `SOURCE_BROWSER_EXECUTABLE`, `SOURCE_BROWSER_HEADLESS`, … | vazio / `1` | Navegador isolado usado somente na análise segura da fonte |
| `TRADUTOR_IA_UPDATE_MANIFEST_URL` | fora do template | Override da URL do manifest do updater (`yomu/runtime/update_bootstrap.py`, `yomu/ui/app.py`); ausente usa `DEFAULT_MANIFEST_URL`, definida vazia desliga a verificação (`not_configured`) |

## Exemplo mínimo recomendado

```dotenv
SUPABASE_URL=<url-do-projeto>
SUPABASE_PUBLISHABLE_KEY=<chave-publishable>
COMMUNITY_AUTH_PROVIDER=supabase
BETA_LICENSE_PROVIDER=supabase

OCR_QUALITY_CONTROL=True
OCR_REGION_SELECTIVE_FALLBACK=True
TRANSLATE_SFX=True

ENABLE_OCR_CACHE=True
ENABLE_TRANSLATION_CACHE=True
ENABLE_IMAGE_PROCESS_CACHE=True
ENABLE_DOWNLOAD_CACHE=True
```

Para problemas de inicialização ou recursos, consulte [Troubleshooting](TROUBLESHOOTING.md).
