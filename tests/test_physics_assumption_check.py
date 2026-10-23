"""Offline tests for the Chinese physics Skill's local figure helper.

Run with Pillow installed. The actual openJiuwen host adapter is also exercised
when the WorkSwarm SDK is available; no model or network calls are made. Set
PHYSICS_PAYLOAD to an extracted inner payload to verify the released bytes.
Use --write-demo-dir /absolute/path to create original manual-test inputs.
"""
from __future__ import annotations

import asyncio
import hashlib
import importlib.util
import json
import os
from pathlib import Path
import subprocess
import struct
import sys
import tempfile
import unittest
import zlib

try:
    from PIL import Image, ImageDraw
except ModuleNotFoundError:
    Image = ImageDraw = None


ROOT = Path(__file__).resolve().parents[1]
PAYLOAD = Path(os.environ.get(
    "PHYSICS_PAYLOAD", str(ROOT / "plugins/physics-assumption-check/physics-assumption-check")
)).resolve()
SCRIPT = PAYLOAD / "scripts/prepare_figure.py"


def load_module(name, path):
    spec = importlib.util.spec_from_file_location(name, path)
    module = importlib.util.module_from_spec(spec)
    sys.modules[name] = module
    # Test imports must preserve the exact release payload, including no caches.
    previous = sys.dont_write_bytecode
    try:
        sys.dont_write_bytecode = True
        spec.loader.exec_module(module)
    finally:
        sys.dont_write_bytecode = previous
    return module


def sha(path):
    return hashlib.sha256(Path(path).read_bytes()).hexdigest()


def make_demo_fixtures(directory):
    """Draw original fixtures; these are inputs, not user testing evidence."""
    if Image is None:
        raise RuntimeError("Pillow is required to generate manual-test fixtures.")
    root = Path(directory).resolve()
    root.mkdir(parents=True, exist_ok=True)
    diagram = Image.new("RGB", (800, 500), "white")
    draw = ImageDraw.Draw(diagram)
    # Technical symbols use Pillow's included font; task instructions are UTF-8.
    draw.line((70, 400, 720, 400), fill="black", width=4)
    draw.polygon(((200, 400), (600, 170), (600, 400)), outline="black", width=4)
    draw.rectangle((440, 215, 505, 260), fill="#cee5ff", outline="black", width=3)
    draw.line((474, 240, 474, 330), fill="#cc3333", width=4)
    draw.polygon(((474, 335), (467, 320), (481, 320)), fill="#cc3333")
    draw.text((485, 305), "mg", fill="black")
    draw.text((455, 225), "m", fill="black")
    draw.text((240, 375), "theta = 30 deg", fill="black")
    draw.text((75, 35), "m = 2 kg; g = 9.8 m/s^2; friction unspecified", fill="black")
    path = root / "斜面受力图.png"
    diagram.save(path)
    bad = root / "损坏图片.png"
    bad.write_bytes(b"This is deliberately not an image.\n")
    instructions = root / "测试题目.txt"
    instructions.write_text(
        "这些是本地生成的原创测试输入，不是用户测试截图。\n\n"
        "例一：图中质量为 2 kg 的物块位于倾角 30° 的斜面上，重力加速度取 "
        "9.8 m/s²。题目没有说明摩擦。请先列出已知量、未知量和假设，说明为何不能"
        "仅凭图示断言物块加速度；再在无摩擦假设下给出沿斜面加速度，检查量纲和极限。\n\n"
        "例二：使用 prepare_physics_figure，将斜面受力图.png 放大到宽度 1600，"
        "输出到尚不存在的 斜面放大.png。核对原文件哈希不变、输出尺寸 1600×1000、"
        "默认 enhanced=false。重复相同输出路径应返回中文错误且保留已有文件。\n\n"
        "例三：输入损坏图片.png，应返回结构化中文错误，且不生成输出文件。\n",
        encoding="utf-8",
    )
    return {"diagram": str(path), "invalid_image": str(bad), "instructions": str(instructions)}


