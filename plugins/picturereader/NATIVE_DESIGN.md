# Native Design — picturereader

## Material-exposure record

Before implementation, only the CAND-DSH-177 tracker row, npm package metadata, and the upstream repository's rendered public README were used to understand the functional idea. No upstream source code, prompts, methodology/skill text, tests, icons, models, or other assets were copied, translated, or adapted. The DSH Cordis bundle, web settings interface, image-block interception, model-adapter proxy, external VLM routing, document conversion, and upstream OCR integrations are intentionally excluded.

## Independent requirement

Provide a portable WorkSwarm/OpenJiuwen Plugin that lets a text-only model inspect a local raster image through deterministic, auditable evidence:

1. `image_scan`: bounded luminance/color grids plus quantitative brightness, edge, symmetry, and dominant-color summaries; optionally scan a region.
2. `image_sample`: exact RGB/HEX/luminance values at caller-selected coordinates, with optional local averaging.
3. `image_palette`: measured dominant colors and proportions.
4. `image_crop`: export an explicitly selected region as PNG for reproducible zoom-and-rescan workflows.

All tools are local-only, read ordinary Pillow-supported raster formats, enforce input size/dimension limits, preserve source files, and return structured errors. No network client exists in the payload.
