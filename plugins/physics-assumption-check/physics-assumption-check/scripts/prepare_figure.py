#!/usr/bin/env python3
"""本地裁剪并放大物理题图；不识别图中连接关系，也不调用模型或网络。

改编自 Carlotess/fisica 的 ampliar.py（MIT，Copyright (c) 2026 Carlotess）。
2026-10-23：中文化，增加输入/输出边界、JSON 结果、拒绝覆盖与可选增强。
完整许可见 ../licenses/fisica/LICENSE，修改范围见 ../THIRD_PARTY_NOTICES.md。
"""
from __future__ import annotations

import argparse
import hashlib
import io
import json
import os
from pathlib import Path
import sys
import warnings

VERSION = "1.0.1"
MAX_INPUT_BYTES = 25 * 1024 * 1024
MAX_INPUT_PIXELS = 20_000_000
MAX_OUTPUT_PIXELS = 32_000_000
MAX_OUTPUT_BYTES = 64 * 1024 * 1024
ALLOWED = {"path", "output", "width", "crop", "enhance"}


class FigureError(Exception):
    def __init__(self, code: str, message: str) -> None:
        super().__init__(message)
        self.code = code


def error_result(code: str, message: str) -> dict:
    return {"ok": False, "version": VERSION, "error": {"code": code, "message": message}}


def _path(value, label: str) -> Path:
    if not isinstance(value, str) or not value or len(value) > 4096 or "\x00" in value:
        raise FigureError("invalid_path", f"{label}必须为非空的本地绝对路径，最多 4096 个字符。")
    if "://" in value or not Path(value).is_absolute():
        raise FigureError("invalid_path", f"{label}只接受本地绝对路径，不支持网址或相对路径。")
    return Path(value)


def _prepare(inputs: dict) -> dict:
    if not isinstance(inputs, dict) or set(inputs) - ALLOWED or not {"path", "output"} <= set(inputs):
        raise FigureError("invalid_input", "请提供 path 和 output；可选参数仅有 width、crop、enhance。")
    source = _path(inputs["path"], "输入图片")
    output = _path(inputs["output"], "输出图片")
    width = inputs.get("width", 1600)
    if type(width) is not int or not 64 <= width <= 4096:
        raise FigureError("invalid_width", "width 必须为 64 至 4096 的整数。")
    enhance = inputs.get("enhance", False)
    if type(enhance) is not bool:
        raise FigureError("invalid_enhance", "enhance 必须为布尔值；默认关闭增强。")
    crop = inputs.get("crop")
    if "crop" in inputs and (not isinstance(crop, list) or len(crop) != 4 or any(type(v) is not int for v in crop)):
        raise FigureError("invalid_crop", "crop 必须为四个整数 [左, 上, 右, 下]，使用旋转校正后的像素坐标。")
    if output.suffix.lower() != ".png":
        raise FigureError("invalid_output", "输出路径必须以 .png 结尾。")
    if os.path.lexists(output):
        raise FigureError("output_exists", "输出路径已存在；请选择新的 PNG 路径，不能覆盖已有文件或链接。")
    if not output.parent.is_dir():
        raise FigureError("missing_directory", "输出目录不存在；请先创建并选择自己的测试目录。")
    try:
        source = source.resolve(strict=True)
        if not source.is_file():
            raise FigureError("invalid_image", "输入路径不是普通图片文件。")
        if source.stat().st_size > MAX_INPUT_BYTES:
            raise FigureError("input_too_large", "输入图片不能超过 25 MiB。")
        with source.open("rb") as stream:
            raw = stream.read(MAX_INPUT_BYTES + 1)
        if len(raw) > MAX_INPUT_BYTES:
            raise FigureError("input_too_large", "输入图片不能超过 25 MiB。")
    except FileNotFoundError:
        raise FigureError("missing_image", "找不到输入图片；请提供后端可访问的实际文件路径。") from None
    except (OSError, RuntimeError):
        raise FigureError("read_failed", "无法读取输入图片；请检查路径和读取权限。") from None
    try:
        from PIL import Image, ImageEnhance, ImageFilter, ImageOps, UnidentifiedImageError
    except ImportError:
        raise FigureError("missing_dependency", "当前 Python 缺少 Pillow。请在独立虚拟环境安装 requirements-local.txt，并用该环境启动后端。") from None
    try:
        with warnings.catch_warnings():
            warnings.simplefilter("error", UserWarning)
            warnings.simplefilter("error", Image.DecompressionBombWarning)
            with Image.open(io.BytesIO(raw)) as original:
                fmt = original.format
                original_size = original.size
                if fmt not in {"PNG", "JPEG"}:
                    raise FigureError("unsupported_format", "仅支持静态 PNG 和 JPEG 图片；请先导出明确的单张题图。")
                if getattr(original, "n_frames", 1) != 1:
                    raise FigureError("animated_image", "不支持多帧图片；请先导出所需的单帧 PNG。")
                if original.width * original.height > MAX_INPUT_PIXELS:
                    raise FigureError("input_pixels_exceeded", "输入图片最多 2000 万像素。")
                original.load()
                oriented = ImageOps.exif_transpose(original)
                oriented_size = oriented.size
                has_alpha = "A" in oriented.getbands() or "transparency" in oriented.info
                image = oriented.convert("RGBA" if has_alpha else "RGB")
        selected = crop or [0, 0, image.width, image.height]
        left, top, right, bottom = selected
        if not (0 <= left < right <= image.width and 0 <= top < bottom <= image.height):
            raise FigureError("invalid_crop", "裁剪区域必须有正面积，且全部位于旋转校正后的原图范围内。")
        if crop is not None:
            image = image.crop(tuple(selected))
        scale = max(1.0, width / image.width)
        size = (round(image.width * scale), max(1, round(image.height * scale)))
        if size[0] * size[1] > MAX_OUTPUT_PIXELS:
            raise FigureError("output_pixels_exceeded", "放大后的图片不能超过 3200 万像素；请缩小 width 或先裁剪。")
        if image.size != size:
            image = image.resize(size, Image.Resampling.LANCZOS)
        if enhance:
            image = image.filter(ImageFilter.UnsharpMask(radius=2, percent=120, threshold=2))
            image = ImageEnhance.Contrast(image).enhance(1.2)
        image.info.clear()
        encoded = io.BytesIO()
        image.save(encoded, format="PNG")
        content = encoded.getvalue()
        if len(content) > MAX_OUTPUT_BYTES:
            raise FigureError("output_too_large", "输出 PNG 超过 64 MiB；请减小放大尺寸。")
    except (Image.DecompressionBombWarning, Image.DecompressionBombError):
        raise FigureError("input_pixels_exceeded", "输入图片的像素尺寸超过安全处理范围。") from None
    except (UnidentifiedImageError, OSError, ValueError, SyntaxError, UserWarning):
        raise FigureError("invalid_image", "图片损坏或无法解码；请使用完整的静态 PNG/JPEG。") from None
    # Exclusive creation also rejects paths created between validation and writing.
    fd = None
    created_identity = None
    try:
        flags = os.O_WRONLY | os.O_CREAT | os.O_EXCL | getattr(os, "O_NOFOLLOW", 0)
        fd = os.open(output, flags, 0o600)
        stat = os.fstat(fd)
        created_identity = (stat.st_dev, stat.st_ino)
        with os.fdopen(fd, "wb") as stream:
            fd = None
            stream.write(content)
    except FileExistsError:
        raise FigureError("output_exists", "输出路径已存在；请选择新的 PNG 路径，不能覆盖已有文件或链接。") from None
    except OSError:
        if created_identity is not None:
            try:
                current = output.lstat()
                if (current.st_dev, current.st_ino) == created_identity:
                    output.unlink()
            except OSError:
                pass
        raise FigureError("write_failed", "无法写入输出 PNG；请检查目录权限和剩余空间。") from None
    finally:
        if fd is not None:
            os.close(fd)
    return {
        "ok": True, "version": VERSION,
        "message": "题图已在本地处理完成，请查看输出图并核对原图中的连接关系。",
        "source": {"path": str(source), "sha256": hashlib.sha256(raw).hexdigest(),
                   "width": original_size[0], "height": original_size[1], "format": fmt,
                   "oriented_width": oriented_size[0], "oriented_height": oriented_size[1]},
        "output": {"path": str(output.resolve()), "sha256": hashlib.sha256(content).hexdigest(),
                   "width": size[0], "height": size[1], "format": "PNG"},
        "processing": {"crop": selected, "enhanced": enhance, "scale": scale},
        "limitations": ["插值放大不会恢复原图缺失的信息；增强可能改变细线外观。",
                        "本工具不判断绳索、节点、极性或物理模型；看不清的细节仍需声明或请用户澄清。"],
    }


