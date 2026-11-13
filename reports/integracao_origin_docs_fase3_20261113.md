# Integração de `origin/docs` com a Fase 3

**Estado:** validação offline concluída; integração preparada na worktree `integracao-docs-fase3`. Sem push, sem merge em `dev`/`main`, sem tag, release ou execução de build/release.

## Escopo e proveniência

- A integração parte da branch `fase-3-qualidade` em `b64691b` e incorpora `origin/docs` (`12176c9`). O merge ainda estava no working tree ao rodar os testes; os relatórios de execução registram o HEAD base `b64691b`, enquanto o código de import passou pelo pacote `komyst` da worktree.
- Foram mantidas as alterações Fase 0/Fase 3 e aplicados os nomes Komyst aos imports, provider interno, variáveis, app e packaging. O identificador `yomu_backend` não é contrato de servidor: o backend armazena/expõe `deepl`; o nome antigo era interno. Não foi mantida compatibilidade ou migração.
- O caminho do provider do app é `komyst_backend`; ele continua sendo uma identificação local. Nenhum RPC, configuração remota ou valor persistido precisa conservar `yomu_backend`.
- Busca final de imports e invocações `yomu.*` não encontrou uso ativo. As ocorrências antigas restantes são apenas a URL externa do manifesto de atualização e o domínio externo real de anúncios, ambos listados ao fim deste relatório.

## Verificações

- `python -c` e `python -s -c`: OpenCV `5.0.0`; `DmlExecutionProvider` disponível; `komyst.__file__` aponta para esta worktree.
- Suíte completa: **6.513 passed, 141 skipped, 1 xfailed, 7 warnings, 787 subtests**, em 945,76 s.
- `git diff --check` e verificação de links Markdown: sem erros de whitespace ou links quebrados. O board carrega em Node com 25 IDs únicos, referências válidas e zero links mortos.
- Referências de packaging verificadas estaticamente: `packaging/Komyst.iss`, `packaging/komyst.spec` e `tools/build_installer.py` estão presentes. Nenhum build foi executado, pois esses arquivos foram tocados na integração.

## REF-A — Apenas Clean, sem tradução paga

Os três runs usaram as mesmas 65 páginas lógicas; a impressão SHA-256 ordenada de `smart_input_pages` é `6e692980577e8bda0109f7b37281fc9651086105162d71bb02d1d0de6634affb`, idêntica à entrada da validação F3.1. Todos produziram 65 PNGs. OCR registrou DirectML. A tradução foi explicitamente desativada; `DEEPL_REQUEST_ATTEMPTED=NO`.

| Run | Tempo total | Certificados | Revisão | Dispositivo de LaMa | Observação |
|---|---:|---|---|---|
| Base F3.1 `komyst_f3_1_refa_clean` | 317,87 s | 62 PASS | p10, p22, p23 | DirectML | Run URL anterior; mesma entrada de imagem |
| Merge, defaults de modelo | 295,89 s | 60 PASS | p10, p18, p22, p23, p60 | não usado | Modelo avançado não encontrado no diretório Komyst; não comparar certificados com o baseline |
| Merge, caminho de modelo temporário | 231,71 s | 62 PASS | p10, p22, p23 | DirectML | 65/65 PNGs; mesmos certificados e páginas em revisão do baseline |

Na rodada com defaults, p18 e p60 trocaram `learned_texture_fill` por `local_ring_median`. O modelo avançado existe fora do repositório, mas não no novo diretório padrão Komyst. Para a comparação final usei `ADVANCED_ART_INPAINT_MODEL_PATH` apontando para o arquivo já existente e `GENERATIVE_INPAINT_MODEL_DIR` apontando para os modelos FLUX existentes, somente no processo de medição. Não movi arquivos nem alterei `.env`. A rodada controlada restaurou `learned_texture_fill` em p18/p60 e reproduziu exatamente os 62 PASS + p10/p22/p23 em revisão do baseline. Isso confirma equivalência de qualidade no conjunto de referência.

