"""Install the upstream CLI from the pinned vendor release if it is absent."""

import hashlib
import os
import platform
import sys
import tarfile
import tempfile
import urllib.request
from pathlib import Path

CLI = "acli"
VERSION = "1.3.40-stable"
DIGESTS = {
    ('darwin', 'arm64'): '70566186d2e1d01160ef0dc35aefc1ffb46d1dd4a60ff41a45248adf8b897b97',
    ('darwin', 'x64'): '92fae879de243f3c12fc805d4f154f9a331091e974536c4035bae696f96730ff',
    ('linux', 'arm64'): 'b1880f66f299ab2b56528c90bbff50ca8263e7331868a31d0b6ca7b67f7469e5',
    ('linux', 'x64'): '19c113789e8a66bf11a80dc18cf75e7e7ba239112005f4e9cd69db05f11ac526',
}
LIMIT = 140 * 1024 * 1024


def platform_id():
    if sys.platform == "darwin":
        system = "darwin"
    elif sys.platform.startswith("linux"):
        system = "linux"
    elif sys.platform == "win32":
        system = "windows"
    else:
        raise ValueError("此操作系统需要手动安装官方 CLI。")
    architecture = {"arm64": "arm64", "aarch64": "arm64", "x86_64": "x64", "amd64": "x64"}.get(platform.machine().lower())
    if (system, architecture) not in DIGESTS:
        raise ValueError("此操作系统或架构需要手动安装官方 CLI。")
    return system, architecture


def verify_download(url, expected, target):
    digest = hashlib.sha256()
    size = 0
    with urllib.request.urlopen(url, timeout=30) as response, target.open("wb") as stream:
        while True:
            part = response.read(256 * 1024)
            if not part:
                break
            size += len(part)
            if size > LIMIT:
                raise ValueError("官方安装文件超过允许的大小。")
            digest.update(part)
            stream.write(part)
    if digest.hexdigest() != expected:
        raise ValueError("官方安装文件的 SHA-256 校验失败。")


def install(bin_dir):
    system, architecture = platform_id()
    suffix = ".exe" if system == "windows" else ""
    if CLI == "acli":
        asset = f"acli_{VERSION}_{system}_{'amd64' if architecture == 'x64' else architecture}"
        url = f"https://acli.atlassian.com/{system}/{VERSION}/{asset}.tar.gz"
    else:
        url = f"https://teamwork-graph.atlassian.com/cli/twg-{system}-{architecture}-v{VERSION}{suffix}"
    bin_dir.mkdir(mode=0o700, parents=True, exist_ok=True)
    with tempfile.TemporaryDirectory(prefix=".install-", dir=bin_dir) as temporary:
        transfer = Path(temporary) / "transfer"
        verify_download(url, DIGESTS[(system, architecture)], transfer)
        binary = transfer
        if CLI == "acli":
            binary = Path(temporary) / CLI
            with tarfile.open(transfer, "r:gz") as bundle:
                member = bundle.getmember(f"{asset}/acli")
                if not member.isfile() or member.size > LIMIT:
                    raise ValueError("官方归档中的 CLI 文件无效。")
                with bundle.extractfile(member) as stream:
                    binary.write_bytes(stream.read())
        binary.chmod(0o700)
        os.replace(binary, bin_dir / (CLI + suffix))
