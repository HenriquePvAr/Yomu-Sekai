# Model ranking — intentionally unranked

**Status:** `PROVISIONAL_NOT_RANKED`.

There is not enough comparable evidence to answer which model is best for simple text, complex backgrounds, manga line art, art preservation, speed, or VRAM efficiency. Two historical T4 smoke runs failed visual/safety acceptance; one separate easy synthetic CPU Big-LaMa sample was visually acceptable and scored better than a Telea primitive on that same mask. No model has broad case coverage, a GPU comparison, or an independent holdout. No winner or commercial candidate is declared.

| Requested category | Current result | Evidence required to decide |
|---|---|---|
| Best overall clean | NONE | Varied cases, accepted text removal, reconstruction fidelity, baseline comparison, holdout |
| Simple balloons / text | NONE | Same owned/synthetic source, identical mask and compositor, clean ground truth |
| Complex backgrounds / halftone | NONE | Medium/hard manga-like synthetic set with texture and line continuity review |
| Line-art reconstruction / art preservation | NONE | Protected-art masks, boundary metrics, native-size human review, multiple cases |
| Speed / VRAM efficiency | NONE | Same GPU, resolution, warm/cold timing protocol, peak allocated/reserved memory |
| Commercial candidate | NONE APPROVED | Exact code/weights/base/dependency rights and security review; see `MODEL_LICENSE_MATRIX.md` |
| Yomu integration | NO MODEL APPROVED | Above evidence plus explicit interface, failure/review, provenance, and product gates |

The next GPU experiment cannot yet be run safely: this Codex host has no Colab execution MCP and the current runtime/resource state is unverified. PowerPaint v2.1's model card labels its model repo Apache-2.0 and advertises inpainting/object removal, but the pinned upstream app disables the safety checker and uses `torch.load` on a `.bin` file. SDXL Inpainting has safetensors and a pinned revision, but the current checkpoint snapshot contains no safety checker. Do not bypass either gap. Do not repeat the private Big-LaMa page or SD 1.5 smoke; if runtime and artifact gates clear, compare the exact saved synthetic fixture across CPU/T4 first.

For ambiguous ownership, text intertwined with character/line art, or cases without enough source evidence, the correct system outcome remains `REVIEW_REQUIRED`, not forced reconstruction.
