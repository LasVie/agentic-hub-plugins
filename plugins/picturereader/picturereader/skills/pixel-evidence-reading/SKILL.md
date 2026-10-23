---
name: pixel-evidence-reading
description: Read local raster images methodically using deterministic scan grids, structure measurements, exact pixel samples, palettes, and region crops. Use when a text-only model needs auditable local image evidence without external vision calls.
---

# Pixel Evidence Reading

1. Call `image_scan` on the whole image first. Treat grids as coarse measurements, not semantic recognition.
2. Use dimensions, dominant colors, brightness, edge energy, and symmetry to form limited layout hypotheses. Clearly label hypotheses.
3. If a small or ambiguous feature matters, call `image_crop` on explicit coordinates and scan the exported region at higher density.
4. Use `image_sample` to verify exact colors or boundaries at named coordinates. Use a radius only when local averaging is appropriate.
5. Use `image_palette` for measured color proportions. Do not infer branding, objects, or text from color alone.
6. For text, object identity, or scene semantics, state that pixel evidence is insufficient and combine it with a dedicated OCR or multimodal asset.
7. Cite image path, region, grid dimensions, and sampled coordinates in the conclusion so another run can reproduce the evidence.