@unittest.skipUnless(Image is not None, "Requires Pillow")
class FigureFixtureTestCase(unittest.TestCase):
    def setUp(self):
        self.temp = tempfile.TemporaryDirectory(prefix="physics-figure-tests-")
        self.addCleanup(self.temp.cleanup)
        self.root = Path(self.temp.name)
        self.source = self.root / "题目原图.png"
        image = Image.new("RGB", (100, 80), "red")
        image.paste((0, 255, 0), (50, 0, 100, 80))
        image.save(self.source)
        self.original = self.source.read_bytes()
        self.output = self.root / "处理结果.png"

    def request(self, **kwargs):
        return {"path": str(self.source), "output": str(self.output), **kwargs}

    def assert_chinese(self, text):
        self.assertIsInstance(text, str)
        self.assertRegex(text, r"[\u4e00-\u9fff]")

    def ok(self, inputs):
        result = self.core.prepare_figure(inputs)
        self.assertTrue(result.get("ok"), result)
        self.assertEqual(result["version"], "1.0.1")
        self.assert_chinese(result["message"])
        return result

    def error(self, inputs):
        result = self.core.prepare_figure(inputs)
        self.assertIs(result.get("ok"), False, result)
        self.assertEqual(result["version"], "1.0.1")
        self.assertTrue(result["error"]["code"])
        self.assert_chinese(result["error"]["message"])
        return result


