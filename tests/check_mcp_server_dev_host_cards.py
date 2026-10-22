"""Exercise native card helpers from a user-provided host checkout, in memory.

No host source is bundled or copied. This read-only check does not install the
plugin into the user's running host and does not replace visual user testing.
"""
from __future__ import annotations

import argparse
import ast
import base64
import hashlib
import json
import logging
import re
import subprocess
import zipfile
from pathlib import Path, PurePosixPath
from typing import Any

import yaml


HELPERS = {
    "_read_package_manifest", "_i18n", "_read_readme_details",
    "_read_package_text", "_parse_skill_frontmatter_text", "_skill_id_from_spec",
    "_map_skills_with_reader", "_map_skills", "_map_class_entries",
    "_map_mcps_with_reader", "_map_mcps", "_connector_names_from_manifest",
    "_package_connection_state", "_resolve_package_avatar", "_build_list_card",
    "_build_show_card", "unready_connectors", "_zip_package_root",
}


def main():
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument("--host-root", required=True, type=Path)
    parser.add_argument("--payload", required=True, type=Path)
    parser.add_argument("--legacy-payload", type=Path)
    parser.add_argument("--local-zip", type=Path)
    parser.add_argument("--node", default="node")
    args = parser.parse_args()
    backend = args.host_root / "jiuwenswarm/server/runtime/extension_package_manager.py"
    frontend = args.host_root / "jiuwenswarm/channels/web/frontend/src/types/pluginPackage.ts"
    tree = ast.parse(backend.read_text(encoding="utf-8"))
    nodes = [ast.ImportFrom(module="__future__", names=[ast.alias(name="annotations")], level=0)]
    for item in tree.body:
        if isinstance(item, ast.FunctionDef) and item.name in HELPERS:
            nodes.append(item)
        elif isinstance(item, ast.Assign) and any(
            isinstance(target, ast.Name) and target.id == "_AVATAR_MIME" for target in item.targets
        ):
            nodes.append(item)
    assert HELPERS == {item.name for item in nodes if isinstance(item, ast.FunctionDef)}
    namespace = dict(Path=Path, PurePosixPath=PurePosixPath, Any=Any, base64=base64,
                     json=json, re=re, yaml=yaml, logger=logging.getLogger(__name__))
    exec(compile(ast.fix_missing_locations(ast.Module(body=nodes, type_ignores=[])),
                 str(backend), "exec"), namespace)
    match = re.search(r"export function localizedText\([^)]*\): string \{([^}]+)\}",
                      frontend.read_text(encoding="utf-8"))
    assert match, "Native frontend localization function not found"
    javascript = """
const data = JSON.parse(process.argv[1]);
const localize = new Function('value', 'language', data.body);
const result = {};
for (const lang of ['zh-CN', 'en-US']) {
  const title = localize(data.card.displayName, lang);
  const description = localize(data.card.displayDescription, lang);
  result[lang] = {title: title || '', description: description || '',
    initial: (Array.from(String(title || '').trim() || '?')[0] || '?').toUpperCase()};
}
console.log(JSON.stringify(result));
"""
    results = {}
    for label, payload in [("fixed", args.payload), ("legacy", args.legacy_payload)]:
        if payload is None:
            continue
        results[label] = {}
        for kind in ("list", "show"):
            function = namespace["_build_" + kind + "_card"]
            card = function(payload, package_type="plugin", source="local",
                            marketplace=None, installed=True)
            rendered = json.loads(subprocess.check_output(
                [args.node, "-e", javascript, json.dumps({"body": match[1], "card": card})], text=True))
            for language, text in rendered.items():
                if label == "fixed":
                    assert text["title"] == "mcp-server-dev", (kind, language, text)
                    assert text["description"].strip(), (kind, language, text)
                    assert text["initial"] == "M", (kind, language, text)
                else:
                    assert text == {"title": "", "description": "", "initial": "?"}, text
            if kind == "show":
                assert {skill["id"] for skill in card["skills"]} == {
                    "mcp-dev-route", "build-mcp-app", "build-mcpb"}
            results[label][kind] = rendered
    results["host_sources"] = {str(path.relative_to(args.host_root)): hashlib.sha256(path.read_bytes()).hexdigest()
                               for path in (backend, frontend)}
    if args.local_zip:
        with zipfile.ZipFile(args.local_zip) as archive:
            paths = [PurePosixPath(name) for name in archive.namelist()]
            assert namespace["_zip_package_root"](paths, "plugin") == PurePosixPath()
            for name in archive.namelist():
                assert archive.read(name) == (args.payload / name).read_bytes(), name
        results["native_zip_root_and_extracted_payload"] = "passed"
    results["limitations"] = "Native helper/frontend localization check; no running-host install or visual UI assertion."
    print(json.dumps(results, ensure_ascii=False, indent=2))


if __name__ == "__main__":
    main()
