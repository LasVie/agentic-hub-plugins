"""Native local pixel-to-text evidence tools for WorkSwarm/OpenJiuwen."""
from __future__ import annotations

import math
from pathlib import Path
from typing import Any, AsyncIterator, Dict, Iterable, List, Tuple

from PIL import Image, ImageOps, UnidentifiedImageError
from openjiuwen.core.foundation.tool import Tool, ToolCard

MAX_BYTES = 50 * 1024 * 1024
MAX_PIXELS = 100_000_000
LUMA_CHARS = " .:-=+*#%@"
COLOR_CODES = {
    "K": (0, 0, 0), "W": (255, 255, 255), "R": (220, 45, 45),
    "O": (235, 135, 35), "Y": (230, 215, 50), "G": (45, 175, 75),
    "C": (45, 190, 200), "B": (55, 95, 210), "P": (150, 70, 190),
    "M": (210, 65, 145), "N": (135, 95, 60), "S": (128, 128, 128),
}


def _error(code: str, message: str) -> Dict[str, Any]:
    return {"ok": False, "error": {"code": code, "message": message}}


def _load(path_value: Any) -> Tuple[Image.Image, Path]:
    if not isinstance(path_value, str) or not path_value.strip():
        raise ValueError("file_path is required")
    path = Path(path_value).expanduser().resolve()
    if not path.is_file():
        raise FileNotFoundError(f"image not found: {path}")
    if path.stat().st_size > MAX_BYTES:
        raise ValueError(f"image exceeds {MAX_BYTES} byte limit")
    try:
        with Image.open(path) as src:
            if src.width * src.height > MAX_PIXELS:
                raise ValueError(f"image exceeds {MAX_PIXELS} pixel limit")
            src.seek(0)
            return ImageOps.exif_transpose(src).convert("RGB").copy(), path
    except (UnidentifiedImageError, OSError) as exc:
        raise ValueError(f"unsupported or corrupt image: {exc}") from exc


def _region(image: Image.Image, value: Any) -> Tuple[Image.Image, Dict[str, int]]:
    if value in (None, {}):
        return image, {"x": 0, "y": 0, "width": image.width, "height": image.height}
    if not isinstance(value, dict):
        raise ValueError("region must be an object with x, y, width, height")
    try:
        x, y, w, h = (int(value[k]) for k in ("x", "y", "width", "height"))
    except (KeyError, TypeError, ValueError) as exc:
        raise ValueError("region requires integer x, y, width, height") from exc
    if x < 0 or y < 0 or w <= 0 or h <= 0 or x + w > image.width or y + h > image.height:
        raise ValueError(f"region outside image bounds {image.width}x{image.height}")
    return image.crop((x, y, x + w, y + h)), {"x": x, "y": y, "width": w, "height": h}


def _luma(rgb: Tuple[int, int, int]) -> float:
    r, g, b = rgb
    return 0.2126 * r + 0.7152 * g + 0.0722 * b


def _nearest_code(rgb: Tuple[int, int, int]) -> str:
    return min(COLOR_CODES, key=lambda k: sum((rgb[i] - COLOR_CODES[k][i]) ** 2 for i in range(3)))


def _grid(image: Image.Image, width: int) -> Tuple[List[List[Tuple[int, int, int]]], int, int]:
    width = max(4, min(64, width))
    height = max(2, min(48, round(width * image.height / max(1, image.width) * 0.5)))
    small = image.resize((width, height), Image.Resampling.BOX)
    rows = [[small.getpixel((x, y)) for x in range(width)] for y in range(height)]
    return rows, width, height


def _palette(image: Image.Image, count: int) -> List[Dict[str, Any]]:
    count = max(2, min(12, count))
    thumb = image.copy()
    thumb.thumbnail((256, 256), Image.Resampling.LANCZOS)
    quant = thumb.quantize(colors=count, method=Image.Quantize.MEDIANCUT)
    colors = sorted(quant.getcolors() or [], reverse=True)
    pal = quant.getpalette() or []
    total = max(1, sum(n for n, _ in colors))
    out = []
    for n, idx in colors:
        rgb = tuple(pal[idx * 3:idx * 3 + 3])
        out.append({"rgb": list(rgb), "hex": "#%02X%02X%02X" % rgb, "share": round(n / total, 4)})
    return out


