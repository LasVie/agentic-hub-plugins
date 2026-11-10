#!/usr/bin/env python3
"""Verify supported WorkSwarm installation without chat/model calls.

Run with the existing isolated host's Python environment (websockets is required).
Only --install permits package import/install. This does not patch the host or
claim that its chat worker has loaded or invoked the native tools.
"""

from __future__ import annotations

import argparse
import asyncio
import contextlib
from datetime import datetime, timezone
import hashlib
import http.client
import importlib.metadata
import json
import os
from pathlib import Path
import sys
import tempfile
from urllib.request import ProxyHandler, build_opener
from urllib.parse import urlsplit
import uuid
import zipfile

from websockets.legacy.client import connect


SLUG = "offline-pipe-network-workbench"
DISPLAY_NAME = "离线管网水力工作台"
VERSION = "1.0.0"
sys.dont_write_bytecode = True


def sha(data: bytes) -> str:
    return hashlib.sha256(data).hexdigest()


def inventory(root: Path, exclude_plugin: str | None = None) -> dict[str, str]:
    result = {}
    for path in sorted(root.rglob("*")):
        relative = path.relative_to(root)
        if exclude_plugin and relative.parts[0] == exclude_plugin:
            continue
        if path.is_file():
            result[relative.as_posix()] = sha(path.read_bytes())
    return result


def archive_payload(path: Path) -> tuple[dict[str, str], dict]:
    """Read one native package, retaining every declared payload file hash."""
    with zipfile.ZipFile(path) as archive:
        names = [name for name in archive.namelist() if not name.endswith("/")]
        manifests = [name for name in names if name.split("/")[-1] == "manifest.json"]
        if len(manifests) != 1:
            raise ValueError("Expected exactly one native manifest.json")
        manifest_path = manifests[0]
        prefix = manifest_path[:-len("manifest.json")]
        if any(not name.startswith(prefix) for name in names):
            raise ValueError("ZIP contains files outside the native package")
        payload = {name[len(prefix):]: sha(archive.read(name)) for name in names}
        manifest = json.loads(archive.read(manifest_path))
    if manifest.get("id") != SLUG or manifest.get("version") != VERSION:
        raise ValueError("ZIP identity/version does not match this verification helper")
    return payload, manifest


async def rpc(port: int, method: str, params: dict | None = None):
    request_id = f"pipe-network-install-check-{uuid.uuid4().hex}"
    async with connect(
        f"ws://127.0.0.1:{port}/ws?user_id=pipe-network-package-verification",
        open_timeout=10,
        max_size=16 * 1024 * 1024,
    ) as websocket:
        await asyncio.wait_for(await websocket.ping(), 5)
        await websocket.send(json.dumps({
            "type": "req", "id": request_id, "method": method, "params": params or {},
        }))
        while True:
            response = json.loads(await asyncio.wait_for(websocket.recv(), 180))
            if response.get("id") == request_id:
                if not response.get("ok"):
                    raise RuntimeError(f"{method} failed: {response.get('payload')}")
                return response["payload"]


def package_summary(items: list[dict]) -> list[dict]:
    return [{"id": item.get("id"), "installed": item.get("installed"),
             "connection_state": item.get("connection_state")} for item in items]


