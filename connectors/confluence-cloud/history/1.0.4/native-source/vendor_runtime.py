"""Install the upstream CLI from the pinned vendor release if it is absent."""

import hashlib
import os
import platform
import sys
import tarfile
import tempfile
import urllib.request
from pathlib import Path

CLI = "twg"
VERSION = "1.4.4"
DIGESTS = {
    ('darwin', 'arm64'): 'a34270ee07ac8a701dbab3f8be669ac640e575fdc85758d5c56846975a7dceec',
    ('darwin', 'x64'): 'c6081730886a4c920377fa17c0e2d674fa50ec6a4b4d379ebfb2ef78c454bebd',
    ('linux', 'arm64'): '4dab6d4fbc94e450fc79e661ac48616ba1099b40077dedc550d4d105e1cb83cc',
    ('linux', 'x64'): '36a93b0ad0011d80909cc00508091c34df03dd0bf1644fded67bf94f2c9ffc07',
    ('windows', 'arm64'): '0e754ee80b3c97e2b255540522e234f0ce5cc33f2831c9fdcd91628d2b98a17e',
    ('windows', 'x64'): 'a490eecff0aea9222cca99b6fb573d365e90c7240e09021d67eae16541c952bc',
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