def _structure(rows: List[List[Tuple[int, int, int]]]) -> Dict[str, float]:
    h, w = len(rows), len(rows[0])
    horizontal, vertical = [], []
    for y in range(h):
        for x in range(w - 1):
            horizontal.append(abs(_luma(rows[y][x]) - _luma(rows[y][x + 1])))
    for y in range(h - 1):
        for x in range(w):
            vertical.append(abs(_luma(rows[y][x]) - _luma(rows[y + 1][x])))
    sym = []
    for y in range(h):
        for x in range(w // 2):
            a, b = rows[y][x], rows[y][w - 1 - x]
            sym.append(sum(abs(a[i] - b[i]) for i in range(3)) / 3)
    mean_h = sum(horizontal) / max(1, len(horizontal))
    mean_v = sum(vertical) / max(1, len(vertical))
    return {
        "horizontal_edge_energy": round(mean_h / 255, 4),
        "vertical_edge_energy": round(mean_v / 255, 4),
        "edge_energy": round((mean_h + mean_v) / 510, 4),
        "left_right_symmetry": round(1 - (sum(sym) / max(1, len(sym))) / 255, 4),
    }


def _invoke_error(exc: Exception) -> Dict[str, Any]:
    if isinstance(exc, FileNotFoundError):
        return _error("NOT_FOUND", str(exc))
    return _error("INVALID_IMAGE", str(exc))


class ImageScanTool(Tool):
    def __init__(self) -> None:
        super().__init__(ToolCard(id="image_scan", name="image_scan", description="Convert a local image or region into bounded pixel grids and measured structure evidence.", input_params={"type": "object", "properties": {"file_path": {"type": "string"}, "grid_width": {"type": "integer", "default": 24}, "palette_count": {"type": "integer", "default": 6}, "region": {"type": "object", "properties": {"x": {"type": "integer"}, "y": {"type": "integer"}, "width": {"type": "integer"}, "height": {"type": "integer"}}}}, "required": ["file_path"]}, parallel_safe=True))

    async def invoke(self, inputs: Dict[str, Any], **kwargs: Any) -> Dict[str, Any]:
        try:
            image, path = _load(inputs.get("file_path"))
            view, region = _region(image, inputs.get("region"))
            rows, gw, gh = _grid(view, int(inputs.get("grid_width", 24)))
            lumas = [_luma(px) for row in rows for px in row]
            return {"ok": True, "file_path": str(path), "image": {"width": image.width, "height": image.height}, "region": region, "grid": {"width": gw, "height": gh, "luminance": ["".join(LUMA_CHARS[min(len(LUMA_CHARS)-1, int(_luma(px) / 256 * len(LUMA_CHARS)))] for px in row) for row in rows], "colors": ["".join(_nearest_code(px) for px in row) for row in rows], "legend": {k: "#%02X%02X%02X" % v for k, v in COLOR_CODES.items()}}, "measurements": {"mean_luminance": round(sum(lumas) / len(lumas), 2), **_structure(rows)}, "palette": _palette(view, int(inputs.get("palette_count", 6)))}
        except (ValueError, FileNotFoundError) as exc:
            return _invoke_error(exc)

    async def stream(self, inputs: Dict[str, Any], **kwargs: Any) -> AsyncIterator[Dict[str, Any]]:
        yield await self.invoke(inputs, **kwargs)


class ImageSampleTool(Tool):
    def __init__(self) -> None:
        super().__init__(ToolCard(id="image_sample", name="image_sample", description="Return exact or locally averaged RGB/HEX/luminance values at image coordinates.", input_params={"type": "object", "properties": {"file_path": {"type": "string"}, "points": {"type": "array", "items": {"type": "object", "properties": {"x": {"type": "integer"}, "y": {"type": "integer"}}, "required": ["x", "y"]}, "minItems": 1, "maxItems": 64}, "radius": {"type": "integer", "default": 0}}, "required": ["file_path", "points"]}, parallel_safe=True))

    async def invoke(self, inputs: Dict[str, Any], **kwargs: Any) -> Dict[str, Any]:
        try:
            image, path = _load(inputs.get("file_path"))
            points = inputs.get("points")
            if not isinstance(points, list) or not 1 <= len(points) <= 64:
                raise ValueError("points must contain 1 to 64 coordinate objects")
            radius = int(inputs.get("radius", 0))
            if not 0 <= radius <= 32:
                raise ValueError("radius must be between 0 and 32")
            samples = []
            for point in points:
                x, y = int(point["x"]), int(point["y"])
                if not (0 <= x < image.width and 0 <= y < image.height):
                    raise ValueError(f"point ({x},{y}) outside image bounds {image.width}x{image.height}")
                box = (max(0, x-radius), max(0, y-radius), min(image.width, x+radius+1), min(image.height, y+radius+1))
                crop = image.crop(box)
                pixels = list(crop.getdata())
                rgb = tuple(round(sum(p[i] for p in pixels) / len(pixels)) for i in range(3))
                samples.append({"x": x, "y": y, "radius": radius, "rgb": list(rgb), "hex": "#%02X%02X%02X" % rgb, "luminance": round(_luma(rgb), 2)})
            return {"ok": True, "file_path": str(path), "image": {"width": image.width, "height": image.height}, "samples": samples}
        except (ValueError, FileNotFoundError, KeyError, TypeError) as exc:
            return _invoke_error(ValueError(str(exc)) if not isinstance(exc, FileNotFoundError) else exc)

    async def stream(self, inputs: Dict[str, Any], **kwargs: Any) -> AsyncIterator[Dict[str, Any]]:
        yield await self.invoke(inputs, **kwargs)


class ImagePaletteTool(Tool):
    def __init__(self) -> None:
        super().__init__(ToolCard(id="image_palette", name="image_palette", description="Measure dominant local image colors and proportions.", input_params={"type": "object", "properties": {"file_path": {"type": "string"}, "count": {"type": "integer", "default": 6}, "region": {"type": "object"}}, "required": ["file_path"]}, parallel_safe=True))

    async def invoke(self, inputs: Dict[str, Any], **kwargs: Any) -> Dict[str, Any]:
        try:
            image, path = _load(inputs.get("file_path"))
            view, region = _region(image, inputs.get("region"))
            return {"ok": True, "file_path": str(path), "region": region, "palette": _palette(view, int(inputs.get("count", 6)))}
        except (ValueError, FileNotFoundError) as exc:
            return _invoke_error(exc)

    async def stream(self, inputs: Dict[str, Any], **kwargs: Any) -> AsyncIterator[Dict[str, Any]]:
        yield await self.invoke(inputs, **kwargs)


class ImageCropTool(Tool):
    def __init__(self) -> None:
        super().__init__(ToolCard(id="image_crop", name="image_crop", description="Export an explicit source-image region as PNG without modifying the source.", input_params={"type": "object", "properties": {"file_path": {"type": "string"}, "region": {"type": "object"}, "output_path": {"type": "string"}, "overwrite": {"type": "boolean", "default": False}}, "required": ["file_path", "region", "output_path"]}, parallel_safe=False))

    async def invoke(self, inputs: Dict[str, Any], **kwargs: Any) -> Dict[str, Any]:
        try:
            image, path = _load(inputs.get("file_path"))
            crop, region = _region(image, inputs.get("region"))
            output_value = inputs.get("output_path")
            if not isinstance(output_value, str) or not output_value.strip():
                raise ValueError("output_path is required")
            output = Path(output_value).expanduser().resolve()
            if output.suffix.lower() != ".png":
                raise ValueError("output_path must end in .png")
            if output == path:
                raise ValueError("output_path must not overwrite the source image")
            if output.exists() and not bool(inputs.get("overwrite", False)):
                return _error("OUTPUT_EXISTS", f"output already exists: {output}")
            output.parent.mkdir(parents=True, exist_ok=True)
            crop.save(output, format="PNG", optimize=True)
            return {"ok": True, "source_path": str(path), "output_path": str(output), "region": region, "width": crop.width, "height": crop.height, "bytes": output.stat().st_size}
        except (ValueError, FileNotFoundError, OSError) as exc:
            return _invoke_error(exc)

    async def stream(self, inputs: Dict[str, Any], **kwargs: Any) -> AsyncIterator[Dict[str, Any]]:
        yield await self.invoke(inputs, **kwargs)
