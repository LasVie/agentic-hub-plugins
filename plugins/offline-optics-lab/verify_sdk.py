#!/usr/bin/env python3
"""Standalone real DeepAgent registration/invocation check; no model/chat calls.

This is a separate SDK subprocess, not a call through the running WorkSwarm
chat worker. Only the explicit plugin-test workspace is used for writes.
"""

from __future__ import annotations

import argparse
import asyncio
from datetime import datetime, timezone
import hashlib
import json
import os
from pathlib import Path
import sys
from urllib.request import ProxyHandler, build_opener
import uuid

os.environ.update(HF_HUB_OFFLINE="1", TRANSFORMERS_OFFLINE="1",
                  OTEL_SDK_DISABLED="true", PYTHONDONTWRITEBYTECODE="1")
sys.dont_write_bytecode = True


def guard_network(event, arguments):
    if event == "socket.connect":
        address = arguments[1]
        if not isinstance(address, tuple) or address[0] not in {"127.0.0.1", "::1"}:
            raise RuntimeError("SDK verification forbids external network connections")


sys.addaudithook(guard_network)

from openjiuwen.core.runner import Runner
from openjiuwen.core.session.agent import create_agent_session
from openjiuwen.core.single_agent.schema.agent_card import AgentCard
from openjiuwen.core.sys_operation import LocalWorkConfig, OperationMode, SysOperationCard
from openjiuwen.harness.deep_agent import DeepAgent
from openjiuwen.harness.rails.skills.skill_use_rail import SkillUseRail
from openjiuwen.harness.schema.config import DeepAgentConfig
from openjiuwen.harness.workspace.workspace import Workspace




def sanitized(value):
    if isinstance(value, dict):
        return {key: ({"count": len(item), "first": sanitized(item[0]), "last": sanitized(item[-1])}
                      if key == "samples" and isinstance(item, list) and item else sanitized(item))
                for key, item in value.items()
                if key not in {"url", "token", "session_id"}}
    if isinstance(value, list):
        return [sanitized(item) for item in value]
    return value


