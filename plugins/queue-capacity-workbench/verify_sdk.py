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

SLUG = "queue-capacity-workbench"
VERSION = "1.0.1"
DISPLAY_NAME = "离线排队容量实验台"
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
        return {key: sanitized(item) for key, item in value.items() if key not in {"url", "token", "session_id"}}
    if isinstance(value, list):
        return [sanitized(item) for item in value]
    return value


def fixture():
    return {"schema": "queue-capacity-workbench/v1", "name": "SDK 中文场景", "units": "minutes",
            "capacities": [1, 2], "jobs": [{"id": f"作业{i+1}", "arrival": i, "service": 4} for i in range(4)]}


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

    operation_id = "queue-capacity-sdk-" + uuid.uuid4().hex
    payload = args.payload.resolve()
    report = {"verified_at": datetime.now(timezone.utc).isoformat(), "plugin_id": SLUG,
              "display_name": DISPLAY_NAME, "version": VERSION,
              "scope": "Standalone actual DeepAgent.load_plugin and registered Tool.invoke; not running WorkSwarm chat-worker execution.",
              "openjiuwen_version": importlib.metadata.version("openjiuwen"),
              "python_version": sys.version.split()[0], "payload": str(payload), "workspace": str(workspace),
              "model_requests": 0, "external_network": "Denied by Python audit hook; calculation worker denies socket activity.",
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

    lifecycle_args = {"workspace": str(workspace)}
    try:
        Runner.resource_mgr.add_sys_operation(SysOperationCard(id=operation_id, mode=OperationMode.LOCAL,
            work_config=LocalWorkConfig(work_dir=str(workspace))))
        operation = Runner.resource_mgr.get_sys_operation(operation_id)
        assert operation is not None
        agent = DeepAgent(AgentCard(id=operation_id, name="排队容量 SDK 验证", description="仅本地插件验证，不调用模型"))
        agent.configure(DeepAgentConfig(workspace=Workspace(root_path=str(workspace / "agent-workspace")),
            sys_operation=operation, language="cn", auto_create_workspace=True, enable_task_loop=False,
            enable_skill_discovery=True, rails=[SkillUseRail(skills_dir=[], skill_mode="all", include_tools=False)]))
        await agent.ensure_initialized()
        record = await agent.load_plugin(str(payload))
        report["registered_refs"] = [{"kind": ref.kind.value, "identity": ref.identity} for ref in record.refs]
        session = create_agent_session(session_id=operation_id, card=agent.card, close_stream_on_post_run=False)
        await session.pre_run(inputs={"query": "本地排队容量工具验证，不调用模型。"})
        for ref in record.refs:
            if ref.kind.value == "tool":
                registered[ref.identity.removesuffix("_" + operation_id)] = Runner.resource_mgr.get_tool(ref.identity, session=session)
        assert set(registered) == {"queue_capacity_workbench", "simulate_queue_capacity"}, list(registered)
        assert all(registered.values())
        report["registered_tools"] = sorted(registered)
        status = await invoke("queue_capacity_workbench", {**lifecycle_args, "action": "status"})
        assert not status["running"]
        denied = await invoke("queue_capacity_workbench", {**lifecycle_args, "action": "start"}, False)
        assert isinstance(denied["error"], str) and any("\u4e00" <= char <= "\u9fff" for char in denied["error"])
        assert "simpy" not in sys.modules
        computed = await invoke("simulate_queue_capacity", {"project": fixture()})
        assert computed["engine"] == "SimPy 4.1.2"
        assert [r["metrics"]["mean_wait"] for r in computed["runs"]] == [4.5, 1]
        assert [r["metrics"]["completion_time"] for r in computed["runs"]] == [16, 9]
        assert "simpy" not in sys.modules
        report["simpy_not_imported_into_host"] = True
        invalid = fixture()
        invalid["script"] = "do not execute"
        rejected = await invoke("simulate_queue_capacity", {"project": invalid}, False)
        assert any("\u4e00" <= char <= "\u9fff" for char in rejected["error"])
        opened = await invoke("queue_capacity_workbench", {**lifecycle_args, "action": "start", "confirmed": True})
        started = True
        assert opened["running"]
        status = await invoke("queue_capacity_workbench", {**lifecycle_args, "action": "status"})
        assert status["running"] and status["session_id"] == opened["session_id"]
        report["start_status_same_session"] = True
        opener = build_opener(ProxyHandler({}))
        with opener.open(opened["url"], timeout=10) as response:
            assert response.status == 200 and DISPLAY_NAME in response.read().decode("utf-8")
            report["local_ui_http"] = response.status
        stopped = await invoke("queue_capacity_workbench", {**lifecycle_args, "action": "stop", "confirmed": True})
        assert not stopped["running"]
        restarted = await invoke("queue_capacity_workbench", {**lifecycle_args, "action": "start", "confirmed": True})
        assert restarted["running"] and restarted["session_id"] != opened["session_id"]
        report["immediate_restart_new_session"] = True
        stopped = await invoke("queue_capacity_workbench", {**lifecycle_args, "action": "stop", "confirmed": True})
        assert not stopped["running"]
        status = await invoke("queue_capacity_workbench", {**lifecycle_args, "action": "status"})
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
                await invoke("queue_capacity_workbench", {**lifecycle_args, "action": "stop", "confirmed": True})
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
    parser.add_argument("--output", type=Path, default=Path(__file__).with_name("sdk-verification.json"))
    args = parser.parse_args()
    args.payload, args.output = args.payload.resolve(), args.output.resolve()
    asyncio.run(run(args))