O total de 231,71 s não é comparável ao tempo URL do baseline como ganho de throughput: a rodada final recebeu as 65 páginas já divididas por `--local-folder` e não pagou download nem smart split. `timing_report.json` acumula tempos de etapas executadas por páginas concorrentes; na rodada final registrou 275,61 s em inpainting e 261,08 s em residual sweep, maiores que o wall time e não somáveis. O custo direto do monitor foi 1,95 s em 23 amostras (10 s de intervalo; cerca de 0,84% do wall time).

Na validação, `GENERATIVE_INPAINT_ENABLED=true` não foi suficiente para usar FLUX enquanto o diretório default estava ausente; a última rodada deixou p23 em revisão como no baseline. A rodada validada não afirma que FLUX melhorou p23.

## DOCUMENTATION IMPACT

- Atualizados: `README.md`, `docs/README.md`, `CLAUDE.md`, `docs/DEVELOPMENT.md`, guia do beta, guia de instalação e guia do usuário; status de licença beta, instalador, instalação limpa e atualizador reescrito com evidência do repositório e com o resultado do tester marcado como informado pelo dono, `v0.9.1-beta.18`, data não informada.
- Atualizados também os documentos técnicos, branding, checklist e congelamento de qualidade para separar instalação limpa informada pelo tester de uma verificação feita nesta sessão.
- O usuário não precisa mais instalar a partir do repositório no início rápido. Configuração de `SUPABASE_URL`, chave publicável e `python start_tradutor.py` foi deslocada para Desenvolvimento; a proibição de segredos de servidor foi mantida.
- Os relatórios históricos de tarefas e consolidação foram removidos do conteúdo ativo. A relação completa de todos os caminhos removidos pelo Git nesta integração segue abaixo.

## Exceções externas que permanecem

- `https://raw.githubusercontent.com/HenriquePvAr/YomuSekai-Releases/main/updates/beta/latest.json`: URL externa configurada do manifesto de atualização; mantida como contrato externo aprovado.
- `yomusekai.com.br`: domínio externo real usado pelos anúncios/CSP/allowlist; mantido como integração externa existente.

## Caminhos removidos do repositório

Os caminhos abaixo são todos os arquivos reportados como removidos por `git diff HEAD --diff-filter=D` no estado integrado (415 arquivos). Parte dos marcadores `__init__.py` foi removida durante a troca do pacote; módulos correspondentes foram renomeados para `komyst/`, não descartados. Os relatórios e documentos históricos removidos são preservados no histórico Git.

