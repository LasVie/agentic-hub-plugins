#!/usr/bin/env python3
"""MCP development companion: explicit routing and non-overwriting scaffolds."""
from __future__ import annotations

import argparse
import json
import re
import shutil
import sys
import tempfile
from pathlib import Path

VERSION = "1.0.1"
ROOT = Path(__file__).resolve().parents[1]
BUILDER_ID = "4c94938898ed4d3580593e5535f2315b"
BUILDER_URL = "https://agentichub.openjiuwen.com/assets/" + BUILDER_ID
SLUG = re.compile(r"[a-z][a-z0-9]*(?:-[a-z0-9]+)*\Z")


def plan(spec: dict) -> dict:
    keys = {"local_access", "interactive_ui", "prototype"}
    if not isinstance(spec, dict) or set(spec) != keys:
        raise ValueError("spec must contain exactly local_access, interactive_ui, prototype")
    if any(type(spec[key]) is not bool for key in keys):
        raise ValueError("all spec values must be JSON booleans")
    local, ui, prototype = (spec[k] for k in ("local_access", "interactive_ui", "prototype"))
    skills = ["build-mcp-app"] if ui else []
    if local and not prototype:
        skills.append("build-mcpb")
    return {
        "plugin_version": VERSION,
        "transport": "stdio" if local or prototype else "streamable-http",
        "distribution": "mcpb" if local and not prototype else "prototype" if prototype else "remote",
        "skills": skills,
        "base_development_asset": {"id": BUILDER_ID, "url": BUILDER_URL},
        "next": "Use MCP Builder for base server/auth; use companion skills for UI and local packaging.",
        "limits": ["Generated examples use stdio; remote deployment/auth belongs to MCP Builder.",
                   "MCPB example requires Node.js >=20; it does not embed a runtime.",
                   "UI rendering requires an MCP Apps capable host and a separate host test."]
    }


def scaffold(kind: str, output: Path, name: str, author: str) -> dict:
    if not SLUG.fullmatch(name) or len(name) > 64:
        raise ValueError("name must be a lowercase slug of at most 64 characters")
    if not author.strip() or len(author) > 128:
        raise ValueError("author must contain 1..128 characters")
    if kind not in {"app", "mcpb"}:
        raise ValueError("kind must be app or mcpb")
    output = output.absolute()
    if output.exists() or output.is_symlink():
        raise ValueError("output must not exist; existing projects are never overwritten")
    if not output.parent.is_dir():
        raise ValueError("output parent must exist")
    with tempfile.TemporaryDirectory(prefix="mcp-dev-", dir=output.parent) as tmp:
        stage = Path(tmp) / "project"
        shutil.copytree(ROOT / "templates" / kind, stage)
        shutil.copy2(ROOT / "templates/collect-licenses.mjs", stage / "collect-licenses.mjs")
        for path in stage.rglob("*"):
            if path.is_file():
                path.write_text(path.read_text(encoding="utf-8").replace("__PROJECT_NAME__", name), encoding="utf-8")
        if kind == "mcpb":
            manifest = {
                "manifest_version": "0.4", "name": name, "version": "0.1.0",
                "description": "Read-only bounded addition demo; adapt before production use.",
                "author": {"name": author},
                "server": {"type": "node", "entry_point": "server.mjs", "mcp_config": {
                    "command": "node", "args": ["${__dirname}/server.mjs"]}},
                "compatibility": {"runtimes": {"node": ">=20"}}
            }
            (stage / "manifest.json").write_text(json.dumps(manifest, ensure_ascii=False, indent=2) + "\n", encoding="utf-8")
        shutil.copytree(ROOT / "licenses", stage / "licenses")
        shutil.copy2(ROOT / "THIRD_PARTY_NOTICES.md", stage / "THIRD_PARTY_NOTICES.md")
        if output.exists() or output.is_symlink():
            raise ValueError("output appeared during generation; refusing to replace it")
        stage.rename(output)
    return {"plugin_version": VERSION, "kind": kind, "project": str(output),
            "name": name, "generated_version": "0.1.0", "runtime": "Node.js >=20",
            "commands": ["npm ci --ignore-scripts", "npm run build", "node server.mjs"] if kind == "app"
                        else ["npm ci --ignore-scripts --omit=dev", "node collect-licenses.mjs", "mcpb validate manifest.json", "mcpb pack"],
            "license_note": "Review rights for your generated code and installed dependencies before distribution."}


def main() -> None:
    p = argparse.ArgumentParser(description=__doc__)
    p.add_argument("--version", action="version", version=VERSION)
    sub = p.add_subparsers(dest="command", required=True)
    route = sub.add_parser("plan")
    route.add_argument("spec", type=Path)
    new = sub.add_parser("scaffold")
    new.add_argument("--kind", choices=["app", "mcpb"], required=True)
    new.add_argument("--output", type=Path, required=True)
    new.add_argument("--name", required=True)
    new.add_argument("--author", required=True)
    args = p.parse_args()
    try:
        if args.command == "plan":
            if args.spec.stat().st_size > 16_384:
                raise ValueError("spec exceeds 16 KiB")
            result = plan(json.loads(args.spec.read_text(encoding="utf-8")))
        else:
            result = scaffold(args.kind, args.output, args.name, args.author)
        print(json.dumps(result, ensure_ascii=False, indent=2))
    except (ValueError, OSError) as exc:
        print(f"ERROR: {exc}", file=sys.stderr)
        raise SystemExit(2)


if __name__ == "__main__":
    main()
