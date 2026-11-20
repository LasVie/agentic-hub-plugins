#!/usr/bin/env python3
"""Use the official external CLI and verify both exact archive payloads."""
from __future__ import annotations
import argparse
import hashlib
import json
import os
from pathlib import Path
import shutil
import subprocess
import stat
import tempfile
import zipfile

BASE = Path(__file__).resolve().parents[1]
SLUG = "business-interruption-rehearsal-team"
CLI_PIN = "c8ee4ef44be0453470114aa5a19f4e1017462907"


def sha(data):
    return hashlib.sha256(data).hexdigest()


def payload_files(root):
    files = {}
    for p in sorted(root.rglob("*")):
        if p.is_symlink():
            raise ValueError("载荷不能包含符号链接")
        if p.is_file():
            rel = p.relative_to(root).as_posix()
            if p.suffix == ".pyc" or any(x in {".local", "__pycache__", ".git"} for x in p.parts):
                raise ValueError("载荷含开发缓存")
            files[rel] = p.read_bytes()
    return files


def retain_archive(candidate, target):
    if target.exists():
        if target.read_bytes() == candidate.read_bytes():
            return
        # The CLI may vary archive timestamps. Keep existing bytes only if every
        # member, including wrapper/icon metadata, is byte-for-byte identical.
        with zipfile.ZipFile(target) as old, zipfile.ZipFile(candidate) as new:
            if old.namelist() == new.namelist() and all(old.read(n) == new.read(n) for n in old.namelist()):
                return
        raise ValueError("已有不同内容的版本包；保留历史证据后另行处理，不覆盖已测试包")
    with target.open("xb") as out:
        out.write(candidate.read_bytes())


def inspect(archive, prefix, files, extra=()):
    with zipfile.ZipFile(archive) as z:
        names = z.namelist()
        if len(names) != len(set(names)) or z.testzip() is not None:
            raise ValueError("ZIP存在重复或CRC错误")
        allowed = {prefix + n for n in files} | set(extra)
        if set(names) != allowed:
            raise ValueError("ZIP文件清单不一致")
        if len(names) > 1000 or archive.stat().st_size > 95 * 1024**2 or sum(i.file_size for i in z.infolist()) > 512 * 1024**2:
            raise ValueError("ZIP 体积或条目数超限")
        for i in z.infolist():
            if i.is_dir() or stat.S_ISLNK(i.external_attr >> 16) or chr(92) in i.filename:
                raise ValueError("ZIP 含目录条目、符号链接或非法路径")
            if i.filename.startswith("/") or ".." in Path(i.filename).parts or i.file_size / max(i.compress_size, 1) > 50:
                raise ValueError("ZIP路径或压缩比例不合规")
        if {n: z.read(prefix + n) for n in files} != files:
            raise ValueError("ZIP载荷与源文件不一致")


def main():
    p = argparse.ArgumentParser(description="使用固定官方CLI构建本专家团的中文原生包与市场包装")
    p.add_argument("--python", required=True)
    p.add_argument("--cli-root", required=True)
    args = p.parse_args()
    meta = json.loads((BASE / "asset.json").read_text(encoding="utf-8"))
    version = meta["version"]
    payload = BASE / SLUG
    files = payload_files(payload)
    for rel in ("manifest.json", "README.md", "agents/leader/AGENT.md"):
        if rel not in files:
            raise ValueError("缺少必需载荷文件")
    staging = BASE / ".local/staging"
    staging.mkdir(parents=True, exist_ok=True)
    run = Path(tempfile.mkdtemp(prefix="official-", dir=staging))
    # No provider credentials, global caches or other task's writable state.
    env = {k: os.environ[k] for k in ("PATH", "HOME", "USER", "LOGNAME", "SHELL") if k in os.environ}
    env.update({"PYTHONPATH": str(Path(args.cli_root).resolve()), "PYTHONDONTWRITEBYTECODE": "1", "XDG_CACHE_HOME": str(BASE / ".local/cache")})
    command = [args.python, "-B", "-m", "openjiuwen_agentichub.main"]
    log = []
    def call(tail):
        result = subprocess.run(command + tail, env=env, text=True, stdout=subprocess.PIPE, stderr=subprocess.STDOUT)
        log.append({"arguments": tail, "exit": result.returncode, "output": result.stdout})
        print(result.stdout)
        if result.returncode:
            raise RuntimeError("官方CLI检查失败")
    call(["init", SLUG, "--type", "agent-group", "--path", str(run)])
    stage = run / SLUG
    # Preserve the just-generated scaffold outside the clean wrapper staging.
    (stage / SLUG).rename(run / "init-scaffold")
    shutil.copytree(payload, stage / SLUG)
    (stage / "icon.png").unlink(missing_ok=True)
    (stage / "plugin.yaml").write_text(
        f"name: {SLUG}\nversion: {version}\ndisplay_name: 业务中断演练与复工核验专家团\n"
        "description: 演练共享系统中断和分阶段复工，独立核对工作项。\n"
        "runtime:\n  type: agent-group\nmetadata:\n  author: Cai Zhenze\n  tags: [桌面演练, 业务连续性, 复工核验]\n", encoding="utf-8")
    call(["validate", str(stage)])
    call(["pack", str(stage), "--output", str(run / "out")])
    packed, = (run / "out").glob("*.zip")
    native_draft = run / "native.zip"
    with zipfile.ZipFile(native_draft, "w", compression=zipfile.ZIP_STORED) as z:
        for rel, data in files.items():
            item = zipfile.ZipInfo(rel, date_time=(2026, 11, 20, 0, 0, 0))
            item.external_attr = 0o100644 << 16
            z.writestr(item, data)
    releases = BASE / "release" / version
    tests = BASE / "test-packages"
    releases.mkdir(parents=True, exist_ok=True)
    tests.mkdir(exist_ok=True)
    native = tests / f"{SLUG}-{version}-native.zip"
    wrapped = releases / f"{SLUG}-{version}-agent-group.zip"
    outer = f"{SLUG}-{version}/"
    inspect(native_draft, "", files)
    inspect(packed, outer + SLUG + "/", files, (outer + "plugin.yaml",))
    retain_archive(native_draft, native)
    retain_archive(packed, wrapped)
    inspect(native, "", files)
    inspect(wrapped, outer + SLUG + "/", files, (outer + "plugin.yaml",))
    artifact = {"asset": SLUG, "type": "agent-group", "version": version, "task_id": meta["task_id"],
                "tool": {"name": "official agentichub CLI", "version": "0.0.1", "commit": CLI_PIN},
                "payload_sha256": {n: sha(b) for n, b in files.items()}, "payload_equality": True,
                "artifacts": {k: {"path": str(path.relative_to(BASE)), "sha256": sha(path.read_bytes()), "bytes": path.stat().st_size}
                              for k, path in (("native", native), ("wrapped", wrapped))},
                "source_review_sha256": sha((BASE / "SOURCE_REVIEW.md").read_bytes()),
                "test_report_sha256": sha((BASE / "TEST_REPORT.md").read_bytes())}
    (releases / "artifact.json").write_text(json.dumps(artifact, ensure_ascii=False, indent=2) + "\n", encoding="utf-8")
    (run / "cli-log.json").write_text(json.dumps(log, ensure_ascii=False, indent=2), encoding="utf-8")
    print(json.dumps(artifact["artifacts"], ensure_ascii=False, indent=2))


if __name__ == "__main__":
    main()
