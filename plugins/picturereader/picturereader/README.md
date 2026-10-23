# Pixel Evidence Reader

An offline WorkSwarm/OpenJiuwen Plugin for turning local raster images into deterministic evidence a text-only model can inspect.

Tools:

- `image_scan`: luminance and color grids, dominant colors, brightness, edge energy, and approximate symmetry; accepts an optional `{x,y,width,height}` region.
- `image_sample`: exact RGB/HEX/luminance samples at selected coordinates, optionally averaged over a radius.
- `image_palette`: dominant measured colors with proportions.
- `image_crop`: non-destructively export an explicit region as PNG for rescan.

The Plugin never makes network calls and never modifies the source image. It requires OpenJiuwen and Pillow in the host environment. Supported formats follow the installed Pillow build (normally PNG, JPEG, WebP, BMP, and GIF first frame).

This scope intentionally excludes OCR, semantic image Q&A, external vision APIs, DSH model-adapter interception, web settings, and document conversion. Use an existing OCR or multimodal asset when those capabilities are required.