async def verify_native_tools(payload: Path, host_root: Path) -> dict:
    """Public SDK resolution/invocation in this test process, not a chat worker."""
    previous_cwd = Path.cwd()
    with tempfile.TemporaryDirectory(prefix="pipe-network-sdk-", dir=host_root / "runtime") as directory:
        temporary = Path(directory).resolve()
        workspace = temporary / "workspace"
        workspace.mkdir()
        sdk_cwd = temporary / "sdk-cwd"
        sdk_cwd.mkdir()
        try:
            os.chdir(sdk_cwd)
            with contextlib.redirect_stdout(sys.stderr):
                from openjiuwen.core.foundation.tool import Tool
                from openjiuwen.harness.resources import load_plugin_package, resolve_plugin_parts
                from openjiuwen.harness.schema.build_context import BuildContext
                spec = load_plugin_package(payload / "manifest.json")
                context = BuildContext(language="cn", member_name="Cai Zhenze", project_dir=str(workspace),
                                       extras={"source_root": str(payload)})
                parts = resolve_plugin_parts(spec, context)
                assert spec.id == SLUG and len(parts.tools) == 1 and len(parts.skills) == 1
                assert not parts.mcps and not parts.rails and not parts.subagents
                tool = parts.tools[0]
                assert isinstance(tool, Tool) and tool.card.id == "pipe_network_workbench"
                assert Path(parts.skills[0].directory) == payload / "skills/pipe-network-workbench"
                assert "简体中文" in (payload / "skills/pipe-network-workbench/SKILL.md").read_text()
                arguments = {"workspace": str(workspace)}
                initial = await tool.invoke({**arguments, "action": "status"})
                assert initial["ok"] and not initial["running"] and list(workspace.iterdir()) == []
                denied = await tool.invoke({**arguments, "action": "start", "confirmed": False})
                assert denied["error"]["code"] == "confirmation_required" and list(workspace.iterdir()) == []
                started = await tool.invoke({**arguments, "action": "start", "confirmed": True})
                assert started["ok"] and started["running"] and started["version"] == VERSION, started
                try:
                    url = urlsplit(started["url"])
                    assert url.hostname == "127.0.0.1"
                    connection = http.client.HTTPConnection(url.hostname, url.port, timeout=3)
                    try:
                        connection.request("GET", url.path)
                        response = connection.getresponse()
                        body = response.read(200000).decode()
                        assert response.status == 200 and DISPLAY_NAME in body
                        assert "'unsafe-eval'" not in response.getheader("Content-Security-Policy")
                    finally:
                        connection.close()
                    again = await tool.invoke({**arguments, "action": "start", "confirmed": True})
                    assert again["reused"] and again["url"] == started["url"]
                    chunks = [chunk async for chunk in tool.stream({**arguments, "action": "status"})]
                    assert len(chunks) == 1 and chunks[0]["running"]
                finally:
                    stopped = await tool.invoke({**arguments, "action": "stop", "confirmed": True})
                    assert stopped["ok"] and not stopped["running"], stopped
                final = await tool.invoke({**arguments, "action": "status"})
                assert final["ok"] and not final["running"]
                # Leave only a separately owned, installed-tool-started workbench for browser QA.
                handoff = host_root / "runtime/installed-workbench-qa"
                handoff.mkdir(exist_ok=False)
                initial_handoff = await tool.invoke({"action":"status","workspace":str(handoff)})
                started_handoff = await tool.invoke({"action":"start","workspace":str(handoff),"confirmed":True})
                reused_handoff = await tool.invoke({"action":"start","workspace":str(handoff),"confirmed":True})
                status_handoff = await tool.invoke({"action":"status","workspace":str(handoff)})
                assert initial_handoff["ok"] and not initial_handoff["running"]
                assert started_handoff["ok"] and reused_handoff["reused"]
                assert started_handoff["url"] == reused_handoff["url"] == status_handoff["url"]
                (host_root / "runtime/workbench-tool-result.json").write_text(json.dumps({"workspace":str(handoff),"status_before":initial_handoff,"start":started_handoff,"reuse":reused_handoff,"status_after":status_handoff},ensure_ascii=False,indent=2))
            return {"passed": True, "openjiuwen_version": importlib.metadata.version("openjiuwen"),
                    "loader": "openjiuwen.harness.resources.load_plugin_package",
                    "resolver": "openjiuwen.harness.resources.resolve_plugin_parts",
                    "tool_id": "pipe_network_workbench", "chinese_skill_loaded": True,
                    "status_no_writes": True, "confirmation_rejected": True,
                    "start_reuse_stream_stop": True, "chinese_entry_http_200": True,
                    "page_csp_no_eval": True, "model_calls": 0,
                    "scope": "Public native SDK in separate verification process; not actual chat dispatch."}
        finally:
            os.chdir(previous_cwd)