```text
docs/consolidation/YOMU_CONSOLIDATION_PLAN.md
docs/consolidation/YOMU_CURRENT_PRODUCT_STATE.md
docs/consolidation/YOMU_SOURCE_RECONCILIATION_MATRIX.md
docs/consolidation/YOMU_WORKTREE_ARCHIVE_PLAN.md
docs/consolidation/YOMU_WORKTREE_INVENTORY.md
docs/research/colab-inpainting/YOMU_GPU_INTEGRATION_PROPOSAL.md
docs/status/relatorios/2026-11-01-LANG-01.md
docs/status/relatorios/2026-11-02-BUGFIX-pipeline.md
docs/status/relatorios/2026-11-02-DOCS-01.md
docs/status/relatorios/2026-11-02-GLOSSARY-01.md
docs/status/relatorios/2026-11-02-sessao-2.md
docs/status/relatorios/2026-11-02-sessao-3.md
docs/status/relatorios/2026-11-02-sessao-4.md
docs/status/relatorios/2026-11-02-sessao-5.md
docs/status/relatorios/2026-11-02-sessao.md
docs/status/relatorios/2026-11-03-bugfix-trans-ui.md
packaging/TradutorIA.iss
reports/auth_login_startup_v1/auth_startup_root_cause.json
reports/auth_login_startup_v1/final_report.md
reports/auth_login_startup_v1/git_preflight.json
reports/clean_only_ui_outputplan_v1/build_manifest.json
reports/clean_only_ui_outputplan_v1/contract_matrix.json
reports/clean_only_ui_outputplan_v1/desktop_smoke.json
reports/clean_only_ui_outputplan_v1/final_report.json
reports/clean_only_ui_outputplan_v1/git_preflight.json
reports/clean_only_ui_outputplan_v1/root_cause.json
reports/clean_only_ui_outputplan_v1/root_policy.json
reports/clean_only_ui_outputplan_v1/secret_scan.json
reports/clean_only_ui_outputplan_v1/test_results.json
reports/clean_parallel_20261108.md
reports/comix_challenge_v1/adaptive_resolver_audit.json
reports/comix_challenge_v1/build.json
reports/comix_challenge_v1/challenge_classifier.json
reports/comix_challenge_v1/final_report.json
reports/comix_challenge_v1/focused_tests.json
reports/comix_challenge_v1/full_tests.json
reports/comix_challenge_v1/git_preflight.json
reports/comix_challenge_v1/job_abort_root_cause.json
reports/comix_challenge_v1/job_state_contract.json
reports/comix_challenge_v1/product_head_audit.json
reports/comix_challenge_v1/real_source_probe.json
reports/comix_challenge_v1/resume_contract.json
reports/comix_challenge_v1/secret_scan.json
reports/comix_challenge_v1/source_strategy_audit.json
reports/comix_challenge_v1/ui_output_format_audit.json
reports/comix_missing_logical_page_79_v1/build_manifest.json
reports/comix_missing_logical_page_79_v1/controlled_source_download.json
reports/comix_missing_logical_page_79_v1/final_report.json
reports/comix_missing_logical_page_79_v1/git_preflight.json
reports/comix_missing_logical_page_79_v1/recovery_decision.json
reports/comix_missing_logical_page_79_v1/root_cause_before_fix.json
reports/comix_missing_logical_page_79_v1/tests.json
reports/concurrency2_confirmation_e2e_v1/benchmark_protocol.json
reports/concurrency2_confirmation_e2e_v1/concurrency_decision.json
reports/concurrency2_confirmation_e2e_v1/dataset_manifest.json
reports/concurrency2_confirmation_e2e_v1/final_report.json
reports/concurrency2_confirmation_e2e_v1/focused_tests.json
reports/concurrency2_confirmation_e2e_v1/m20_readiness_after_operational_e2e.json
reports/concurrency2_confirmation_e2e_v1/multi_image_job_manifest.json
reports/concurrency2_confirmation_e2e_v1/product_head_audit.json
reports/concurrency2_confirmation_e2e_v1/production_config_before_after.json
reports/concurrency2_confirmation_e2e_v1/root_policy.json
reports/concurrency2_confirmation_e2e_v1/secret_scan.json
reports/concurrency2_confirmation_e2e_v1/vps_final_health.json
reports/discord_observability_v1/current_observability_audit.json
reports/discord_observability_v1/discord_config_audit.json
reports/discord_observability_v1/event_contract.json
reports/discord_observability_v1/event_matrix.json
reports/discord_observability_v1/final_report.json
reports/discord_observability_v1/git_preflight.json
reports/discord_observability_v1/live_results.json
reports/discord_observability_v1/product_head_audit.json
reports/discord_observability_v1/redaction_contract.json
reports/discord_observability_v1/root_policy.json
reports/discord_observability_v1/secret_scan.json
reports/discord_observability_v1/vps_preflight.json
reports/gemini_chat_slot_v1/current_chat_reuse_experiment.json
reports/gemini_chat_slot_v1/current_worker_chat_audit.json
reports/gemini_chat_slot_v1/discord_slot_observability.json
reports/gemini_chat_slot_v1/dom_baseline_strategy.json
reports/gemini_chat_slot_v1/dom_tests.json
reports/gemini_chat_slot_v1/final_report.json
reports/gemini_chat_slot_v1/full_tests.json
reports/gemini_chat_slot_v1/git_preflight.json
reports/gemini_chat_slot_v1/live_hashes.json
reports/gemini_chat_slot_v1/live_reuse_3.json
reports/gemini_chat_slot_v1/live_reuse_5.json
reports/gemini_chat_slot_v1/new_output_detection.json
reports/gemini_chat_slot_v1/ownership_contract.json
reports/gemini_chat_slot_v1/product_head_audit.json
reports/gemini_chat_slot_v1/queue_behavior.json
reports/gemini_chat_slot_v1/queue_tests.json
reports/gemini_chat_slot_v1/restart_recovery.json
reports/gemini_chat_slot_v1/restart_test.json
reports/gemini_chat_slot_v1/root_policy.json
reports/gemini_chat_slot_v1/rotation_policy.json
reports/gemini_chat_slot_v1/secret_scan.json
reports/gemini_chat_slot_v1/slot_contract.json
reports/gemini_chat_slot_v1/slot_state_machine.json
reports/gemini_chat_slot_v1/stale_output_firewall.json
reports/gemini_chat_slot_v1/unit_tests.json
reports/gemini_chat_slot_v1/vps_deploy.json
reports/gemini_concurrency2_v1/atomic_acquire.json
reports/gemini_concurrency2_v1/benchmark_c1.json
reports/gemini_concurrency2_v1/benchmark_c2.json
reports/gemini_concurrency2_v1/benchmark_comparison.json
reports/gemini_concurrency2_v1/browser_architecture_a_results.json
reports/gemini_concurrency2_v1/browser_architecture_audit.json
reports/gemini_concurrency2_v1/concurrent_gate_2.json
reports/gemini_concurrency2_v1/concurrent_gate_4.json
reports/gemini_concurrency2_v1/cross_slot_correlation.json
reports/gemini_concurrency2_v1/current_slot_manager_audit.json
reports/gemini_concurrency2_v1/discord_concurrency_metrics.json
reports/gemini_concurrency2_v1/failure_isolation.json
reports/gemini_concurrency2_v1/final_report.json
reports/gemini_concurrency2_v1/focused_tests.json
reports/gemini_concurrency2_v1/full_tests.json
reports/gemini_concurrency2_v1/git_preflight.json
reports/gemini_concurrency2_v1/product_head_audit.json
reports/gemini_concurrency2_v1/queue_behavior.json
reports/gemini_concurrency2_v1/queue_gate_3.json
reports/gemini_concurrency2_v1/resource_usage_c1.json
reports/gemini_concurrency2_v1/resource_usage_c2.json
reports/gemini_concurrency2_v1/restart_two_slots.json
reports/gemini_concurrency2_v1/root_policy.json
reports/gemini_concurrency2_v1/secret_scan.json
reports/gemini_concurrency2_v1/slot_assignment.json
reports/gemini_concurrency2_v1/stale_output_firewall.json
reports/gemini_concurrency2_v1/two_slot_contract.json
reports/gemini_concurrency2_v1/vps_deploy.json
reports/gemini_concurrency2_v1/vps_health.json
reports/gemini_concurrency2_v1/windows_build.json
reports/gemini_perf_root_cause_v1/benchmark_dataset.json
reports/gemini_perf_root_cause_v1/benchmark_final_comparison.json
reports/gemini_perf_root_cause_v1/browser_contention_analysis.json
reports/gemini_perf_root_cause_v1/c1_run_1.json
reports/gemini_perf_root_cause_v1/c1_run_2.json
reports/gemini_perf_root_cause_v1/c1_run_3.json
reports/gemini_perf_root_cause_v1/c1_summary.json
reports/gemini_perf_root_cause_v1/c2_run_1.json
reports/gemini_perf_root_cause_v1/c2_run_2.json
reports/gemini_perf_root_cause_v1/c2_run_3.json
reports/gemini_perf_root_cause_v1/c2_summary.json
reports/gemini_perf_root_cause_v1/chat_growth_analysis.json
reports/gemini_perf_root_cause_v1/concurrency_lock_audit.json
reports/gemini_perf_root_cause_v1/cpu_contention_analysis.json
reports/gemini_perf_root_cause_v1/current_performance_instrumentation_audit.json
reports/gemini_perf_root_cause_v1/final_report.json
reports/gemini_perf_root_cause_v1/focused_tests.json
reports/gemini_perf_root_cause_v1/full_tests.json
reports/gemini_perf_root_cause_v1/gemini_serialization_analysis.json
reports/gemini_perf_root_cause_v1/git_preflight.json
reports/gemini_perf_root_cause_v1/network_analysis.json
reports/gemini_perf_root_cause_v1/overlap_analysis.json
reports/gemini_perf_root_cause_v1/phase_contention_analysis.json
reports/gemini_perf_root_cause_v1/phase_timing_contract.json
reports/gemini_perf_root_cause_v1/process_map.json
reports/gemini_perf_root_cause_v1/product_head_audit.json
reports/gemini_perf_root_cause_v1/production_recommendation.json
reports/gemini_perf_root_cause_v1/resource_comparison.json
reports/gemini_perf_root_cause_v1/resource_sampler_contract.json
reports/gemini_perf_root_cause_v1/root_cause_conclusion.json
reports/gemini_perf_root_cause_v1/root_policy.json
reports/gemini_perf_root_cause_v1/secret_scan.json
reports/gemini_perf_root_cause_v1/vps_deploy.json
reports/gemini_perf_root_cause_v1/vps_health.json
reports/gemini_perf_root_cause_v1/warmup.json
reports/gemini_perf_root_cause_v1/windows_build.json
reports/gemini_residual_recovery_v1/build_manifest.json
reports/gemini_residual_recovery_v1/capability_audit.json
reports/gemini_residual_recovery_v1/final_report.json
reports/gemini_residual_recovery_v1/focused_tests.json
reports/gemini_residual_recovery_v1/full_tests.json
reports/gemini_residual_recovery_v1/git_preflight.json
reports/gemini_residual_recovery_v1/historical_implementation_audit.json
reports/gemini_residual_recovery_v1/p003_regression.json
reports/gemini_residual_recovery_v1/page_count_mismatch.json
reports/gemini_residual_recovery_v1/residual_validator_contract.json
reports/gemini_residual_recovery_v1/root_policy.json
reports/gemini_residual_recovery_v1/secret_scan.json
reports/gemini_residual_recovery_v1/translation_fallback_contract.json
reports/gemini_residual_recovery_v1/vps_health.json
reports/gemini_v2_integration/batch10_offline_regression.json
reports/gemini_v2_integration/branch_ancestry.json
reports/gemini_v2_integration/build_smoke.json
reports/gemini_v2_integration/capability_inventory.json
reports/gemini_v2_integration/completed_case_reviews.json
reports/gemini_v2_integration/desktop_smoke.json
reports/gemini_v2_integration/final_report.json
reports/gemini_v2_integration/frontend_validation.json
reports/gemini_v2_integration/gemini_commit_inventory.json
reports/gemini_v2_integration/git_preflight.json
reports/gemini_v2_integration/live_vps_smoke.json
reports/gemini_v2_integration/mask_v2_regression.json
reports/gemini_v2_integration/old_to_new_module_map.json
reports/gemini_v2_integration/port_plan.json
reports/gemini_v2_integration/ported_capabilities.json
reports/gemini_v2_integration/quality_metadata_contract.json
reports/gemini_v2_integration/root_policy_check.json
reports/gemini_v2_integration/secret_scan.json
reports/gemini_v2_integration/tests_focused.json
reports/gemini_v2_integration/tests_full.json
reports/gemini_v2_integration/training_candidate_evaluation.json
reports/gemini_v2_integration/training_candidate_packages.json
reports/gemini_v2_integration/worker_contract_version.json
reports/history_final_polish_v1/auth_startup_audit.json
reports/history_final_polish_v1/bottom_scroll_root_cause.json
reports/history_final_polish_v1/final_report.json
reports/history_final_polish_v1/git_preflight.json
reports/history_scroll_delete_v1/codex_final_report.json
reports/history_scroll_delete_v1/codex_runtime_diagnostic_import.json
reports/history_scroll_delete_v1/codex_takeover_preflight.json
reports/history_scroll_delete_v1/delete_fixture_reproduction.json
reports/history_scroll_delete_v1/delete_root_cause.json
reports/history_scroll_delete_v1/problem_case_comparison.json
reports/history_scroll_delete_v1/review_generation_layout.json
reports/history_scroll_delete_v1/second_scroll_root_cause.json
reports/history_selection_ux_v2/final_report.json
reports/history_selection_ux_v2/scroll_regression_root_cause.json
reports/history_selection_ux_v2/toolbar_before_after.json
reports/history_selection_ux_v2/wip_import_provenance.json
reports/inpaint_activation_20261108.md
reports/inpaint_followup_20261108.md
reports/job_457d265b_runtime_20261108.md
reports/kaggle_qwen_fallback_lab_dry_run.json
reports/main_candidate_comix_ui_v1/branch_inventory.json
reports/main_candidate_comix_ui_v1/build.json
reports/main_candidate_comix_ui_v1/capability_matrix.json
reports/main_candidate_comix_ui_v1/capability_provenance.json
reports/main_candidate_comix_ui_v1/final_report.json
reports/main_candidate_comix_ui_v1/focused_tests.json
reports/main_candidate_comix_ui_v1/full_tests.json
reports/main_candidate_comix_ui_v1/git_preflight.json
reports/main_candidate_comix_ui_v1/overlap_and_conflicts.json
reports/main_candidate_comix_ui_v1/root_policy.json
reports/main_candidate_comix_ui_v1/security.json
reports/main_candidate_comix_ui_v1/source_validation.json
reports/output_modes_v1/artifact_and_contract_matrix.json
reports/output_modes_v1/clean_typeset_decoupling_audit.json
reports/output_modes_v1/current_capability_audit.json
reports/output_modes_v1/execution_matrix.json
reports/output_modes_v1/final_decoupling_report.json
reports/output_modes_v1/implementation_report.json
reports/output_modes_v1/tests_and_security.json
reports/output_modes_v1/translate_only/completion_and_yk_matrix.json
reports/output_modes_v1/translate_only/final_report.json
reports/output_modes_v1/translate_only/translate_only_audit.json
reports/output_ui_v1/current_ui_audit.json
reports/output_ui_v1/final_report.json
reports/output_ui_v1/git_preflight.json
reports/output_ui_v1/physical_ui_validation.json
reports/output_ui_v1/preset_progress_finish_matrix.json
reports/output_ui_v1/screenshot_evidence_manifest.json
reports/output_ui_v2/artifact_exposure_and_naming.json
reports/output_ui_v2/final_report.json
reports/output_ui_v2/git_preflight.json
reports/output_ui_v2/physical_ui_validation.json
reports/output_ui_v2/ux_hierarchy_and_copy.json
reports/outputplan_execution_ops_v1/authorization_contract.json
reports/outputplan_execution_ops_v1/build_and_smoke.json
reports/outputplan_execution_ops_v1/old_job_evidence.json
reports/outputplan_execution_ops_v1/stale_source_analysis_duplicate_recovery.json
reports/outputplan_execution_ops_v1/test_evidence.json
reports/outputplan_final_artifact_validation_v1/artifact_authority_contract.json
reports/outputplan_final_artifact_validation_v1/build_validation.json
reports/outputplan_final_artifact_validation_v1/clean_only_regression.json
reports/outputplan_final_artifact_validation_v1/final_report.json
reports/outputplan_final_artifact_validation_v1/focused_tests.json
reports/outputplan_final_artifact_validation_v1/full_tests.json
reports/outputplan_final_artifact_validation_v1/git_preflight.json
reports/outputplan_final_artifact_validation_v1/legacy_full_usage_audit.json
reports/outputplan_final_artifact_validation_v1/legacy_job_compatibility.json
reports/outputplan_final_artifact_validation_v1/missing_clean_negative_test.json
reports/outputplan_final_artifact_validation_v1/preset_artifact_matrix.json
reports/outputplan_final_artifact_validation_v1/real_job_readonly_evidence.json
reports/outputplan_final_artifact_validation_v1/root_cause.json
reports/outputplan_gemini_integration_v1/artifact_matrix.json
reports/outputplan_gemini_integration_v1/automatic_regression.json
reports/outputplan_gemini_integration_v1/build_smoke.json
reports/outputplan_gemini_integration_v1/chat_reuse_policy.json
reports/outputplan_gemini_integration_v1/clean_only_regression.json
reports/outputplan_gemini_integration_v1/clean_orchestrator_contract.json
reports/outputplan_gemini_integration_v1/cross_job_tests.json
reports/outputplan_gemini_integration_v1/desktop_smoke.json
reports/outputplan_gemini_integration_v1/failure_mode_tests.json
reports/outputplan_gemini_integration_v1/fallback_trigger_policy.json
reports/outputplan_gemini_integration_v1/final_report.json
reports/outputplan_gemini_integration_v1/frontend_validation.json
reports/outputplan_gemini_integration_v1/full_tests.json
reports/outputplan_gemini_integration_v1/gemini_fallback_tests.json
reports/outputplan_gemini_integration_v1/gemini_v2_preservation.json
reports/outputplan_gemini_integration_v1/git_preflight.json
reports/outputplan_gemini_integration_v1/integration_plan.json
reports/outputplan_gemini_integration_v1/large_file_scan.json
reports/outputplan_gemini_integration_v1/live_vps_smoke.json
reports/outputplan_gemini_integration_v1/local_clean_status_map.json
reports/outputplan_gemini_integration_v1/local_success_tests.json
reports/outputplan_gemini_integration_v1/outputplan_clean_matrix.json
reports/outputplan_gemini_integration_v1/outputplan_preservation.json
reports/outputplan_gemini_integration_v1/overlap_analysis.json
reports/outputplan_gemini_integration_v1/professional_regression.json
reports/outputplan_gemini_integration_v1/provider_yk_matrix.json
reports/outputplan_gemini_integration_v1/root_policy.json
reports/outputplan_gemini_integration_v1/secret_scan.json
reports/outputplan_gemini_integration_v1/sfx_firewall_tests.json
reports/outputplan_gemini_integration_v1/source_a_commit_inventory.json
reports/outputplan_gemini_integration_v1/source_b_commit_inventory.json
reports/outputplan_gemini_integration_v1/training_candidate_regression.json
reports/outputplan_gemini_integration_v1/translate_clean_regression.json
reports/outputplan_gemini_integration_v1/translate_only_regression.json
reports/packaged_ui_stale_asset_v1/backend_http_ui_probe.json
reports/packaged_ui_stale_asset_v1/build_source_provenance.json
reports/packaged_ui_stale_asset_v1/final_report.json
reports/packaged_ui_stale_asset_v1/fix.json
reports/packaged_ui_stale_asset_v1/owner_review_state.json
reports/packaged_ui_stale_asset_v1/packaged_asset_fingerprints.json
reports/packaged_ui_stale_asset_v1/port_8080_ownership.json
reports/packaged_ui_stale_asset_v1/preflight.json
reports/packaged_ui_stale_asset_v1/process_map_before.json
reports/packaged_ui_stale_asset_v1/rebuild.json
reports/packaged_ui_stale_asset_v1/root_cause.json
reports/packaged_ui_stale_asset_v1/source_asset_fingerprints.json
reports/packaged_ui_stale_asset_v1/tests.json
reports/page23_options_20261108.md
reports/plan_prep_20261110.md
reports/repository_reorganization_v1/entrypoint_smoke.json
reports/repository_reorganization_v1/existing_changes_classification.json
reports/repository_reorganization_v1/external_artifact_manifest.json
reports/repository_reorganization_v1/final_report.json
reports/repository_reorganization_v1/git_preflight.json
reports/repository_reorganization_v1/gitattributes_audit.json
reports/repository_reorganization_v1/gitignore_audit.json
reports/repository_reorganization_v1/large_file_scan.json
reports/repository_reorganization_v1/link_check.json
reports/repository_reorganization_v1/move_plan.json
reports/repository_reorganization_v1/moves_executed.json
reports/repository_reorganization_v1/packaging_smoke.json
reports/repository_reorganization_v1/reference_fix_report.json
reports/repository_reorganization_v1/reference_map_after.json
reports/repository_reorganization_v1/reference_map_before.json
reports/repository_reorganization_v1/repository_tree_after.txt
reports/repository_reorganization_v1/repository_tree_before.txt
reports/repository_reorganization_v1/root_files_after.json
reports/repository_reorganization_v1/root_files_before.json
reports/repository_reorganization_v1/root_inventory.json
reports/repository_reorganization_v1/secret_scan.json
reports/repository_reorganization_v1/test_delta.json
reports/repository_reorganization_v1/tests_after.json
reports/repository_reorganization_v1/tests_before.json
reports/repository_reorganization_v1/uncommitted_artifact_policy.json
reports/repository_reorganization_v2/collection.json
reports/repository_reorganization_v2/commits_created.json
reports/repository_reorganization_v2/compatibility_shims.json
reports/repository_reorganization_v2/desktop_smoke.json
reports/repository_reorganization_v2/final_git_status.json
reports/repository_reorganization_v2/final_report.json
reports/repository_reorganization_v2/frontend_tests.json
reports/repository_reorganization_v2/git_preflight.json
reports/repository_reorganization_v2/historical_failures_recheck.json
reports/repository_reorganization_v2/import_fixes.json
reports/repository_reorganization_v2/large_file_scan.json
reports/repository_reorganization_v2/move_plan.json
reports/repository_reorganization_v2/moves_executed.json
reports/repository_reorganization_v2/package_design.json
reports/repository_reorganization_v2/packaging_changes.json
reports/repository_reorganization_v2/pyinstaller_build.json
reports/repository_reorganization_v2/python_module_dependency_map.json
reports/repository_reorganization_v2/repository_tree_after.txt
reports/repository_reorganization_v2/repository_tree_before.txt
reports/repository_reorganization_v2/resource_path_fixes.json
reports/repository_reorganization_v2/root_allowlist.json
reports/repository_reorganization_v2/root_files_after.json
reports/repository_reorganization_v2/root_files_before.json
reports/repository_reorganization_v2/root_inventory_before.json
reports/repository_reorganization_v2/root_policy.json
reports/repository_reorganization_v2/secret_scan.json
reports/repository_reorganization_v2/test_delta.json
reports/repository_reorganization_v2/tests_after.json
reports/repository_reorganization_v2/tests_before.json
reports/same_source_submission_v1/build_and_validation.json
reports/same_source_submission_v1/owner_retest_contract.json
reports/same_source_submission_v1/root_cause.json
reports/same_source_submission_v1/test_evidence.json
reports/sfx_terms_metrics_ep285_v1/METRICS.md
reports/translated_chapters_ui_v1/final_report.json
reports/translated_chapters_ui_v1/fix_and_state_contract.json
reports/translated_chapters_ui_v1/git_preflight.json
reports/translated_chapters_ui_v1/scroll_root_cause.json
yomu/__init__.py
yomu/auth/__init__.py
yomu/clean/__init__.py
yomu/clean/inpainting/__init__.py
yomu/clean/ownership/__init__.py
yomu/clean/reconstruction/__init__.py
yomu/commands/__init__.py
yomu/community/__init__.py
yomu/community/legacy/__init__.py
yomu/community/storage/__init__.py
yomu/config/__init__.py
yomu/core/__init__.py
yomu/desktop/__init__.py
yomu/download/__init__.py
yomu/download/local/__init__.py
yomu/download/readers/__init__.py
yomu/download/sources/__init__.py
yomu/export/__init__.py
yomu/ocr/__init__.py
yomu/pipeline/__init__.py
yomu/review/__init__.py
yomu/review/workflows/__init__.py
yomu/runtime/__init__.py
yomu/security/__init__.py
yomu/translation/__init__.py
yomu/translation/providers/__init__.py
yomu/ui/__init__.py
```