def prepare_figure(inputs: dict) -> dict:
    try:
        return _prepare(inputs)
    except FigureError as error:
        return error_result(error.code, str(error))
    except (MemoryError, OverflowError):
        return error_result("resource_limit", "图片处理超出本机资源范围，请使用更小的图片或裁剪区域。")


class ChineseParser(argparse.ArgumentParser):
    def format_help(self):
        return super().format_help().replace("usage: ", "用法：")

    def error(self, message):
        raise FigureError("invalid_arguments", "命令参数无效；请运行 --help 查看中文用法。")


def main(argv=None) -> int:
    parser = ChineseParser(description=__doc__, add_help=False)
    parser._positionals.title = "位置参数"
    parser._optionals.title = "可选参数"
    parser.add_argument("-h", "--help", action="help", help="显示中文用法并退出")
    parser.add_argument("--path", required=True, help="输入静态 PNG/JPEG 的本地绝对路径")
    parser.add_argument("--output", required=True, help="新的输出 PNG 绝对路径；拒绝覆盖")
    parser.add_argument("--width", "--ancho", dest="width", type=int, default=1600,
                        help="目标宽度 64–4096 像素，默认 1600；只放大，不缩小")
    parser.add_argument("--crop", nargs=4, type=int, metavar=("左", "上", "右", "下"),
                        help="旋转校正后的原图像素裁剪区域")
    parser.add_argument("--enhance", action="store_true", help="可选锐化与对比度增强，默认关闭")
    try:
        args = parser.parse_args(argv)
        values = vars(args)
        if values["crop"] is None:
            del values["crop"]
        result = prepare_figure(values)
    except FigureError as error:
        result = error_result(error.code, str(error))
    print(json.dumps(result, ensure_ascii=False, allow_nan=False))
    return 0 if result["ok"] else 2


if __name__ == "__main__":
    sys.exit(main())