async def run(args):
    workspace = args.workspace.resolve()
    workspace.mkdir(parents=True, exist_ok=False)
    operation_id = "offline-optics-sdk-" + uuid.uuid4().hex
    report = {
        "verified_at": datetime.now(timezone.utc).isoformat(),
        "scope": "Standalone SDK DeepAgent.load_plugin plus registered Tool.invoke; not running WorkSwarm chat-worker execution.",
        "plugin_id": "offline-optics-lab", "version": "1.0.0",
        "payload": str(args.payload.resolve()), "workspace": str(workspace),
        "model_requests": 0, "external_network": "Denied by audit hook in this verification subprocess.",
        "records": [], "passed": False,
    }
    payload = args.payload.resolve()
    report["payload_sha256"] = {
        path.relative_to(payload).as_posix(): hashlib.sha256(path.read_bytes()).hexdigest()
        for path in sorted(payload.rglob("*")) if path.is_file()
        and "__pycache__" not in path.relative_to(payload).parts and path.suffix != ".pyc"
    }
    agent = None
    record = None
    session = None
    tools = {}
    started = False
    failure = None

    async def invoke(name, inputs, expected_ok=True):
        result = await tools[name].invoke(inputs, session=session)
        assert isinstance(result, dict), type(result)
        assert result.get("version") == "1.0.0", sanitized(result)
        assert result.get("ok") is expected_ok, sanitized(result)
        report["records"].append({"tool": name, "inputs": inputs, "result": sanitized(result)})
        return result

    try:
        Runner.resource_mgr.add_sys_operation(SysOperationCard(
            id=operation_id, mode=OperationMode.LOCAL,
            work_config=LocalWorkConfig(work_dir=str(workspace)),
        ))
        operation = Runner.resource_mgr.get_sys_operation(operation_id)
        assert operation is not None
        agent = DeepAgent(AgentCard(id=operation_id, name="Optics SDK verifier",
                                    description="Local native-plugin verification without model calls"))
        agent.configure(DeepAgentConfig(
            workspace=Workspace(root_path=str(workspace / "agent-workspace")),
            sys_operation=operation, language="cn", auto_create_workspace=True,
            enable_task_loop=False, enable_skill_discovery=True,
            rails=[SkillUseRail(skills_dir=[], skill_mode="all", include_tools=False)],
        ))
        await agent.ensure_initialized()
        record = await agent.load_plugin(str(args.payload.resolve()))
        report["registered_refs"] = [{"kind": ref.kind.value, "identity": ref.identity} for ref in record.refs]
        session = create_agent_session(session_id=operation_id, card=agent.card, close_stream_on_post_run=False)
        await session.pre_run(inputs={"query": "Local optics plugin verification; no model invocation"})
        for ref in record.refs:
            if ref.kind.value == "tool":
                tool = Runner.resource_mgr.get_tool(ref.identity, session=session)
                assert tool is not None, ref.identity
                # DeepAgent appends its agent ID to resource registry identities.
                # Resolve the actual registered instance, then key by plugin ID.
                tools[ref.identity.removesuffix("_" + operation_id)] = tool
        assert set(tools) == {"local_optics_lab", "simulate_optical_scene"}, list(tools)
        report["registered_tools"] = sorted(tools)
        status = await invoke("local_optics_lab", {"action": "status", "workspace": str(workspace)})
        assert not status["running"]
        denied = await invoke("local_optics_lab", {"action": "start", "workspace": str(workspace)}, False)
        assert denied["error"]["code"] == "confirmation_required"
        examples = json.loads((payload / "engine/examples.json").read_text())
        for example in examples:
            simulation = await invoke("simulate_optical_scene", {"scene": example["scene"]})
            assert simulation["segment_count"] > 0
            assert simulation["detectors"] and simulation["detectors"][0]["hits"] > 0
            if example["id"] == "lens":
                assert abs(abs(simulation["detectors"][0]["power"]) - 1) < 1e-9
        rejected = await invoke("simulate_optical_scene", {"scene": {"schema_version": 1, "title": "拒绝联网字段", "objects": [], "backgroundImage": "https://example.invalid/a"}}, False)
        assert rejected["error"]["code"] == "unsupported_field"
        opened = await invoke("local_optics_lab", {"action": "start", "workspace": str(workspace), "confirmed": True})
        started = True
        assert opened["running"]
        status = await invoke("local_optics_lab", {"action": "status", "workspace": str(workspace)})
        assert status["running"] and status["session_id"] == opened["session_id"]
        report["start_status_same_session"] = True
        # Inspect the actual plugin-owned browser service; never publish its token.
        opener = build_opener(ProxyHandler({}))
        with opener.open(opened["url"], timeout=10) as response:
            html = response.read().decode("utf-8")
            assert response.status == 200 and "离线光学实验室" in html
            report["local_ui_http"] = response.status
        stopped = await invoke("local_optics_lab", {"action": "stop", "workspace": str(workspace), "confirmed": True})
        assert not stopped["running"]
        restarted = await invoke("local_optics_lab", {"action": "start", "workspace": str(workspace), "confirmed": True})
        assert restarted["running"] and restarted["session_id"] != opened["session_id"]
        report["immediate_restart_new_session"] = True
        stopped_again = await invoke("local_optics_lab", {"action": "stop", "workspace": str(workspace), "confirmed": True})
        assert not stopped_again["running"]
        for _ in range(20):
            final_status = await invoke("local_optics_lab", {"action": "status", "workspace": str(workspace)})
            if final_status.get("ok") and not final_status.get("running"):
                break
            await asyncio.sleep(.1)
        assert final_status.get("ok") and not final_status.get("running"), sanitized(final_status)
        report["stopped_service_verified"] = True
        started = False
        report["invocations"] = len(report["records"])
    except Exception as error:
        failure = error
        report["error"] = f"{type(error).__name__}: {error}"
    finally:
        if started:
            try:
                await invoke("local_optics_lab", {"action": "stop", "workspace": str(workspace), "confirmed": True})
            except Exception as error:
                report["cleanup_error"] = f"{type(error).__name__}: {error}"
                failure = failure or error
        if session:
            await session.post_run()
        if record:
            unloaded = await agent.unload_extension(record)
            report["unloaded_refs"] = len(unloaded)
            assert len(unloaded) == len(record.refs)
        Runner.resource_mgr.remove_sys_operation(operation_id)
        if agent and getattr(agent, "shutdown", None):
            await agent.shutdown()
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
    asyncio.run(run(parser.parse_args()))
