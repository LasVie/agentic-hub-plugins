import fcntl
import hashlib
import json
import os
from pathlib import Path
import re
import shutil
import subprocess
import sys
import tempfile
import time


INSTALL_TIMEOUT = 150
LOCK_TIMEOUT = 180


def read_json(path):
    try:
        value = json.loads(path.read_text(encoding="utf-8"))
        return value if isinstance(value, dict) else {}
    except (OSError, ValueError):
        return {}


def write_json(path, value):
    path.parent.mkdir(parents=True, exist_ok=True)
    temporary = None
    try:
        with tempfile.NamedTemporaryFile(mode="w", encoding="utf-8", dir=path.parent, delete=False) as stream:
            temporary = Path(stream.name)
            json.dump(value, stream)
            stream.write("\n")
        os.chmod(temporary, 0o600)
        os.replace(temporary, path)
    finally:
        if temporary is not None:
            temporary.unlink(missing_ok=True)


def find_node(configuration):
    explicit = os.environ.get("ANNOTATE_NODE")
    candidates = [explicit] if explicit else [read_json(configuration).get("node"), shutil.which("node")]
    if not explicit:
        for applications in (Path("/Applications"), Path.home() / "Applications"):
            for application in sorted(applications.glob("*Swarm.app")):
                candidates.append(str(application / "Contents/Resources/node-runtime/bin/node"))
    for candidate in dict.fromkeys(value for value in candidates if isinstance(value, str) and value):
        executable = Path(candidate).expanduser()
        if not executable.is_file():
            continue
        try:
            result = subprocess.run([str(executable), "--version"], capture_output=True, text=True, timeout=5, check=True)
        except (OSError, subprocess.SubprocessError):
            continue
        match = re.fullmatch(r"v(\d+)\.\d+\.\d+\s*", result.stdout)
        if match and int(match.group(1)) >= 20:
            return str(executable.resolve()), result.stdout.strip()
    raise RuntimeError("未在 WorkSwarm 或 PATH 中找到 Node.js >=20。请检查桌面应用自带的运行环境，无需安装 Conda。")


def fingerprint(runtime, version):
    digest = hashlib.sha256(version.encode("utf-8"))
    for filename in ("package.json", "package-lock.json"):
        digest.update((runtime / filename).read_bytes())
    return digest.hexdigest()


def dependencies_present(runtime):
    packages = read_json(runtime / "package-lock.json").get("packages", {})
    dependencies = {name: metadata for name, metadata in packages.items() if name.startswith("node_modules/")}
    if not dependencies:
        return False
    for name, metadata in dependencies.items():
        installed = read_json(runtime / name / "package.json")
        if not installed or installed.get("version") != metadata.get("version"):
            return False
    return all((runtime / filename).is_file() for filename in (
        "node_modules/playwright-core/index.mjs",
        "node_modules/@modelcontextprotocol/sdk/dist/esm/server/index.js",
    ))


def ensure_runtime(payload, cache, node, version):
    runtime = payload / "runtime"
    expected = fingerprint(runtime, version)
    state = runtime / "node_modules/.annotate-ready.json"
    identity = hashlib.sha256(str(runtime.resolve()).encode("utf-8")).hexdigest()[:24]
    cache.mkdir(parents=True, exist_ok=True)
    deadline = time.monotonic() + LOCK_TIMEOUT
    with (cache / f"bootstrap-{identity}.lock").open("a") as lock:
        while True:
            try:
                fcntl.flock(lock, fcntl.LOCK_EX | fcntl.LOCK_NB)
                break
            except BlockingIOError:
                if time.monotonic() >= deadline:
                    raise RuntimeError("另一个批注会话正在准备依赖，请等待其完成后重试。")
                time.sleep(0.1)
        if read_json(state).get("fingerprint") != expected or not dependencies_present(runtime):
            state.unlink(missing_ok=True)
            print("网页圈选与批注：首次使用正在初始化并下载锁定的 npm 依赖，不安装全局包、不修改 Conda。", file=sys.stderr, flush=True)
            try:
                result = subprocess.run(
                    [node, str(payload / "scripts/setup.mjs")],
                    env={**os.environ, "npm_config_cache": os.environ.get("npm_config_cache", str(cache / "npm"))},
                    stdin=subprocess.DEVNULL,
                    stdout=sys.stderr,
                    stderr=sys.stderr,
                    timeout=min(INSTALL_TIMEOUT, max(1, deadline - time.monotonic())),
                    check=False,
                )
            except subprocess.TimeoutExpired as error:
                raise RuntimeError("依赖安装超时。请检查 npm 源及网络连接，然后重新点击插件使用。") from error
            if result.returncode != 0:
                raise RuntimeError("自动安装依赖失败。请查看上方 npm 原始错误并检查网络或软件源，然后重新点击插件使用。")
            if not dependencies_present(runtime):
                raise RuntimeError("依赖安装不完整，请重新点击插件使用；未完成的安装不会标记为就绪。")
            write_json(state, {"fingerprint": expected})
        write_json(cache / "runtime.json", {"node": node})


def main():
    payload = Path(__file__).resolve().parents[1]
    cache = Path(os.environ.get("ANNOTATE_DATA_DIR", str(Path.home() / ".cache" / "agentic-hub-annotate")))
    configuration = cache / "runtime.json"
    node, version = find_node(configuration)
    ensure_runtime(payload, cache, node, version)
    os.execv(str(node), [str(node), str(payload / "runtime" / "server" / "index.mjs")])


if __name__ == "__main__":
    try:
        main()
    except (OSError, ValueError, RuntimeError) as error:
        print(f"网页圈选与批注启动失败： {error}", file=sys.stderr)
        sys.exit(1)