class FigureFunctionalTests(FigureFixtureTestCase):
    @classmethod
    def setUpClass(cls):
        cls.core = load_module("physics_figure_core_under_test", SCRIPT)

    def test_default_enlargement_metadata_unicode_and_immutable_source(self):
        result = self.ok(self.request())
        self.assertEqual(self.source.read_bytes(), self.original)
        self.assertEqual(result["source"]["sha256"], sha(self.source))
        self.assertEqual(result["output"]["sha256"], sha(self.output))
        self.assertEqual((result["source"]["width"], result["source"]["height"]), (100, 80))
        self.assertEqual((result["output"]["width"], result["output"]["height"]), (1600, 1280))
        self.assertEqual(result["output"]["format"], "PNG")
        self.assertEqual(result["processing"]["crop"], [0, 0, 100, 80])
        self.assertIs(result["processing"]["enhanced"], False)
        self.assertEqual(result["processing"]["scale"], 16)
        self.assertTrue(result["limitations"])
        for limitation in result["limitations"]:
            self.assert_chinese(limitation)
        self.assertIn("题目原图", json.dumps(result, ensure_ascii=False))
        with Image.open(self.output) as output:
            self.assertEqual(output.size, (1600, 1280))
            self.assertEqual(output.getpixel((100, 100)), (255, 0, 0))
            self.assertEqual(output.getpixel((1500, 100)), (0, 255, 0))

    def test_crop_has_expected_geometry_and_known_pixels(self):
        result = self.ok(self.request(width=128, crop=[50, 0, 100, 50]))
        self.assertEqual(result["processing"]["crop"], [50, 0, 100, 50])
        self.assertAlmostEqual(result["processing"]["scale"], 2.56)
        with Image.open(self.output) as output:
            self.assertEqual(output.size, (128, 128))
            self.assertEqual(output.getpixel((0, 0)), (0, 255, 0))
            self.assertEqual(output.getpixel((127, 127)), (0, 255, 0))
        self.assertEqual(self.source.read_bytes(), self.original)

    def test_requested_width_never_reduces_existing_image(self):
        result = self.ok(self.request(width=64))
        self.assertEqual((result["output"]["width"], result["output"]["height"]), (100, 80))
        self.assertEqual(result["processing"]["scale"], 1)

    def test_enhancement_is_explicit_and_changes_low_contrast_pixels(self):
        image = Image.new("RGB", (100, 80), (110, 110, 110))
        image.paste((140, 140, 140), (50, 0, 100, 80))
        image.save(self.source)
        source_sha = sha(self.source)
        self.ok(self.request(width=100))
        plain = self.output.read_bytes()
        enhanced_path = self.root / "增强.png"
        result = self.ok(self.request(output=str(enhanced_path), width=100, enhance=True))
        self.assertIs(result["processing"]["enhanced"], True)
        self.assertNotEqual(enhanced_path.read_bytes(), plain)
        self.assertEqual(sha(self.source), source_sha)

    def test_transparent_png_keeps_alpha_channel(self):
        source = self.root / "透明图.png"
        image = Image.new("RGBA", (80, 80), (20, 40, 60, 0))
        image.paste((200, 180, 160, 128), (20, 20, 60, 60))
        image.save(source)
        self.ok(self.request(path=str(source), width=80))
        with Image.open(self.output) as output:
            self.assertEqual(output.mode, "RGBA")
            self.assertEqual(output.getpixel((0, 0))[3], 0)
            self.assertEqual(output.getpixel((40, 40))[3], 128)

    def test_jpeg_exif_orientation_is_applied_before_crop(self):
        source = self.root / "旋转题图.jpg"
        image = Image.new("RGB", (120, 80), "white")
        image.paste((240, 0, 0), (0, 0, 120, 40))
        exif = Image.Exif()
        exif[274] = 6
        exif[270] = "Synthetic test description; omit metadata from derived output."
        image.save(source, exif=exif, quality=100)
        before = sha(source)
        result = self.ok(self.request(path=str(source), crop=[0, 0, 40, 120], width=80))
        self.assertEqual((result["source"]["width"], result["source"]["height"]), (120, 80))
        self.assertEqual((result["source"]["oriented_width"], result["source"]["oriented_height"]), (80, 120))
        self.assertEqual((result["output"]["width"], result["output"]["height"]), (80, 240))
        self.assertEqual(sha(source), before)
        with Image.open(self.output) as output:
            self.assertFalse(output.getexif())

    def test_existing_output_source_and_hardlink_are_not_overwritten(self):
        self.output.write_bytes(b"preserve an existing file")
        cases = [self.request(), self.request(output=str(self.source))]
        hardlink = self.root / "原图硬链接.png"
        os.link(self.source, hardlink)
        cases.append(self.request(output=str(hardlink)))
        for request in cases:
            with self.subTest(output=request["output"]):
                self.error(request)
                self.assertEqual(self.source.read_bytes(), self.original)
                self.assertEqual(self.output.read_bytes(), b"preserve an existing file")
                self.assertEqual(hardlink.read_bytes(), self.original)

    def test_existing_and_dangling_output_symlinks_are_preserved(self):
        for name, target in (("图链接.png", self.source), ("悬空链接.png", self.root / "不存在.png")):
            link = self.root / name
            link.symlink_to(target)
            with self.subTest(name=name):
                self.error(self.request(output=str(link)))
                self.assertTrue(link.is_symlink())
                self.assertEqual(os.readlink(link), str(target))
                self.assertEqual(self.source.read_bytes(), self.original)
                if name == "悬空链接.png":
                    self.assertFalse(target.exists())

    def test_cyclic_input_symlink_returns_structured_error(self):
        first = self.root / "循环图一.png"
        second = self.root / "循环图二.png"
        first.symlink_to(second)
        second.symlink_to(first)
        self.error(self.request(path=str(first)))
        self.assertFalse(self.output.exists())
        self.assertTrue(first.is_symlink())
        self.assertTrue(second.is_symlink())

    def test_invalid_input_shape_paths_unknown_fields_and_width(self):
        requests = [None, [], "path", {}, {"path": str(self.source)},
                    self.request(path="relative.png"), self.request(output="relative.png"),
                    self.request(path="https://example.com/image.png"),
                    self.request(output="https://example.com/result.png"),
                    self.request(path=str(self.source) + "\x00"),
                    self.request(path=1), self.request(output=None),
                    self.request(output=str(self.root / "wrong.jpg")),
                    self.request(output=str(self.root / "missing" / "result.png")),
                    self.request(model="paid"), self.request(enhance="true"),
                    self.request(enhance=1)]
        requests.extend(self.request(width=value) for value in (None, True, False, 63, 4097, 100.5, "128"))
        for request in requests:
            with self.subTest(request=request):
                self.error(request)
                self.assertFalse(self.output.exists())

    def test_invalid_crop_bounds_and_types_create_no_output(self):
        crops = (None, [], [0, 0, 100], [0, 0, 100, 80, 1], "0,0,100,80",
                 [-1, 0, 100, 80], [0, 0, 101, 80], [0, 0, 100, 81],
                 [50, 0, 50, 80], [60, 0, 50, 80], [0, 80, 100, 80],
                 [False, 0, 100, 80], [0.0, 0, 100, 80])
        for index, crop in enumerate(crops):
            with self.subTest(crop=crop):
                output = self.root / f"invalid-crop-{index}.png"
                self.error(self.request(crop=crop, output=str(output)))
                self.assertFalse(output.exists())

    def test_broken_and_unsupported_images_return_structured_errors(self):
        broken = self.root / "损坏.png"
        broken.write_bytes(b"not a PNG file")
        gif = self.root / "不支持.gif"
        Image.new("RGB", (100, 80), "blue").save(gif)
        for path in (broken, gif, self.root / "missing.png", self.root):
            with self.subTest(path=str(path)):
                self.error(self.request(path=str(path)))
                self.assertFalse(self.output.exists())

    def test_multiframe_png_is_rejected_without_output(self):
        source = self.root / "动画.png"
        first = Image.new("RGB", (100, 80), "blue")
        second = Image.new("RGB", (100, 80), "red")
        first.save(source, save_all=True, append_images=[second], duration=100, loop=0)
        with Image.open(source) as image:
            self.assertEqual(image.n_frames, 2)
        self.error(self.request(path=str(source)))
        self.assertFalse(self.output.exists())

    def test_byte_and_source_pixel_limits_are_enforced(self):
        padded = self.root / "超过文件上限.png"
        padded.write_bytes(self.original + b"\x00" * (25 * 1024 * 1024))
        self.error(self.request(path=str(padded)))
        oversized = self.root / "超过像素上限.png"
        image = Image.new("RGB", (5000, 4001), "white")
        image.save(oversized)
        image.close()
        self.error(self.request(path=str(oversized)))
        self.assertFalse(self.output.exists())

    def test_output_pixel_budget_rejects_tall_enlargement(self):
        source = self.root / "细长图.png"
        Image.new("RGB", (100, 1000), "white").save(source)
        self.error(self.request(path=str(source), width=4096))
        self.assertFalse(self.output.exists())

    def test_cli_success_is_single_utf8_json_and_error_uses_exit_two(self):
        command = [sys.executable, str(SCRIPT), "--path", str(self.source),
                   "--output", str(self.output), "--width", "128"]
        success = subprocess.run(command, capture_output=True, text=True, encoding="utf-8", timeout=20)
        self.assertEqual(success.returncode, 0, success.stderr)
        self.assertEqual(success.stderr, "")
        result = json.loads(success.stdout)
        self.assertTrue(result["ok"], result)
        self.assertEqual(result["output"]["width"], 128)
        self.assertIn("处理结果", success.stdout)
        failure = subprocess.run(command, capture_output=True, text=True, encoding="utf-8", timeout=20)
        self.assertEqual(failure.returncode, 2)
        self.assertEqual(failure.stderr, "")
        error = json.loads(failure.stdout)
        self.assertFalse(error["ok"])
        self.assert_chinese(error["error"]["message"])

    def test_cli_help_and_parser_errors_are_chinese(self):
        result = subprocess.run([sys.executable, str(SCRIPT), "--help"],
                                capture_output=True, text=True, encoding="utf-8", timeout=20)
        self.assertEqual(result.returncode, 0)
        self.assert_chinese(result.stdout)
        self.assertIn("--crop", result.stdout)
        self.assertEqual(result.stderr, "")
        for arguments in ([], ["--path", str(self.source), "--output", str(self.output), "--width", "bad"],
                          ["--path", str(self.source), "--output", str(self.output), "--unknown"]):
            with self.subTest(arguments=arguments):
                result = subprocess.run([sys.executable, str(SCRIPT), *arguments], capture_output=True,
                                        text=True, encoding="utf-8", timeout=20)
                self.assertEqual(result.returncode, 2)
                self.assertEqual(result.stderr, "")
                self.assert_chinese(json.loads(result.stdout)["error"]["message"])

    def test_corrupt_exif_is_chinese_json_error_without_warning_stderr(self):
        # A valid PNG with a CRC-valid EXIF chunk whose TIFF directory is cut off.
        # Pillow emits an English UserWarning if the decoder warning is ignored.
        exif = b"II*\x00\x08\x00\x00\x00\x01\x00"
        chunk = b"eXIf" + exif
        encoded = struct.pack(">I", len(exif)) + chunk + struct.pack(">I", zlib.crc32(chunk))
        source = self.root / "元数据损坏.png"
        source.write_bytes(self.original[:33] + encoded + self.original[33:])
        command = [sys.executable, str(SCRIPT), "--path", str(source),
                   "--output", str(self.output), "--width", "128"]
        result = subprocess.run(command, capture_output=True, text=True, encoding="utf-8", timeout=20)
        self.assertEqual(result.returncode, 2, result.stdout)
        self.assertEqual(result.stderr, "")
        error = json.loads(result.stdout)
        self.assertFalse(error["ok"])
        self.assert_chinese(error["error"]["message"])
        self.assertFalse(self.output.exists())


