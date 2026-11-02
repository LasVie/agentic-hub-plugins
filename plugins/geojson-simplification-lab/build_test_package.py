#!/usr/bin/env python3
"""Derive a deterministic WorkSwarm ZIP from the checked canonical package.

Adapted from the repository's offline-optics-lab packaging helper. Requires the
same developer environment as tools/asset_release.py; never starts the plugin.
"""

from __future__ import annotations

import io
import json
from pathlib import Path
import stat
import sys
import zipfile

ASSET = Path(__file__).resolve().parent
ROOT = ASSET.parents[1]
sys.dont_write_bytecode = True
sys.path.insert(0, str(ROOT / "tools"))
from asset_release import check_asset, inspect_zip, read_json, require, sha


def native_bytes(files: dict[str, bytes]) -> bytes:
    """Keep every payload byte; remove only the Hub marketplace wrapper."""
    buffer = io.BytesIO()
    with zipfile.ZipFile(buffer, "w", compression=zipfile.ZIP_STORED) as archive:
        for name, body in sorted(files.items()):
            info = zipfile.ZipInfo(name, (1980, 1, 1, 0, 0, 0))
            info.create_system = 3
            info.external_attr = (stat.S_IFREG | 0o644) << 16
            archive.writestr(info, body)
    body = buffer.getvalue()
    with zipfile.ZipFile(io.BytesIO(body)) as archive:
        require(archive.testzip() is None, "原生 ZIP 的 CRC 校验失败")
        require({name: archive.read(name) for name in archive.namelist()} == files,
                "原生 ZIP 与市场 ZIP 的内层文件不一致")
    return body


def verify_destination(path: Path, body: bytes) -> None:
    require(path.is_relative_to(ROOT), f"输出路径不在仓库内：{path}")
    cursor = ROOT
    for part in path.relative_to(ROOT).parts:
        cursor /= part
        require(not cursor.is_symlink(), f"输出路径不能是符号链接：{cursor}")
    if path.exists():
        require(path.is_file() and path.read_bytes() == body,
                f"已有同版本文件内容不同；请升级版本，不得覆盖：{path}")


def write_new_or_identical(path: Path, body: bytes) -> None:
    verify_destination(path, body)
    if path.exists():
        return
    path.parent.mkdir(parents=True, exist_ok=True)
    try:
        with path.open("xb") as stream:
            stream.write(body)
    except FileExistsError:
        # A concurrent invocation must also preserve an already-created file.
        verify_destination(path, body)


def main() -> None:
    metadata, payload, _ = check_asset(ASSET)
    slug, version = metadata["name"], metadata["version"]
    require(metadata["type"] == "agent-plugin", "仅支持 Plugin 包")
    canonical = ROOT / "releases" / "agent-plugin" / slug / version / f"{slug}-{version}.zip"
    canonical_body = canonical.read_bytes()
    wrapper, canonical_hashes = inspect_zip(canonical_body)
    require(wrapper.get("name") == slug and wrapper.get("version") == version
            and wrapper.get("runtime", {}).get("type") == "agent-plugin",
            "市场 ZIP 的插件标识、版本或类型不一致")
    artifact = read_json(canonical.parent / "artifact.json")
    require(all(artifact.get(key) == value for key, value in {
        "name": slug, "version": version, "type": "agent-plugin",
        "zip": canonical.name, "sha256": sha(canonical_body),
        "payload_sha256": canonical_hashes,
    }.items()), "市场 ZIP 与 artifact.json 记录不一致")
    current_hashes = {path.relative_to(payload).as_posix(): sha(path.read_bytes())
                      for path in sorted(payload.rglob("*")) if path.is_file()}
    require(current_hashes == canonical_hashes,
            "当前内层文件已变更；请先重新检查并打包市场 ZIP")
    prefix = f"{slug}/{slug}/"
    with zipfile.ZipFile(io.BytesIO(canonical_body)) as archive:
        require(not any(info.is_dir() for info in archive.infolist()),
                "市场 ZIP 含意外目录条目")
        files = {name[len(prefix):]: archive.read(name)
                 for name in archive.namelist() if name.startswith(prefix)}
    body = native_bytes(files)
    native = ASSET / "test-packages" / f"{slug}-{version}-workswarm.zip"
    dist = ROOT / "dist" / slug / version
    copy = dist / native.name
    record = {
        "version": version,
        "canonical_zip": str(canonical), "canonical_sha256": sha(canonical_body),
        "workswarm_zip": str(copy), "workswarm_sha256": sha(body),
        "payload_identical": True,
        "payload_files": dict(sorted(canonical_hashes.items())),
    }
    outputs = {
        native: body,
        copy: body,
        dist / "companion-artifact.json": (json.dumps(record, ensure_ascii=False, indent=2) + "\n").encode("utf-8"),
    }
    # Check all destinations before writing any. Identical existing files stay
    # untouched; a different version payload requires a version bump.
    for path, content in outputs.items():
        verify_destination(path, content)
    for path, content in outputs.items():
        write_new_or_identical(path, content)
        require(path.read_bytes() == content, f"输出回读校验失败：{path}")
    print(json.dumps({key: value for key, value in record.items() if key != "payload_files"},
                     ensure_ascii=False, indent=2))


if __name__ == "__main__":
    main()
