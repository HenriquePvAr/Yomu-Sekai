# Google Colab feasibility for Yomu inpainting

Status: desk research only; no Google login, Colab assignment, GPU runtime, or paid resource was opened in this task.

## Decision summary

- A Google AI/Google One “Pro” badge is not enough evidence of a specific Colab entitlement. Eligible paid Google AI plans can include a monthly Colab compute-unit allocation and premium hardware, but the exact benefit depends on the plan, region, and account. Verify it in the signed-in Colab account under **Settings → Subscription**; do not buy or upgrade anything for this research.
- Colab does not guarantee a GPU type, GPU memory, runtime lifetime, or fixed quotas. Google says availability and limits fluctuate and are not published as fixed guarantees. An 80 GB A100/H100 therefore cannot be promised from the plan name or catalog.
- Colab is suitable for interactive, bounded experiments. A notebook runtime is ephemeral and may disconnect; it is not a dependable always-on Yomu production worker. Use a durable GPU VM/service for production if a measured need justifies its cost and operations.
- No GPU, time, VRAM, compute units, or pages/minute were measured here. The benchmark report deliberately records `NOT_RUN` rather than extrapolating.

## Account and accelerator gate

**Not verified:** account identity/plan, subscription benefit, remaining compute units, selectable accelerators, live GPU allocation, system RAM, and GPU VRAM. These are private account/runtime facts not exposed by the repository or public documentation. Owner action to close the gate: in Colab, open Settings → Subscription and report the displayed plan and unit balance; then, only if the owner wants a one-image smoke, start the notebook with GPU selected and record its `nvidia-smi` output. Do not send screenshots containing account identifiers.

The notebook records GPU model, total/free VRAM, CUDA/PyTorch versions, host RAM, image dimensions, checkpoint identifier/revision/hash, load/inference wall times, peak allocated/reserved VRAM, and the owner-entered compute-unit delta. If unit consumption cannot be read, stop after one image and request approval before another run. Hard cap: 5 units for any later, explicitly approved experimental sequence; no upgrades or purchases.

An 80 GB card may enable loading a larger model or larger batch without offload. That is a capacity argument, not evidence of higher image quality or faster single-image latency. For Yomu’s localized masks, weight loading, crop size, denoising steps, kernel support, and data transfer may dominate. Compare on the same image/mask and count end-to-end time before any chapter extrapolation.

## Official Google Colab MCP

The user-supplied repository is the official Google-owned [`googlecolab/colab-mcp`](https://github.com/googlecolab/colab-mcp). Its README says clients must support `notifications/tools/list_changed` and names Gemini CLI, Claude Code, and Windsurf as clients meeting that requirement; Codex is not listed. The current task has no Colab MCP tools available, no server is configured, and no OAuth was started. Therefore compatibility with this installed Codex host is **unproven**, not “connected”.

Static review only: the official implementation starts a local stdio MCP server, launches a browser connection to Colab, and proxies notebook tools through a local WebSocket. Notebook-side Python execution is powerful and can consume the signed-in account’s quota; any eventual integration must be local/trusted, human-authorized, and scoped to synthetic or explicitly cleared data. The official server was not installed or run.

An unofficial fork advertises Codex support and OAuth/runtime controls, but it was not installed and has not passed a source/dependency/security review in this task. Do not run its installer as a shortcut. If the official MCP remains incompatible, use the interactive notebook manually or review the fork’s pinned source, permissions, OAuth scopes, dependency lock, and runtime-selection behavior before considering it.

## Policy and data handling

- Use a notebook as an interactive research session, not a persistent service, remote desktop, SSH proxy, or unattended distributed worker. Follow the live Colab terms for the account and plan.
- Do not upload Yomu source pages, chapter archives, masks derived from private/customer material, local project files, secrets, cookies, or credentials. This notebook creates a synthetic comic-like fixture in memory and writes only under its runtime-local `/content/yomu_colab_inpainting` folder.
- Do not mount Drive by default. Runtime files are ephemeral; export only explicitly approved experiment outputs after reviewing them.
- Stop the runtime after a smoke. Colab may terminate/disconnect sessions and does not provide durable worker semantics.

## Alternatives for operational inference

1. Keep the existing local CPU/local GPU and fail-closed review path until a benchmark demonstrates an operational bottleneck.
2. For sustained production GPU work, evaluate a dedicated VM or managed GPU service with explicit price, region, capacity, queue, data-retention, access-control, and teardown policy. Google specifically points users to GCP Marketplace/Colab Enterprise or their own runtime for more guaranteed resources; the actual bill must be checked before provisioning.
3. Do not turn an interactive Colab session into the Yomu remote provider. A production adapter needs durable queue semantics, authenticated transport, idempotent requests, bounded retries, cancellation, health/readiness, observability, and deterministic safe compositing.

## Sources

- [Google Colab FAQ](https://research.google.com/colaboratory/faq.html) and [Portuguese FAQ](https://research.google.com/colaboratory/intl/pt-BR/faq.html): dynamic resource availability, paid-plan benefits, usage limits, runtime duration, and restrictions.
- [Official Colab MCP README](https://github.com/googlecolab/colab-mcp): supported-client requirement and setup.
- [Colab MCP official source](https://github.com/googlecolab/colab-mcp/tree/main/src/colab_mcp): static source reviewed; not executed.
