#!/usr/bin/env python3
"""Verify an exact installed Chinese package through the real public SDK.

This standalone process registers and invokes native tools without model calls.
It does not exercise dispatch through the running WorkSwarm chat worker.
Adapted from Cai Zhenze’s maintained offline-allocation-workbench verification helper; no host or SDK patch.
"""
from __future__ import annotations

import argparse
import asyncio
import copy
from datetime import datetime, timezone
import hashlib
import importlib.metadata
import ipaddress
import json
import os
from pathlib import Path
import re
import stat
import sys
from urllib.request import ProxyHandler, build_opener
import uuid
import zipfile

SLUG = "offline-steam-properties-workbench"
VERSION = "1.0.0"
DISPLAY_NAME = "离线水与蒸汽物性工作台"
TASK_ID = "AH-20261116-offline-steam-properties-workbench"
sys.dont_write_bytecode = True


def guard_network(event, arguments):
    host = None
    if event == "socket.getaddrinfo":
        host = arguments[0]
    elif event in {"socket.connect", "socket.sendto"}:
        address = arguments[-1]
        if isinstance(address, tuple):
            host = address[0]
    if host is None or host in {"localhost", ""}:
        return
    try:
        allowed = ipaddress.ip_address(host).is_loopback
    except (ValueError, TypeError):
        allowed = False
    if not allowed:
        raise RuntimeError("SDK verification forbids non-loopback networking")


sys.addaudithook(guard_network)


def sha(data):
    return hashlib.sha256(data).hexdigest()


def inventory(root):
    result = {}
    for path in sorted(root.rglob("*")):
        if path.is_symlink():
            raise ValueError("Payload inventory contains a symlink")
        if path.is_file() and "__pycache__" not in path.parts and path.suffix not in {".pyc", ".pyo"}:
            result[path.relative_to(root).as_posix()] = sha(path.read_bytes())
    return result


def archive_payload(path):
    with zipfile.ZipFile(path) as archive:
        entries = archive.infolist()
        names = [item.filename for item in entries if not item.is_dir()]
        if (len(names) != len(set(names)) or len(entries) > 1000
                or sum(item.file_size for item in entries) > 512 * 1024 * 1024
                or any(Path(name).is_absolute() or ".." in Path(name).parts or "\\" in name for name in names)
                or any(stat.S_ISLNK(item.external_attr >> 16) for item in entries)):
            raise ValueError("Unsafe, duplicate or oversized native ZIP paths")
        if [name for name in names if Path(name).name == "manifest.json"] != ["manifest.json"]:
            raise ValueError("Expected exactly one native manifest at ZIP root")
        manifest = json.loads(archive.read("manifest.json"))
        if manifest.get("id") != SLUG or manifest.get("version") != VERSION:
            raise ValueError("Native ZIP identity/version differs")
        return {name: sha(archive.read(name)) for name in names}


def sanitized(value):
    if isinstance(value, dict):
        return {key: sanitized(item) for key, item in value.items()
                if key not in {"url", "token", "session_id"}}
    if isinstance(value, list):
        return [sanitized(item) for item in value]
    return value


def fixture():
    return {"schema": "steam-properties/v1", "name": "SDK 中文常压水验证",
            "state": {"pair": "PQ", "pressure_pa": 101325, "quality": 0},
            "sweep": {"variable": "pressure_pa", "start": 10000, "end": 2000000, "points": 25}}


