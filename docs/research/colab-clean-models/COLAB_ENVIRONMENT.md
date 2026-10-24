# Colab runtime evidence

Status: **HISTORICAL T4 INFERENCE VERIFIED; CURRENT RUNTIME NOT VERIFIED**.

The connected Google Drive connector allowed read-only inspection of the saved notebook `Yomu_Big_LaMa_Colab_Benchmark_V4`. Its saved cell output records a Tesla T4 inference. This proves the historical run, not that its runtime is still alive now. The owner asked to leave the runtime connected; it has not been disconnected. No Colab runtime-control MCP exists in this session, and no browser/computer control was used.

| Field | Current evidence |
|---|---|
| Notebook visible in browser context | `https://colab.research.google.com/drive/1C_vcvYY_IXsgtSN8zopnSkqPYiKKaLdE` (context only) |
| Runtime connected now | NOT_VERIFIED; leave connected as requested |
| GPU / VRAM | Historical run: Tesla T4, 15,637,086,208 total VRAM bytes; free VRAM not captured |
| System RAM / free storage | NOT_CAPTURED |
| CUDA / PyTorch / Python | Historical run: PyTorch 2.11.0+cu130, Python 3.13.15; CUDA runtime/driver version not separately captured |
| Colab compute-unit balance / paid status | NOT_AVAILABLE; no account inspection performed |
| Historical model inference in saved notebook | YES: one completed Big-LaMa inference; the earlier cell execution failed at parse time with `IndentationError` before inference |
| New Colab inference started in this continuation | NO; one separate local CPU synthetic inference was run in an earlier continuation |
| Colab runner prepared | YES; one-image, non-holdout, hash-verified; not run |
| Runner check on this Windows host | Fail-closed as expected: `CUDA_GPU_NOT_AVAILABLE`; no checkpoint was loaded and no output directory was created |
| Local accelerator | AMD Radeon RX 6600 detected; CUDA unavailable and `torch-directml` absent; local model smoke used CPU |
| Paid-resource state for historical run | NOT_CAPTURED |

To close this evidence gate without computer-control automation, the owner can run the notebook's environment-inspection cell and share the output fields only (GPU model/total-free VRAM, RAM, disk free, Python, PyTorch, CUDA, runtime state, and a confirmation that no paid upgrade/resource was enabled). Do not share cookies, tokens, account identifiers, or billing screenshots containing personal details.
