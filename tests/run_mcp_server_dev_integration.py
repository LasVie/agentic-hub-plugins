"""Run real generated MCP servers and an official MCPB pack/unpack cycle.

Requires Python >=3.9, Node >=20 and npm on PATH.
Set MCP_DEV_NODE / MCP_DEV_NPM_CLI to use explicitly selected executables.
Installs integrity-locked npm packages in a temporary directory, not in the ZIP.
"""
from __future__ import annotations

import argparse
import json
import os
import shutil
import subprocess
import sys
import tempfile
import zipfile
from pathlib import Path

ROOT = Path(__file__).resolve().parents[1]


def main():
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument("--payload", type=Path, default=ROOT / "plugins/mcp-server-dev/mcp-server-dev")
    parser.add_argument("--workspace", type=Path)
    args = parser.parse_args()
    node = os.environ.get("MCP_DEV_NODE") or shutil.which("node")
    if not node:
        raise SystemExit("Node.js >=20 is required")
    npm = [node, os.environ["MCP_DEV_NPM_CLI"]] if os.environ.get("MCP_DEV_NPM_CLI") else [shutil.which("npm") or "npm"]
    if args.workspace:
        args.workspace.mkdir(parents=True, exist_ok=False)
        run(args.payload.resolve(), args.workspace.resolve(), node, npm)
    else:
        with tempfile.TemporaryDirectory(prefix="mcp-dev-functional-") as d:
            run(args.payload.resolve(), Path(d), node, npm)


def run(payload, work, node, npm):
    def command(argv, *, success=True):
        result = subprocess.run([str(x) for x in argv], cwd=work, text=True, stdout=subprocess.PIPE,
                                stderr=subprocess.STDOUT, timeout=180)
        print("$", " ".join(str(x) for x in argv), flush=True)
        print(result.stdout, end="", flush=True)
        if (result.returncode == 0) != success:
            raise RuntimeError(f"Unexpected exit {result.returncode}")
        return result.stdout

    env_info = {"python": sys.version.split()[0], "node": command([node, "--version"]).strip(),
                "npm": command(npm + ["--version"]).strip(), "plugin": "1.0.0"}
    print(json.dumps(env_info), flush=True)
    tool_dir = work / "tools"
    shutil.copytree(ROOT / "tests/mcp-dev-node-tools", tool_dir)
    install = ["ci", "--ignore-scripts", "--no-audit", "--no-fund", "--cache", work / "npm-cache",
               "--registry", "https://registry.npmjs.org"]
    command(npm + install + ["--prefix", tool_dir])
    modules = tool_dir / "node_modules"
    cli = modules / "@anthropic-ai/mcpb/dist/cli/cli.js"
    for kind in ("app", "mcpb"):
        project = work / kind
        command([sys.executable, payload / "scripts/devkit.py", "scaffold", "--kind", kind, "--output",
                 project, "--name", "tested-" + kind, "--author", "Vannes Wijaya"])
        command(npm + install + ["--prefix", project] + (["--omit=dev"] if kind == "mcpb" else []))
        for file in project.glob("*.mjs"):
            command([node, "--check", file])
        if kind == "app":
            command([node, project / "build.mjs"])
            app_license = project / "licenses/npm/_modelcontextprotocol_ext-apps@1.7.5/LICENSE"
            assert "licensing transition" in app_license.read_text(encoding="utf-8")
        else:
            command([node, project / "collect-licenses.mjs"])
        command([node, ROOT / "tests/mcp_server_dev_smoke.mjs", project, kind, modules])
    project = work / "mcpb"
    command([node, cli, "validate", project / "manifest.json"])
    invalid = work / "invalid-manifest.json"
    invalid.write_text('{"manifest_version":"0.4"}', encoding="utf-8")
    command([node, cli, "validate", invalid], success=False)
    archive = work / "tested.mcpb"
    command([node, cli, "pack", project, archive])
    with zipfile.ZipFile(archive) as z:
        names = z.namelist()
        assert all(not Path(n).is_absolute() and ".." not in Path(n).parts for n in names)
        for n in ("server.mjs", "manifest.json", "licenses/claude-plugins-official/LICENSE",
                  "node_modules/@modelcontextprotocol/sdk/LICENSE", "node_modules/zod/LICENSE"):
            assert n in names, n
        assert not any(n.startswith("node_modules/@anthropic-ai/mcpb/") for n in names)
        print("MCPB archive:", len(names), "files; no traversal; runtime dependency licenses present")
    relocated = work / "relocated"
    command([node, cli, "unpack", archive, relocated])
    command([node, ROOT / "tests/mcp_server_dev_smoke.mjs", relocated, "mcpb", modules])
    print("PASS: real App protocol, text fallback, invalid inputs, MCPB validate/pack/unpack/relocation")
    print("Host UI rendering, target-desktop install and Hub submission remain separate evidence.")


if __name__ == "__main__":
    main()