async def run(args):
    payload = args.payload.resolve(strict=True)
    if not re.fullmatch(r"[0-9a-f]{64}", args.expected_sha256):
        raise ValueError("Expected ZIP SHA-256 must be explicit")
    if sha(args.native_zip.read_bytes()) != args.expected_sha256:
        raise ValueError("Native ZIP differs from the exact test package")
    frozen = archive_payload(args.native_zip)
    if inventory(payload) != frozen:
        raise ValueError("Installed payload differs from the exact native ZIP")
    workspace = args.workspace.resolve()
    if workspace == payload or payload in workspace.parents:
        raise ValueError("Test state must be outside the installed payload")
    if args.output == payload or payload in args.output.parents:
        raise ValueError("Verification output must be outside the installed payload")
    workspace.mkdir(parents=True, exist_ok=False)
    os.chdir(workspace)
    os.environ.update(HF_HUB_OFFLINE="1", TRANSFORMERS_OFFLINE="1", OTEL_SDK_DISABLED="true",
                      PYTHONDONTWRITEBYTECODE="1", JIUWENSWARM_HOME=str(workspace / "home"),
                      XDG_CACHE_HOME=str(workspace / "cache"))
    from openjiuwen.core.runner import Runner
    from openjiuwen.core.session.agent import create_agent_session
    from openjiuwen.core.single_agent.schema.agent_card import AgentCard
    from openjiuwen.core.sys_operation import LocalWorkConfig, OperationMode, SysOperationCard
    from openjiuwen.harness.deep_agent import DeepAgent
    from openjiuwen.harness.rails.skills.skill_use_rail import SkillUseRail
    from openjiuwen.harness.schema.config import DeepAgentConfig
    from openjiuwen.harness.workspace.workspace import Workspace

    operation_id = "steam-sdk-" + uuid.uuid4().hex
    report = {"verified_at": datetime.now(timezone.utc).isoformat(), "task_id": TASK_ID,
              "plugin_id": SLUG, "display_name": DISPLAY_NAME, "version": VERSION,
              "native_zip_sha256": args.expected_sha256, "payload": str(payload),
              "workspace": str(workspace), "openjiuwen_version": importlib.metadata.version("openjiuwen"),
              "python_version": sys.version.split()[0], "model_requests": 0,
              "scope": "Standalone actual DeepAgent.load_plugin and registered Tool.invoke; running chat-worker dispatch is untested.",
              "external_network": "Denied by Python audit hook; CoolProp worker has its own OS network sandbox.",
              "payload_sha256": frozen, "records": [], "passed": False}
    agent = record = session = None
    registered = {}
    started = False
    failure = None

    async def invoke(name, inputs, expected_ok=True):
        result = await registered[name].invoke(inputs, session=session)
        assert isinstance(result, dict) and result.get("version") == VERSION, sanitized(result)
        assert result.get("ok") is expected_ok, sanitized(result)
        report["records"].append({"tool": name, "inputs": inputs, "result": sanitized(result)})
        return result

    lifecycle = {"workspace": str(workspace)}
    try:
        Runner.resource_mgr.add_sys_operation(SysOperationCard(
            id=operation_id, mode=OperationMode.LOCAL,
            work_config=LocalWorkConfig(work_dir=str(workspace))))
        operation = Runner.resource_mgr.get_sys_operation(operation_id)
        assert operation is not None
        agent = DeepAgent(AgentCard(id=operation_id, name="水蒸气 SDK 验证", description="仅本地插件验证，不调用模型"))
        agent.configure(DeepAgentConfig(
            workspace=Workspace(root_path=str(workspace / "agent-workspace")),
            sys_operation=operation, language="cn", auto_create_workspace=True,
            enable_task_loop=False, enable_skill_discovery=True,
            rails=[SkillUseRail(skills_dir=[], skill_mode="all", include_tools=False)]))
        await agent.ensure_initialized()
        record = await agent.load_plugin(str(payload))
        report["registered_refs"] = [{"kind": ref.kind.value, "identity": ref.identity} for ref in record.refs]
        session = create_agent_session(session_id=operation_id, card=agent.card, close_stream_on_post_run=False)
        await session.pre_run(inputs={"query": "本地水蒸气工具验证，不调用模型。"})
        for ref in record.refs:
            if ref.kind.value == "tool":
                name = ref.identity.removesuffix("_" + operation_id)
                registered[name] = Runner.resource_mgr.get_tool(ref.identity, session=session)
        assert set(registered) == {"steam_workbench", "calculate_water_properties"}, list(registered)
        assert all(registered.values())
        report["registered_tools"] = sorted(registered)
        assert any(ref.kind.value == "skill" for ref in record.refs), "Declared Chinese Skill was not discovered"
        report["declared_skill_discovered"] = True
        status = await invoke("steam_workbench", {**lifecycle, "action": "status"})
        assert not status["running"]
        denied = await invoke("steam_workbench", {**lifecycle, "action": "start"}, False)
        assert any("\u4e00" <= c <= "\u9fff" for c in denied["error"]["message"])
        baseline = await invoke("calculate_water_properties", {"project": fixture()})
        assert baseline["engine"] == {"name": "CoolProp", "version": "8.0.0", "backend": "HEOS", "fluid": "Water"}
        assert abs(baseline["state"]["temperature_k"] - 373.1243) < .02
        assert abs(baseline["state"]["density_kg_m3"] - 958.3675) < 1
        assert abs(baseline["saturation"]["latent_heat_j_kg"] - 2256471.6) < 300
        assert len(baseline["sweep"]) == 25
        mixture = fixture()
        mixture["state"]["quality"] = .5
        wet = await invoke("calculate_water_properties", {"project": mixture})
        assert wet["input"] == mixture and wet["state"]["quality"] == .5
        expected_h = (wet["saturation"]["liquid"]["enthalpy_j_kg"] + wet["saturation"]["vapor"]["enthalpy_j_kg"]) / 2
        assert abs(wet["state"]["enthalpy_j_kg"] - expected_h) < 1e-3
        superheated = fixture()
        superheated["state"] = {"pair": "PT", "pressure_pa": 101325, "temperature_k": 473.15}
        hot = await invoke("calculate_water_properties", {"project": superheated})
        assert hot["state"]["quality"] is None and hot["state"]["phase"] == "气态"
        assert 2800000 < hot["state"]["enthalpy_j_kg"] < 3000000
        temperature = fixture()
        temperature["state"] = {"pair": "TQ", "temperature_k": 373.15, "quality": 1}
        temperature["sweep"] = {"variable": "temperature_k", "start": 300, "end": 620, "points": 25}
        saturated = await invoke("calculate_water_properties", {"project": temperature})
        assert abs(saturated["state"]["pressure_pa"] - 101417.9967) < 50
        assert saturated["state"]["quality"] == 1
        for invalid in [{**fixture(), "script": "do not execute"},
                        {**fixture(), "state": {"pair": "PQ", "pressure_pa": 10**400, "quality": 0}}]:
            rejected = await invoke("calculate_water_properties", {"project": invalid}, False)
            assert any("\u4e00" <= c <= "\u9fff" for c in rejected["error"]["message"])
        opened = await invoke("steam_workbench", {**lifecycle, "action": "start", "confirmed": True})
        started = True
        assert opened["running"]
        reused = await invoke("steam_workbench", {**lifecycle, "action": "start", "confirmed": True})
        assert reused["running"] and reused["url"] == opened["url"] and not reused["started"]
        status = await invoke("steam_workbench", {**lifecycle, "action": "status"})
        assert status["running"] and status["session_id"] == opened["session_id"]
        report["start_reuse_status_same_session"] = True
        stream = [value async for value in registered["steam_workbench"].stream(
            {**lifecycle, "action": "status"}, session=session)]
        assert len(stream) == 1 and stream[0]["running"]
        report["records"].append({"tool": "steam_workbench.stream", "result": sanitized(stream[0])})
        opener = build_opener(ProxyHandler({}))
        with opener.open(opened["url"], timeout=10) as response:
            assert response.status == 200 and DISPLAY_NAME in response.read().decode("utf-8")
            report["local_ui_http"] = response.status
        stopped = await invoke("steam_workbench", {**lifecycle, "action": "stop", "confirmed": True})
        assert not stopped["running"]
        restarted = await invoke("steam_workbench", {**lifecycle, "action": "start", "confirmed": True})
        assert restarted["running"] and restarted["session_id"] != opened["session_id"]
        report["immediate_restart_new_session"] = True
        stopped = await invoke("steam_workbench", {**lifecycle, "action": "stop", "confirmed": True})
        assert not stopped["running"]
        status = await invoke("steam_workbench", {**lifecycle, "action": "status"})
        assert not status["running"]
        started = False
        report["stopped_service_verified"] = True
        report["invocations"] = len(report["records"])
    except Exception as error:
        failure = error
        report["error"] = f"{type(error).__name__}: {error}"
    finally:
        try:
            if started:
                await invoke("steam_workbench", {**lifecycle, "action": "stop", "confirmed": True})
            if session:
                await session.post_run()
            if record:
                unloaded = await agent.unload_extension(record)
                report["unloaded_refs"] = len(unloaded)
                assert len(unloaded) == len(record.refs)
            Runner.resource_mgr.remove_sys_operation(operation_id)
            if agent and getattr(agent, "shutdown", None):
                await agent.shutdown()
        except Exception as error:
            failure = failure or error
            report["cleanup_error"] = f"{type(error).__name__}: {error}"
        report["payload_unchanged"] = inventory(payload) == frozen
        if not report["payload_unchanged"]:
            failure = failure or AssertionError("Installed payload changed during SDK verification")
        report["passed"] = failure is None
        args.output.parent.mkdir(parents=True, exist_ok=True)
        args.output.write_text(json.dumps(report, ensure_ascii=False, indent=2) + "\n", encoding="utf-8")
        print(json.dumps({key: value for key, value in report.items()
                          if key not in {"records", "payload_sha256"}}, ensure_ascii=False, indent=2))
    if failure:
        raise failure


if __name__ == "__main__":
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument("payload", type=Path)
    parser.add_argument("--native-zip", type=Path, required=True)
    parser.add_argument("--expected-sha256", required=True)
    parser.add_argument("--workspace", type=Path, required=True)
    parser.add_argument("--output", type=Path, required=True)
    args = parser.parse_args()
    args.payload, args.native_zip = args.payload.resolve(), args.native_zip.resolve()
    args.output = args.output.resolve()
    asyncio.run(run(args))
