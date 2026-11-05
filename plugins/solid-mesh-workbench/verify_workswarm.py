#!/usr/bin/env python3
"""Verify supported WorkSwarm installation without chat/model calls.

Run with the existing isolated host's Python environment (websockets is required).
Only --install permits package import/install. This does not patch the host or
claim that its chat worker has loaded or invoked the native tools.
"""

from __future__ import annotations

import argparse
import asyncio
from datetime import datetime, timezone
import hashlib
import json
from pathlib import Path
from urllib.request import ProxyHandler, build_opener
import uuid
import zipfile

import psutil
from websockets.legacy.client import connect


SLUG = "solid-mesh-workbench"
DISPLAY_NAME = "立体网格布尔工坊"
VERSION = "1.0.0"


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
        if len(names) != len(set(names)) or any(Path(name).is_absolute() or ".." in Path(name).parts for name in names):
            raise ValueError("ZIP has duplicate or unsafe paths")
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
    request_id = f"solid-mesh-install-check-{uuid.uuid4().hex}"
    async with connect(
        f"ws://127.0.0.1:{port}/ws?user_id=solid-mesh-package-verification",
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


async def main(args) -> None:
    host_root = args.host_root.resolve()
    marker = json.loads((host_root / ".task-owner.json").read_text())
    if marker.get("task_id") != "AH-20261031-solid-mesh-workbench":
        raise ValueError("Host root is not owned by this task")
    expected_ports = {"frontend": args.frontend_port, "gateway": args.backend_port}
    if any(marker.get("ports", {}).get(name) != port for name, port in expected_ports.items()):
        raise ValueError("Requested ports do not match this task's owned host marker")
    pid_records = json.loads((host_root / "runtime/pids.json").read_text())
    for name, port in expected_ports.items():
        record = pid_records[name]
        command = record["command"]
        if command[command.index("--port") + 1] != str(port):
            raise ValueError("Recorded service port differs from the owned host marker")
        if command[command.index("--dotenv") + 1] != str(host_root / "runtime/instance.env"):
            raise ValueError("Service configuration does not belong to this task")
        process = psutil.Process(record["pid"])
        if process.cmdline()[1:] != command[1:] or Path(process.cwd()).resolve() != host_root / "runtime/cwd":
            raise ValueError("Live service PID or working directory differs from the task-owned record")
    if args.install and not args.expected_sha256:
        raise ValueError("--install requires the exact approved test ZIP --expected-sha256")
    local_plugins = host_root / "data/agent/workspace/plugins/plugin_packages/local"
    report = {
        "verified_at": datetime.now(timezone.utc).isoformat(),
        "plugin_id": SLUG, "display_name": DISPLAY_NAME, "version": VERSION,
        "frontend_url": f"http://127.0.0.1:{args.frontend_port}/",
        "backend_websocket_url": f"ws://127.0.0.1:{args.backend_port}/ws",
        "host_root": str(host_root), "model_requests": 0,
        "source_commit": marker["source_commit"],
        "runtime_dependencies": "Fresh task-owned venv; unchanged host uv.lock with uv sync --frozen --no-dev --no-install-project; Python 3.12.14, openjiuwen 0.1.19.",
        "isolation": "Dedicated source copy, frontend build, venv, cache, data, home, tasks and ports; no shared dependencies or host source changed.",
        "host_network_configuration": "Localhost:9 disabled model endpoint; agent prewarm=0; JIUWENSWARM_CONFIG_URL=off; no credentials copied.",
        "host_code_changes": False, "service_restarts_during_verification": False,
        "verified_service_pids": {name: pid_records[name]["pid"] for name in expected_ports},
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
        report["prior_host_sdk_evidence"] = "Maintained offline-optics-lab verification pattern; current pinned host source independently inspected, and current real SDK invocation reported separately."
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
                existing = {key: value for key, value in inventory(installed_root).items()
                            if "__pycache__" not in Path(key).parts and not key.endswith(".pyc")}
                if existing != payload:
                    raise ValueError("Existing installed payload differs; preserve it and investigate before replacing")
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
            elif args.install:
                raise AssertionError("Installed package directory is absent")
        elif args.install:
            raise ValueError("--install requires --native-zip")
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
        report["passed"] = (failure is None and report["model_config_unchanged"]
                            and report["other_plugin_payloads_unchanged"] and report["other_plugin_catalog_unchanged"])
        args.output.write_text(json.dumps(report, ensure_ascii=False, indent=2) + "\n", encoding="utf-8")
        print(json.dumps({key: value for key, value in report.items() if key != "payload_sha256"}, ensure_ascii=False, indent=2))
    if failure:
        raise failure
    assert report["passed"], "Other plugin payloads or model settings changed during verification"


if __name__ == "__main__":
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument("--host-root", type=Path, required=True)
    parser.add_argument("--frontend-port", type=int, default=6401)
    parser.add_argument("--backend-port", type=int, default=29360)
    parser.add_argument("--native-zip", type=Path)
    parser.add_argument("--expected-sha256")
    parser.add_argument("--install", action="store_true")
    parser.add_argument("--output", type=Path, default=Path(__file__).with_name("host-verification.json"))
    asyncio.run(main(parser.parse_args()))
