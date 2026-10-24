# Candidate shortlist for manga / webtoon clean reconstruction

This is a research shortlist, not a ranking or production approval. Exact model, code, base-model, and checkpoint terms must be checked independently; a repository's code license does not automatically license its weights or training data.

| Candidate | Mask contract | License / commercial gate | T4 suitability | Why test / main risk | Priority |
|---|---|---|---|---|---|
| Anime-Manga Big-LaMa (existing Yomu TorchScript descriptor) | Native binary-mask inpainting | Exact community checkpoint rights remain unresolved in Yomu; do not redistribute or recommend commercially yet | T4 page run failed visually; one separate CPU synthetic case was visually acceptable, but GPU comparison is pending | Task-specific and lightweight; black streak artifacts on SFX fixture; one easy synthetic result beat the Telea primitive only | Keep research-only; any next T4 run must use the frozen synthetic fixture and be resource-authorized; not a winner |
| MAT (Mask-Aware Transformer) | Native mask-aware inpainting | Official repository states code and models are for research purposes only; exclude from commercial integration absent separate permission | No VRAM figure published in the reviewed README; old documented stack is Python 3.7 / PyTorch 1.7.1 / CUDA 11.0; 512-multiple input constraint | Transformer-based large-hole restoration; risk of old dependencies and natural-image domain mismatch | Research-only; low priority |
| Stable Diffusion XL Inpainting | Native inpainting image + mask | OpenRAIL++ and research-use terms require review | FP16 UNet is ~5.14 GB; total T4 peak unknown. Current pinned snapshot lacks a safety-checker component/weights | No run under the existing safety gate until a separate trusted safety checker is integrated; hallucination can harm manga fidelity | Blocked pending safe checker and legal review |
| BrushNet + exact inpainting base checkpoint | Native mask-conditioned diffusion | Must clear the BrushNet code license, exact BrushNet checkpoint terms, and the separately selected SD base checkpoint terms; no commercial conclusion until all are pinned | Not measured; T4 feasibility unknown | Explicit mask control; base-model drift, safety behavior, and dependency compatibility remain risks | Research candidate only after exact artifacts and all terms are pinned |
| PowerPaint v2.1 | Official repo advertises masked inpainting/object removal; actual pinned adapter still needs validation | The v2.1 model card labels its repo Apache-2.0, but base-model and full-stack terms remain unreviewed | Snapshot metadata totals ~9.52 GB; GPU peak not measured | Pinned official app disables its safety checker and loads a `.bin` component via `torch.load`; do not run that path. A safety-preserving, audited adapter is a prerequisite | Conditional candidate only after safe adapter and complete terms review |
| FLUX.2 Klein 4B (FP8 variant) | Image editing; official model card does not establish a binary-mask inpainting API | Model card lists Apache-2.0; still verify exact selected variant and all dependencies | FP8 weights listed around 4.08 GB; actual peak VRAM/runtime not measured | Modern editing and commercial-friendly published license; not directly comparable to masked inpainting and can drift outside target | Separate exploratory edit track, not part of mask-model ranking |

## Baselines and exclusions

- **Yomu OpenCV patch synthesis/reconstruction:** mandatory same-input baseline; already integrated in the product and must not be weakened for comparison.
- **Original LaMa Big-LaMa:** useful generic baseline, but pretrained-weight rights are not clearly settled by the upstream source-code license; do not treat third-party mirrors' license labels as authoritative.
- **FLUX.1 Fill [dev]:** genuine mask-fill candidate, but its official license is non-commercial/non-production; exclude from a commercial-integration recommendation absent a separate grant.
- **Qwen-Image-Edit-2511:** published Apache-2.0 model card, but it is prompt-based image editing and its large model artifacts make it unsuitable as a first T4 binary-mask candidate. Consider only on suitable hardware and in the separate editing track.
- **ZITS/ZITS++:** potentially relevant structural/line-art inpainting, but authoritative checkpoint availability and exact weight terms must be verified before scheduling a run; do not download similarly named mirrors as substitutes.

## Proposed first fair comparison

1. Keep the Yomu baseline as the control.
2. Select no more than three mask-conditioned candidates whose exact weights, revisions, hashes, and terms are verified: Big-LaMa only if a new run is justified and not a repetition; then BrushNet or PowerPaint; then SDXL Inpainting if the safety-filter policy and T4 memory allow it.
3. Use a small synthetic manga-like fixture with a clean ground truth, one fixed mask, one fixed resolution, identical compositing, and a held-out second fixture that is never used for parameter selection.
4. One image per model initially. Record wall time, load time, RAM/VRAM peak, artifact hashes, OCR residual, boundary/line continuity, and human visual verdict. Stop if quota is unavailable or usage cannot be bounded.
5. Editing-only models get a separate crop/edit experiment and are never scored as if they consumed the same mask contract.

## Source links

- [LaMa upstream README](https://github.com/advimman/lama/blob/main/README.md) and [open issue requesting pretrained-weight license clarification](https://github.com/advimman/lama/issues/366).
- [Sanster IOPaint AnimeLaMa adapter](https://github.com/Sanster/IOPaint/blob/main/iopaint/model/lama.py) documents the Anime/Manga checkpoint endpoint and its mask input path.
- [BrushNet official repository](https://github.com/TencentARC/BrushNet) and [mask-input usage guide](https://github.com/TencentARC/BrushNet/blob/main/docs/source/en/using-diffusers/inpaint.md).
- [PowerPaint official repository](https://github.com/open-mmlab/PowerPaint), which distinguishes code repository terms from its versioned model weights.
- [PowerPaint v2.1 model card](https://huggingface.co/JunhaoZhuang/PowerPaint-v2-1) currently labels the model artifact Apache-2.0; this is not a blanket clearance for the full runtime stack.
- [MAT official repository](https://github.com/fenglinglwb/MAT) states code and models are for research purposes only and documents the older runtime/input constraints.
- [FLUX.1 Fill [dev] license](https://huggingface.co/black-forest-labs/FLUX.1-Fill-dev/blob/main/LICENSE.md).
- [FLUX.2 Klein 4B model card](https://huggingface.co/black-forest-labs/FLUX.2-klein-4B) describes image editing and its published Apache-2.0 license.
- [Qwen-Image-Edit-2511 model card](https://huggingface.co/Qwen/Qwen-Image-Edit-2511) describes the edit pipeline and Apache-2.0 license.
- [ZITS++ official repository](https://github.com/ewrfcas/ZITS-PlusPlus).
