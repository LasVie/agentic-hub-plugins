#!/usr/bin/env python3
"""Exercise actual DeepAgent registration and Tool.invoke without model calls.

This standalone SDK process does not exercise the running WorkSwarm chat worker.
The payload must be the extracted Chinese test package, not a second source copy.
"""
from __future__ import annotations

import argparse
import asyncio
from datetime import datetime, timezone
import hashlib
import importlib.metadata
import json
import os
from pathlib import Path
import sys
from urllib.request import ProxyHandler, build_opener
import uuid

SLUG = "solid-mesh-workbench"
VERSION = "1.0.0"
DISPLAY_NAME = "立体网格布尔工坊"
os.environ.update(HF_HUB_OFFLINE="1", TRANSFORMERS_OFFLINE="1", OTEL_SDK_DISABLED="true",
                  PYTHONDONTWRITEBYTECODE="1")
sys.dont_write_bytecode = True


def guard_network(event, arguments):
    if event == "socket.connect":
        address = arguments[1]
        if not isinstance(address, tuple) or address[0] not in {"127.0.0.1", "::1"}:
            raise RuntimeError("SDK verification forbids external network connections")


sys.addaudithook(guard_network)


def sanitized(value):
    if isinstance(value, dict):
        return {key: ({"count": len(item)} if key in {"positions", "triangles", "mergeFromVert", "mergeToVert"}
                      and isinstance(item, list) else {"bytes": len(item.encode()), "sha256": hashlib.sha256(item.encode()).hexdigest()}
                      if key == "obj" and isinstance(item, str) else sanitized(item))
                for key, item in value.items() if key not in {"url", "token", "session_id"}}
    if isinstance(value, list):
        return [sanitized(item) for item in value]
    return value


def fixture(operation, offset=1):
    return {"schema": "solid-mesh-workbench/v1", "units": "mm", "operation": operation,
            "a": {"kind": "box", "size": [2, 2, 2]},
            "b": {"kind": "box", "size": [2, 2, 2], "translate": [offset, 0, 0]}}