@unittest.skipUnless(Image is not None, "Requires Pillow")
class PhysicsHostAdapterTests(FigureFixtureTestCase):
    @classmethod
    def setUpClass(cls):
        try:
            from openjiuwen.core.common.logging.log_config import configure_log_config, get_log_config_snapshot
            config = get_log_config_snapshot()
            config["log_path"] = os.environ.get(
                "PHYSICS_TEST_LOG_DIR", str(Path(tempfile.gettempdir()) / "physics-figure-host-test-logs")
            )
            configure_log_config(config)
            from openjiuwen.core.foundation.tool import Tool
        except ModuleNotFoundError as exc:
            if not exc.name.startswith("openjiuwen"):
                raise
            raise unittest.SkipTest("Requires the actual WorkSwarm openJiuwen SDK") from exc
        cls.adapter = load_module("physics_figure_adapter_under_test", PAYLOAD / "tools/physics_tool.py")
        cls.host_tool_type = Tool
        cls.core = load_module("physics_figure_host_core_under_test", SCRIPT)

    def test_actual_host_tool_card_and_invoke(self):
        tool = self.adapter.PhysicsFigureTool()
        self.assertIsInstance(tool, self.host_tool_type)
        self.assertEqual(tool.card.name, "prepare_physics_figure")
        self.assert_chinese(tool.card.description)
        self.assertFalse(tool.card.input_params["additionalProperties"])
        for name in ("path", "output", "width", "crop", "enhance"):
            self.assert_chinese(tool.card.input_params["properties"][name]["description"])
        result = asyncio.run(tool.invoke(self.request(width=128)))
        self.assertTrue(result["ok"], result)
        self.assertEqual((result["output"]["width"], result["output"]["height"]), (128, 102))
        self.assertEqual(result["source"]["sha256"], hashlib.sha256(self.original).hexdigest())

    def test_actual_host_stream_yields_one_result_and_propagates_errors(self):
        tool = self.adapter.PhysicsFigureTool()

        async def collect(inputs):
            return [result async for result in tool.stream(inputs)]

        results = asyncio.run(collect(self.request(width=128)))
        self.assertEqual(len(results), 1)
        self.assertTrue(results[0]["ok"], results)
        errors = asyncio.run(collect(self.request(width=128)))
        self.assertEqual(len(errors), 1)
        self.assertFalse(errors[0]["ok"])
        self.assert_chinese(errors[0]["error"]["message"])


if __name__ == "__main__":
    if len(sys.argv) == 3 and sys.argv[1] == "--write-demo-dir":
        print(json.dumps(make_demo_fixtures(sys.argv[2]), ensure_ascii=False, indent=2))
    else:
        unittest.main()
