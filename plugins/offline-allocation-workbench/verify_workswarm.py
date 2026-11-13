#!/usr/bin/env python3
"""Verify native local import/install against this task's isolated WorkSwarm.

Only --install authorizes package writes. No chat/model requests, Hub calls,
host modifications or generic native-tool RPC endpoints are used.
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

import psutil
from websockets.legacy.client import connect

from verify_sdk import SLUG, VERSION, DISPLAY_NAME, TASK_ID, archive_payload, inventory


def sha(data):
    return hashlib.sha256(data).hexdigest()


async def rpc(port, method, params=None):
    request_id = "allocation-install-" + uuid.uuid4().hex
    async with connect(f"ws://127.0.0.1:{port}/ws?user_id=allocation-package-verification",
                       open_timeout=15, max_size=16 * 1024 * 1024) as websocket:
        await asyncio.wait_for(await websocket.ping(), 5)
        await websocket.send(json.dumps({"type": "req", "id": request_id,
                                         "method": method, "params": params or {}}))
        while True:
            response = json.loads(await asyncio.wait_for(websocket.recv(), 120))
            if response.get("id") == request_id:
                if not response.get("ok"):
                    raise RuntimeError(f"{method}: {response.get('payload')}")
                return response["payload"]


def catalog_summary(items):
    return sorted([{"id": item.get("id"), "installed": item.get("installed"),
                    "connection_state": item.get("connection_state")} for item in items],
                  key=lambda item: item["id"])


async def run(args):
    root = args.host_root.resolve(strict=True)
    marker = json.loads((root / ".task-owner.json").read_text())
    if marker.get("task_id") != TASK_ID:
        raise ValueError("Host marker belongs to another task")
    if marker.get("ports", {}).get("frontend") != args.frontend_port:
        raise ValueError("Frontend port differs from the owned host marker")
    if marker.get("ports", {}).get("web") != args.web_port:
        raise ValueError("Web port differs from the owned host marker")
    records = json.loads((root / "runtime/pids.json").read_text())
    for name in ("backend", "web"):
        record = records[name]
        command = record["command"]
        if command[command.index("--dotenv") + 1] != str(root / "runtime/task.env"):
            raise ValueError("Service dotenv is outside this task")
        process = psutil.Process(record["pid"])
        if process.cmdline()[1:] != command[1:] or Path(process.cwd()).resolve() != root / "cwd":
            raise ValueError("Recorded PID/command/cwd differs from the owned live process")
    if sha(args.native_zip.read_bytes()) != args.expected_sha256:
        raise ValueError("Native ZIP SHA-256 differs from the selected test package")
    frozen = archive_payload(args.native_zip)
    local = root / "data/domain/agent/workspace/plugins/plugin_packages/local"
    installed_root = local / SLUG
    before_others = {key: value for key, value in inventory(local).items()
                     if not key.startswith(SLUG + "/")}
    before_config = await rpc(args.frontend_port, "config.get")
    before_config_hash = sha(json.dumps(before_config, sort_keys=True).encode())
    catalog_before = catalog_summary((await rpc(args.frontend_port, "plugin_packages.list",
                                               {"filter": "mine"}))["packages"])
    report = {"verified_at": datetime.now(timezone.utc).isoformat(), "task_id": TASK_ID,
              "plugin_id": SLUG, "display_name": DISPLAY_NAME, "version": VERSION,
              "host_commit": marker["host_commit"], "host_root": str(root),
              "native_zip_sha256": args.expected_sha256, "native_payload_files": len(frozen),
              "frontend_url": f"http://127.0.0.1:{args.frontend_port}/",
              "model_requests": 0, "host_code_changes": False,
              "dependency_scope": marker["dependency_scope"],
              "scope": "Running local native import/install/catalog; standalone SDK execution is recorded separately; running chat-worker dispatch is untested.",
              "connection_state_limitation": "For a no-MCP plugin, connected mirrors installation and does not prove native tool execution.",
              "catalog_before": catalog_before, "payload_sha256": frozen,
              "passed": False}
    failure = None
    try:
        opener = build_opener(ProxyHandler({}))
        with opener.open(report["frontend_url"], timeout=15) as response:
            assert response.status == 200
            report["frontend_http"] = response.status
        await rpc(args.web_port, "plugin_packages.list", {"filter": "mine"})
        report["direct_and_proxy_websocket_ping_pong"] = True
        if args.install:
            if installed_root.exists():
                if inventory(installed_root) != frozen:
                    raise ValueError("Existing installed payload differs; preserve and investigate")
                report["matching_installation_reused"] = True
            else:
                imported = await rpc(args.frontend_port, "plugin_packages.import_local",
                                     {"path": str(args.native_zip)})
                assert imported.get("id") == SLUG, imported
                report["supported_local_import"] = True
                await rpc(args.frontend_port, "plugin_packages.install", {"id": SLUG})
                report["supported_local_install"] = True
        if not installed_root.is_dir():
            raise AssertionError("Native package is not installed")
        assert inventory(installed_root) == frozen, "Installed payload differs from exact native ZIP"
        report["installed_payload_matches_zip"] = True
        report["installed_payload"] = str(installed_root)
        detail = await rpc(args.frontend_port, "plugin_packages.show", {"id": SLUG})
        card = detail.get("package", detail)
        report["installed_card"] = {key: card.get(key) for key in
                                    ("id", "version", "displayName", "installed", "connection_state", "tools", "skills")}
        assert card.get("installed") and card.get("version") == VERSION, card
        assert card.get("displayName", {}).get("zh") == DISPLAY_NAME, card
        direct = await rpc(args.web_port, "plugin_packages.show", {"id": SLUG})
        assert direct.get("package", direct).get("installed")
    except Exception as error:
        failure = error
        report["error"] = f"{type(error).__name__}: {error}"
    finally:
        after_config = await rpc(args.frontend_port, "config.get")
        after_others = {key: value for key, value in inventory(local).items()
                        if not key.startswith(SLUG + "/")}
        after_catalog = catalog_summary((await rpc(args.frontend_port, "plugin_packages.list",
                                                  {"filter": "mine"}))["packages"])
        report["model_config_unchanged"] = sha(json.dumps(after_config, sort_keys=True).encode()) == before_config_hash
        report["other_plugin_payloads_unchanged"] = before_others == after_others
        report["other_plugin_catalog_unchanged"] = (
            [item for item in catalog_before if item["id"] != SLUG]
            == [item for item in after_catalog if item["id"] != SLUG])
        report["catalog_after"] = after_catalog
        report["passed"] = failure is None and all(report[key] for key in
            ("model_config_unchanged", "other_plugin_payloads_unchanged", "other_plugin_catalog_unchanged"))
        args.output.parent.mkdir(parents=True, exist_ok=True)
        args.output.write_text(json.dumps(report, ensure_ascii=False, indent=2) + "\n", encoding="utf-8")
        print(json.dumps({key: value for key, value in report.items() if key != "payload_sha256"},
                         ensure_ascii=False, indent=2))
    if failure:
        raise failure
    assert report["passed"], "Unrelated configuration or plugin data changed"


if __name__ == "__main__":
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument("--host-root", type=Path, required=True)
    parser.add_argument("--native-zip", type=Path, required=True)
    parser.add_argument("--expected-sha256", required=True)
    parser.add_argument("--frontend-port", type=int, default=6457)
    parser.add_argument("--web-port", type=int, default=29457)
    parser.add_argument("--install", action="store_true")
    parser.add_argument("--output", type=Path, required=True)
    args = parser.parse_args()
    args.native_zip, args.output = args.native_zip.resolve(), args.output.resolve()
    asyncio.run(run(args))
