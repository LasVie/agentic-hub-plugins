"""Real OpenJiuwen-tool integration tests for picturereader."""
from __future__ import annotations

import asyncio
import hashlib
import json
import sys
import tempfile
from pathlib import Path

from PIL import Image, ImageDraw

HERE = Path(__file__).resolve()
sys.path.insert(0, str(HERE.parents[1] / "picturereader" / "tools"))
import picture_reader  # noqa: E402


async def run() -> int:
    root = Path(tempfile.mkdtemp(prefix="picturereader-test-"))
    source = root / "fixture.png"
    image = Image.new("RGB", (120, 80), "white")
    draw = ImageDraw.Draw(image)
    draw.rectangle((0, 0, 59, 39), fill=(255, 0, 0))
    draw.rectangle((60, 0, 119, 39), fill=(0, 255, 0))
    draw.rectangle((0, 40, 59, 79), fill=(0, 0, 255))
    draw.rectangle((60, 40, 119, 79), fill=(255, 255, 255))
    draw.line((60, 0, 60, 79), fill=(0, 0, 0), width=2)
    image.save(source)
    image.save(root / "fixture.jpg", quality=95)
    image.save(root / "fixture.webp", lossless=True)

    scan_tool = picture_reader.ImageScanTool()
    sample_tool = picture_reader.ImageSampleTool()
    palette_tool = picture_reader.ImagePaletteTool()
    crop_tool = picture_reader.ImageCropTool()

    checks = []
    for fixture in (source, root / "fixture.jpg", root / "fixture.webp"):
        result = await scan_tool.invoke({"file_path": str(fixture), "grid_width": 20})
        checks.append((f"scan {fixture.suffix}", result.get("ok") and result["grid"]["width"] == 20 and len(result["grid"]["colors"]) >= 2))

    scan = await scan_tool.invoke({"file_path": str(source), "grid_width": 24, "region": {"x": 0, "y": 0, "width": 60, "height": 40}})
    checks.append(("region scan is red-dominant", scan.get("ok") and scan["palette"][0]["rgb"][0] > 240 and scan["palette"][0]["rgb"][1] < 20))
    checks.append(("structure metrics bounded", scan.get("ok") and all(0 <= scan["measurements"][k] <= 1 for k in ("edge_energy", "left_right_symmetry"))))

    sample = await sample_tool.invoke({"file_path": str(source), "points": [{"x": 10, "y": 10}, {"x": 90, "y": 10}, {"x": 10, "y": 60}, {"x": 90, "y": 60}]})
    checks.append(("exact quadrant samples", sample.get("ok") and [s["hex"] for s in sample["samples"]] == ["#FF0000", "#00FF00", "#0000FF", "#FFFFFF"]))

    palette = await palette_tool.invoke({"file_path": str(source), "count": 5})
    checks.append(("palette proportions", palette.get("ok") and abs(sum(x["share"] for x in palette["palette"]) - 1) < 0.01 and len(palette["palette"]) >= 4))

    crop_path = root / "zoom.png"
    crop = await crop_tool.invoke({"file_path": str(source), "region": {"x": 60, "y": 40, "width": 60, "height": 40}, "output_path": str(crop_path)})
    checks.append(("crop output", crop.get("ok") and crop_path.exists() and Image.open(crop_path).size == (60, 40)))
    original_hash = hashlib.sha256(source.read_bytes()).hexdigest()
    checks.append(("source unchanged", original_hash == hashlib.sha256(source.read_bytes()).hexdigest()))
    exists = await crop_tool.invoke({"file_path": str(source), "region": {"x": 0, "y": 0, "width": 10, "height": 10}, "output_path": str(crop_path)})
    checks.append(("overwrite protection", not exists.get("ok") and exists["error"]["code"] == "OUTPUT_EXISTS"))
    invalid = await sample_tool.invoke({"file_path": str(source), "points": [{"x": 999, "y": 1}]})
    checks.append(("invalid coordinate rejected", not invalid.get("ok") and invalid["error"]["code"] == "INVALID_IMAGE"))

    print(json.dumps({"fixture": str(source), "checks": checks, "scan_summary": scan, "sample_summary": sample, "crop": crop}, indent=2))
    for name, passed in checks:
        print(f"[{'PASS' if passed else 'FAIL'}] {name}")
    return 0 if all(passed for _, passed in checks) else 1


if __name__ == "__main__":
    raise SystemExit(asyncio.run(run()))