async def main(args) -> None:
    host_root = args.host_root.resolve()
    marker = json.loads((host_root / "runtime/prepared.json").read_text())
    if marker.get("plugin_id") != SLUG or marker.get("data_dir") != str(host_root / "data"):
        raise ValueError("Refusing a host instance not explicitly prepared for this plugin")
    local_plugins = host_root / "data/agent/workspace/plugins/plugin_packages/local"
    report = {
        "verified_at": datetime.now(timezone.utc).isoformat(),
        "plugin_id": SLUG, "display_name": DISPLAY_NAME, "version": VERSION,
        "frontend_url": f"http://127.0.0.1:{args.frontend_port}/",
        "backend_websocket_url": f"ws://127.0.0.1:{args.backend_port}/ws",
        "host_root": str(host_root), "model_requests": 0,
        "dedicated_instance": True,
        "host_source_commit": marker.get("source_commit"),
        "host_code_changes": False, "initial_setup_correction": "Task-owned first startup logs retained; corrected isolated gateway port and disabled image probes via supported config. Other services unchanged.",
        "verification_scope": "Supported running-backend import/install/catalog and payload integrity only.",
        "native_tool_execution_through_chat_worker": "Not exercised; requires separate manual conversation testing.",
        "connection_state_limitation": "For a package without MCP connectors, connected mirrors installed and does not prove native-tool loading or execution.",
        "sdk_invocation": "Not performed by this helper; report separately if tested.",
        "supported_interface_evidence": {
            "host_paths_relative_to_source": {
                "jiuwenswarm/channels/web/frontend/src/services/pluginPackagesApi.ts:145": "show; importLocal at154; install at159.",
                "jiuwenswarm/common/schema/message.py:406": "Supported plugin package WS request-method declarations.",
                "jiuwenswarm/server/runtime/extension_package_manager.py:4126": "import_plugin_package; install_plugin_package at4308.",
                "jiuwenswarm/server/runtime/extension_package_manager.py:639": "Native-only connected state mirrors installed.",
                "jiuwenswarm/server/runtime/agent_adapter/interface_deep.py:2909": "Selected chat plugins load through DeepAgent.load_plugin at2936.",
            },
            "sdk_paths_relative_to_openjiuwen": {
                "harness/deep_agent.py:2196": "Public DeepAgent.load_plugin API.",
                "harness/resources/extension_resolver.py:103": "resolve_plugin_parts resolves manifest-declared native tools and skills.",
            },
            "unsupported_test_path": "No generic native Tool.invoke request is declared in the inspected WorkSwarm WS schema. No test endpoint, monkey-patch, or fake-model conversation is used.",
        },
    }
    before_config = await rpc(args.frontend_port, "config.get")
    before_config_hash = sha(json.dumps(before_config, sort_keys=True).encode())
    before_others = inventory(local_plugins, SLUG)
    catalog_before = (await rpc(args.frontend_port, "plugin_packages.list", {"filter": "mine"}))["packages"]
    report["catalog_before"] = package_summary(catalog_before)
    report["config_sha256_before"] = before_config_hash
    report["other_plugin_files_before"] = len(before_others)
    failure = None
    try:
        report["prior_host_sdk_evidence"] = "Adapted maintained geojson-simplification-lab/verify_workswarm.py supported APIs; this instance has independent source/dependencies/data/runtime/cache and only this plugin is imported."
        opener = build_opener(ProxyHandler({}))
        with opener.open(report["frontend_url"], timeout=10) as response:
            report["frontend_http"] = response.status
            assert response.status == 200
        await rpc(args.backend_port, "plugin_packages.list", {"filter": "mine"})
        report["websocket_proxy_ping_pong"] = True
        report["websocket_direct_ping_pong"] = True
        if args.native_zip:
            native_zip = args.native_zip.resolve()
            actual_zip_hash = sha(native_zip.read_bytes())
            if args.expected_sha256 and actual_zip_hash != args.expected_sha256:
                raise ValueError("Native test ZIP hash does not match expected hash")
            payload, _manifest = archive_payload(native_zip)
            report["native_zip"] = {"path": str(native_zip), "sha256": actual_zip_hash,
                                    "payload_files": len(payload)}
            installed_root = local_plugins / SLUG
            if args.install and not installed_root.exists():
                imported = await rpc(args.frontend_port, "plugin_packages.import_local", {"path": str(native_zip)})
                assert imported.get("id") == SLUG, imported
                report["import_local"] = True
                await rpc(args.frontend_port, "plugin_packages.install", {"id": SLUG})
                report["install"] = True
            elif args.install:
                report["installation_reused"] = True
            if installed_root.exists():
                installed = inventory(installed_root)
                payload_installed = {key: value for key, value in installed.items()
                                     if "__pycache__" not in Path(key).parts and not key.endswith(".pyc")}
                report["payload_matches_zip"] = payload_installed == payload
                report["payload_sha256"] = payload
                assert report["payload_matches_zip"], "Installed package differs from exact test ZIP"
                details = await rpc(args.frontend_port, "plugin_packages.show", {"id": SLUG})
                card = details.get("package", details)
                report["installed_card"] = {key: card.get(key) for key in ("id", "version", "displayName", "installed", "connection_state")}
                assert card.get("installed") and card.get("version") == VERSION
                assert card.get("displayName", {}).get("zh") == DISPLAY_NAME
                direct = await rpc(args.backend_port, "plugin_packages.show", {"id": SLUG})
                assert direct.get("package", direct).get("installed")
                if args.verify_native_tools:
                    report["sdk_invocation"] = await verify_native_tools(installed_root, host_root)
                    installed_after = {key: value for key, value in inventory(installed_root).items()
                                       if "__pycache__" not in Path(key).parts and not key.endswith(".pyc")}
                    assert installed_after == payload, "SDK invocation changed installed payload"
                    report["sdk_payload_unchanged"] = True
            elif args.install:
                raise AssertionError("Installed package directory is absent")
            elif args.verify_native_tools:
                raise AssertionError("Native SDK checks require an installed exact package")
        elif args.install:
            raise ValueError("--install requires --native-zip")
        elif args.verify_native_tools:
            raise ValueError("--verify-native-tools requires --native-zip and an installed exact package")
    except Exception as error:
        failure = error
        report["error"] = f"{type(error).__name__}: {error}"
    finally:
        after_config = await rpc(args.frontend_port, "config.get")
        after_hash = sha(json.dumps(after_config, sort_keys=True).encode())
        after_others = inventory(local_plugins, SLUG)
        report["config_sha256_after"] = after_hash
        report["model_config_unchanged"] = before_config_hash == after_hash
        report["other_plugin_payloads_unchanged"] = before_others == after_others
        report["catalog_after"] = package_summary((await rpc(args.frontend_port, "plugin_packages.list", {"filter": "mine"}))["packages"])
        old_catalog = sorted((item for item in report["catalog_before"] if item["id"] != SLUG), key=lambda item: item["id"])
        new_catalog = sorted((item for item in report["catalog_after"] if item["id"] != SLUG), key=lambda item: item["id"])
        report["other_plugin_catalog_unchanged"] = old_catalog == new_catalog
        source_record = json.loads((host_root / "runtime/source-copy.json").read_text())
        source_expected = source_record["source_inventory"]
        source_root = host_root / "source"
        source_actual = {path.relative_to(source_root).as_posix(): sha(path.read_bytes())
                         for path in source_root.rglob("*") if path.is_file()
                         and not any(part in {".venv", "node_modules", "__pycache__", ".vite", ".vite-temp", ".DS_Store"}
                                     for part in path.relative_to(source_root).parts)}
        report["host_source_files_unchanged"] = source_actual == source_expected
        report["source_copy_inventory_sha256"] = source_record["inventory_sha256"]
        report["passed"] = (failure is None and report["model_config_unchanged"]
                            and report["other_plugin_payloads_unchanged"] and report["other_plugin_catalog_unchanged"]
                            and report["host_source_files_unchanged"])
        args.output.write_text(json.dumps(report, ensure_ascii=False, indent=2) + "\n", encoding="utf-8")
        print(json.dumps({key: value for key, value in report.items() if key != "payload_sha256"}, ensure_ascii=False, indent=2))
    if failure:
        raise failure
    assert report["passed"], "Other plugin payloads or model settings changed during verification"


if __name__ == "__main__":
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument("--host-root", type=Path, required=True)
    parser.add_argument("--frontend-port", type=int, default=6431)
    parser.add_argument("--backend-port", type=int, default=29431)
    parser.add_argument("--native-zip", type=Path)
    parser.add_argument("--expected-sha256")
    parser.add_argument("--install", action="store_true")
    parser.add_argument("--verify-native-tools", action="store_true")
    parser.add_argument("--output", type=Path, default=Path(__file__).with_name("host-verification.json"))
    asyncio.run(main(parser.parse_args()))