async def run(args):
    workspace = args.workspace.resolve()
    workspace.mkdir(parents=True, exist_ok=False)
    # Put SDK logs and configuration in this explicit test workspace before import.
    os.chdir(workspace)
    os.environ.update(JIUWENSWARM_HOME=str(workspace / "home"), XDG_CACHE_HOME=str(workspace / "cache"))
    from openjiuwen.core.runner import Runner
    from openjiuwen.core.session.agent import create_agent_session
    from openjiuwen.core.single_agent.schema.agent_card import AgentCard
    from openjiuwen.core.sys_operation import LocalWorkConfig, OperationMode, SysOperationCard
    from openjiuwen.harness.deep_agent import DeepAgent
    from openjiuwen.harness.rails.skills.skill_use_rail import SkillUseRail
    from openjiuwen.harness.schema.config import DeepAgentConfig
    from openjiuwen.harness.workspace.workspace import Workspace

    operation_id = "solid-mesh-sdk-" + uuid.uuid4().hex
    payload = args.payload.resolve()
    report = {"verified_at": datetime.now(timezone.utc).isoformat(), "plugin_id": SLUG,
              "display_name": DISPLAY_NAME, "version": VERSION,
              "scope": "Standalone actual DeepAgent.load_plugin and registered Tool.invoke; not running WorkSwarm chat-worker execution.",
              "openjiuwen_version": importlib.metadata.version("openjiuwen"),
              "python_version": sys.version.split()[0], "payload": str(payload), "workspace": str(workspace),
              "model_requests": 0, "external_network": "Denied by Python audit hook; bundled engine has no network imports.",
              "records": [], "passed": False}
    report["payload_sha256"] = {path.relative_to(payload).as_posix(): hashlib.sha256(path.read_bytes()).hexdigest()
                                for path in sorted(payload.rglob("*")) if path.is_file()
                                and "__pycache__" not in path.parts and path.suffix != ".pyc"}
    agent = record = session = None
    registered = {}
    started = False
    failure = None

    async def invoke(name, inputs, expected_ok=True):
        result = await registered[name].invoke(inputs, session=session)
        assert isinstance(result, dict), type(result)
        assert result.get("version") == VERSION, sanitized(result)
        assert result.get("ok") is expected_ok, sanitized(result)
        report["records"].append({"tool": name, "inputs": inputs, "result": sanitized(result)})
        return result

    lifecycle_args = {"workspace": str(workspace), "node_path": str(args.node_path.resolve())}
    try:
        Runner.resource_mgr.add_sys_operation(SysOperationCard(id=operation_id, mode=OperationMode.LOCAL,
            work_config=LocalWorkConfig(work_dir=str(workspace))))
        operation = Runner.resource_mgr.get_sys_operation(operation_id)
        assert operation is not None
        agent = DeepAgent(AgentCard(id=operation_id, name="立体网格 SDK 验证", description="仅本地插件验证，不调用模型"))
        agent.configure(DeepAgentConfig(workspace=Workspace(root_path=str(workspace / "agent-workspace")),
            sys_operation=operation, language="cn", auto_create_workspace=True, enable_task_loop=False,
            enable_skill_discovery=True, rails=[SkillUseRail(skills_dir=[], skill_mode="all", include_tools=False)]))
        await agent.ensure_initialized()
        record = await agent.load_plugin(str(payload))
        report["registered_refs"] = [{"kind": ref.kind.value, "identity": ref.identity} for ref in record.refs]
        session = create_agent_session(session_id=operation_id, card=agent.card, close_stream_on_post_run=False)
        await session.pre_run(inputs={"query": "本地立体网格工具验证，不调用模型。"})
        for ref in record.refs:
            if ref.kind.value == "tool":
                registered[ref.identity.removesuffix("_" + operation_id)] = Runner.resource_mgr.get_tool(ref.identity, session=session)
        assert set(registered) == {"solid_mesh_workbench", "calculate_solid_mesh"}, list(registered)
        assert all(registered.values())
        report["registered_tools"] = sorted(registered)
        status = await invoke("solid_mesh_workbench", {**lifecycle_args, "action": "status"})
        assert not status["running"]
        denied = await invoke("solid_mesh_workbench", {**lifecycle_args, "action": "start"}, False)
        assert isinstance(denied["error"], str) and any("\u4e00" <= char <= "\u9fff" for char in denied["error"])
        for operation, expected in (("union", 12), ("difference", 4), ("intersection", 4)):
            result = await invoke("calculate_solid_mesh", {"project": fixture(operation), "node_path": str(args.node_path.resolve())})
            assert abs(result["metrics"]["volume_mm3"] - expected) < 1e-9, result["metrics"]
            assert result["metrics"]["triangles"] > 0 and result["obj"]
        empty = await invoke("calculate_solid_mesh", {"project": fixture("intersection", 5), "node_path": str(args.node_path.resolve())})
        assert empty["metrics"]["empty"] and empty["metrics"]["volume_mm3"] == 0 and empty["metrics"]["bounds"] is None
        invalid = fixture("union")
        invalid["script"] = "fetch('https://example.invalid/')"
        rejected = await invoke("calculate_solid_mesh", {"project": invalid, "node_path": str(args.node_path.resolve())}, False)
        assert isinstance(rejected["error"], str) and any("\u4e00" <= char <= "\u9fff" for char in rejected["error"])
        opened = await invoke("solid_mesh_workbench", {**lifecycle_args, "action": "start", "confirmed": True})
        started = True
        assert opened["running"]
        status = await invoke("solid_mesh_workbench", {**lifecycle_args, "action": "status"})
        assert status["running"] and status["session_id"] == opened["session_id"]
        report["start_status_same_session"] = True
        opener = build_opener(ProxyHandler({}))
        with opener.open(opened["url"], timeout=10) as response:
            assert response.status == 200 and DISPLAY_NAME in response.read().decode("utf-8")
            report["local_ui_http"] = response.status
        stopped = await invoke("solid_mesh_workbench", {**lifecycle_args, "action": "stop", "confirmed": True})
        assert not stopped["running"]
        restarted = await invoke("solid_mesh_workbench", {**lifecycle_args, "action": "start", "confirmed": True})
        assert restarted["running"] and restarted["session_id"] != opened["session_id"]
        report["immediate_restart_new_session"] = True
        stopped = await invoke("solid_mesh_workbench", {**lifecycle_args, "action": "stop", "confirmed": True})
        assert not stopped["running"]
        status = await invoke("solid_mesh_workbench", {**lifecycle_args, "action": "status"})
        assert not status["running"]
        report["stopped_service_verified"] = True
        started = False
        report["invocations"] = len(report["records"])
    except Exception as error:
        failure = error
        report["error"] = f"{type(error).__name__}: {error}"
    finally:
        try:
            if started:
                await invoke("solid_mesh_workbench", {**lifecycle_args, "action": "stop", "confirmed": True})
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
        after_hashes = {path.relative_to(payload).as_posix(): hashlib.sha256(path.read_bytes()).hexdigest()
                        for path in sorted(payload.rglob("*")) if path.is_file()
                        and "__pycache__" not in path.parts and path.suffix != ".pyc"}
        report["payload_unchanged"] = after_hashes == report["payload_sha256"]
        if not report["payload_unchanged"]:
            failure = failure or AssertionError("Payload changed during SDK verification")
        report["passed"] = failure is None
        args.output.write_text(json.dumps(report, ensure_ascii=False, indent=2) + "\n", encoding="utf-8")
        print(json.dumps({key: value for key, value in report.items() if key not in {"records", "payload_sha256"}}, ensure_ascii=False, indent=2))
    if failure:
        raise failure


if __name__ == "__main__":
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument("payload", type=Path)
    parser.add_argument("--workspace", type=Path, required=True)
    parser.add_argument("--node-path", type=Path, required=True)
    parser.add_argument("--output", type=Path, default=Path(__file__).with_name("sdk-verification.json"))
    args = parser.parse_args()
    args.payload, args.output = args.payload.resolve(), args.output.resolve()
    asyncio.run(run(args))
