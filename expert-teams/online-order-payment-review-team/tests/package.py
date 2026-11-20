"""Package this asset with the pinned CLI and compare the exact payloads."""

import argparse
import hashlib
import json
import os
from pathlib import Path
import shutil
import subprocess
import sys
import tempfile
import zipfile


ASSET = Path(__file__).resolve().parents[1]
SLUG = ASSET.name
# The maintained helpers already enforce archive members, bounds and immutable ZIPs.
sys.path.insert(0, str(ASSET.parent / "business-interruption-rehearsal-team/tests"))
from package import inspect, payload_files, retain_archive


def digest(data):
    return hashlib.sha256(data).hexdigest()


def main():
    cli = argparse.ArgumentParser(description=__doc__)
    cli.add_argument("--python", required=True)
    cli.add_argument("--cli-root", required=True, type=Path, help="Pinned skillhub checkout root")
    args = cli.parse_args()
    team = ASSET / SLUG
    info = json.loads((ASSET / "asset.json").read_text())
    version = info["version"]
    manifest = json.loads((team / "manifest.json").read_text())
    if (manifest["name"], manifest["version"], manifest["package_type"]) != (SLUG, version, "agent_group"):
        raise ValueError("Native identity differs from asset")
    if manifest["display_name"]["zh"] != info["display_name"]:
        raise ValueError("Native display name differs from asset")
    pin = json.loads((ASSET / "provenance.json").read_text())["references"][0]["version"]
    approved = json.loads((ASSET.parent / "business-interruption-rehearsal-team/tests/records/official-cli-sources.json").read_text())
    if approved["ref"] != pin:
        raise ValueError("CLI pin differs from reviewed source record")
    for name, expected in approved["files_sha256"].items():
        if digest((args.cli_root / name).read_bytes()) != expected:
            raise ValueError(f"CLI source differs from pin: {name}")
    files = payload_files(team)
    staging = ASSET / ".local/staging"
    staging.mkdir(exist_ok=True, parents=True)
    run = Path(tempfile.mkdtemp(prefix="official-", dir=staging))
    stage = run / "wrapper"
    stage.mkdir()
    shutil.copytree(team, stage / SLUG)
    outer = stage / "plugin.yaml"
    quoted = lambda value: json.dumps(value, ensure_ascii=False)
    outer.write_text(
        f"name: {quoted(SLUG)}\nversion: {quoted(version)}\n"
        f"display_name: {quoted(info['display_name'])}\ndescription: {quoted(info['description'])}\n"
        "runtime:\n  type: agent-group\n"
        f"metadata:\n  author: {quoted(info['publisher'])}\n  tags: {quoted(info['tags'])}\n",
        encoding="utf-8",
    )
    env = {"PATH": os.environ["PATH"], "PYTHONPATH": str(args.cli_root.resolve() / "cli"),
           "PYTHONDONTWRITEBYTECODE": "1", "XDG_CACHE_HOME": str(run / "cache")}
    command = [args.python, "-B", "-m", "openjiuwen_agentichub.main"]
    outcomes = []
    for action in (["validate", str(stage)], ["pack", str(stage), "--output", str(run / "out")]):
        result = subprocess.run(command + action, cwd=run, env=env, capture_output=True, text=True, timeout=60)
        outcomes.append({"command": action[0], "exit": result.returncode})
        print(result.stdout + result.stderr)
        result.check_returncode()
    (packed,) = (run / "out").glob("*.zip")
    native_draft = run / "native.zip"
    with zipfile.ZipFile(native_draft, "w") as archive:
        for name, body in files.items():
            member = zipfile.ZipInfo(name, date_time=(2026, 11, 20, 0, 0, 0))
            member.external_attr = 0o100644 << 16
            archive.writestr(member, body)
    prefix = f"{SLUG}-{version}/"
    native = ASSET / "test-packages" / f"{SLUG}-{version}-native.zip"
    wrapped = ASSET / "release" / version / f"{SLUG}-{version}-agent-group.zip"
    for kind, draft, destination in (("native", native_draft, native), ("wrapped", packed, wrapped)):
        inner = "" if kind == "native" else prefix + SLUG + "/"
        extra = () if kind == "native" else (prefix + "plugin.yaml",)
        inspect(draft, inner, files, extra)
        destination.parent.mkdir(parents=True, exist_ok=True)
        retain_archive(draft, destination)
        inspect(destination, inner, files, extra)
        if extra:
            with zipfile.ZipFile(destination) as archive:
                assert archive.read(extra[0]) == outer.read_bytes()
    artifact = {
        "asset": SLUG, "type": "agent-group", "version": version, "task_id": info["task_id"],
        "tool": {"name": "official agentichub CLI", "version": "0.0.1", "commit": pin, "checks": outcomes},
        "payload_sha256": {name: digest(body) for name, body in files.items()}, "payload_equality": True,
        "artifacts": {
            kind: {"path": str(path.relative_to(ASSET)), "sha256": digest(path.read_bytes()),
                   "bytes": path.stat().st_size}
            for kind, path in (("native", native), ("wrapped", wrapped))
        }
    }
    (wrapped.parent / "artifact.json").write_text(json.dumps(artifact, ensure_ascii=False, indent=2) + "\n")
    print(json.dumps(artifact["artifacts"], ensure_ascii=False))


if __name__ == "__main__":
    main()
