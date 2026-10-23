"""Exercise the actual host loader/resolver and native Exa tool invocations."""
import argparse
import asyncio
import hashlib
import importlib.metadata
import json
import os
from pathlib import Path
import sys
import tempfile
from contextlib import contextmanager
from unittest.mock import patch

parser = argparse.ArgumentParser(description=__doc__)
parser.add_argument("--sdk-root", type=Path, required=True)
parser.add_argument("--host-root", type=Path)
parser.add_argument("--payload", type=Path, required=True)
parser.add_argument("--archive", type=Path)
parser.add_argument("--live", action="store_true")
parser.add_argument("--output", type=Path, required=True)
args = parser.parse_args()
payload = args.payload.resolve()
archive = args.archive.resolve() if args.archive else None
output = args.output.resolve()
sys.path.insert(0, str(args.sdk_root.resolve()))
if args.host_root:
    sys.path.insert(0, str(args.host_root.resolve()))

@contextmanager
def host_home():
    original_cwd = Path.cwd()
    with tempfile.TemporaryDirectory(prefix="exa-plugin-host-") as temp:
        try:
            yield temp
        finally:
            # Windows cannot delete a temporary log directory with open sinks.
            from openjiuwen.core.common.logging import LogManager
            LogManager.reset()
            from loguru import logger
            logger.remove()
            import logging
            logging.shutdown()
            os.chdir(original_cwd)

async def main():
    # Select a temporary home before importing host state/log managers.
    with host_home() as temp:
        os.environ["JIUWENSWARM_DATA_DIR"] = temp
        os.chdir(temp)
        from openjiuwen.core.common.logging.log_config import configure_log_config, get_log_config_snapshot
        settings = get_log_config_snapshot()
        settings["log_path"] = str(Path(temp) / "logs")
        configure_log_config(settings)
        from openjiuwen.harness.resources.extension_loader import load_plugin_package
        from openjiuwen.harness.resources.extension_resolver import resolve_plugin_parts
        from openjiuwen.harness.schema.build_context import BuildContext

        installed = None
        manager = None
        if archive:
            from jiuwenswarm.common.utils import get_user_workspace_dir
            assert get_user_workspace_dir().resolve() == Path(temp).resolve()
            from jiuwenswarm.server.runtime import extension_package_manager as manager
            imported = manager.import_plugin_package({"path": str(archive)})
            assert imported["id"] == "exa-deep-research"
            manager.install_plugin_package(imported)
            assert manager.is_plugin_allowed(imported["id"])
            installed = manager.resolve_plugin_dir(imported["id"])
            assert installed.resolve().is_relative_to(Path(temp).resolve())

        current = installed or payload
        native = load_plugin_package(current / "manifest.json")
        parts = resolve_plugin_parts(native, BuildContext(language="en"))
        assert len(parts.tools) == 4 and len(parts.skills) == 2
        # Native tools manage their own authenticated MCP sessions: no duplicate
        # host MCP registration is needed or claimed.
        assert not native.mcps
        names = [type(tool).__name__ for tool in parts.tools]
        result = {"plugin_version": json.loads((current / "manifest.json").read_text(encoding="utf-8"))["version"],
                  "host_load": "passed", "tools": names, "skills": len(parts.skills),
                  "runtime": {"python": sys.version.split()[0], "mcp": importlib.metadata.version("mcp"), "jsonschema": importlib.metadata.version("jsonschema")},
                  "loader_sha256": hashlib.sha256((args.sdk_root / "openjiuwen/harness/resources/extension_loader.py").read_bytes()).hexdigest()}
        from openjiuwen.core.single_agent.schema.agent_card import AgentCard
        from openjiuwen.harness.factory import create_deep_agent
        from openjiuwen.harness.rails import SkillUseRail
        expected = {"exa_search", "exa_fetch", "exa_search_advanced", "exa_research"}
        result["main_agent"] = {}
        for progressive in (False, True):
            agent = create_deep_agent(
                None, card=AgentCard(id=f"exa-check-{progressive}", name="main_agent"),
                enable_task_loop=False, auto_create_workspace=False, language="en",
                rails=[SkillUseRail(skills_dir=str(Path(temp) / "skills"), include_tools=False)],
                enable_read_image_multimodal=False, progressive_tool_enabled=progressive)
            await agent.ensure_initialized()
            before = {item.name for item in await agent.ability_manager.list_tool_info()}
            adapter = None
            if archive and args.host_root:
                from jiuwenswarm.server.runtime.agent_adapter.interface_deep import JiuWenSwarmDeepAdapter
                # Exercise the real chat equipment method without starting a
                # server, model session, or changing the user's saved state.
                adapter = JiuWenSwarmDeepAdapter()
                adapter._instance = agent
                adapter._loaded_plugins = {}
                await adapter._load_plugins_for_request({"plugin_names": []})
                assert not expected & {item.name for item in await agent.ability_manager.list_tool_info()}
                from jiuwenswarm.common.schema.agent import AgentRequest
                from jiuwenswarm.common.schema.message import ReqMethod
                sid = f"exa-check-{progressive}"
                adapter._is_session_scoped_adapter = True
                adapter._parent_session_id = sid
                adapter._enable_auto_permission = True
                adapter._permissions_external_input_context_builder = None
                request = AgentRequest(
                    request_id="exa-mount", channel_id="test", session_id=sid,
                    req_method=ReqMethod.CHAT_SEND, params={"plugin_names": ["exa-deep-research"]})
                # Exercise real admission/activity accounting and the real
                # equipment gate. Policy activation is isolated from accounts.
                with patch.object(adapter, "_uses_smart_permission_lifecycle", return_value=True), \
                     patch.object(adapter, "_validate_auto_permission_workspace_request"), \
                     patch.object(adapter, "_capture_permission_version", return_value=(None, {}, {})):
                    async with adapter._permission_request_admission(request, {"query": "mount check"}):
                        error = await adapter._ensure_chat_extensions(request)
                        assert error is None, error.payload if error else None
                record = adapter._loaded_plugins["exa-deep-research"][0]
            else:
                record = await agent.load_plugin(str(current))
            infos = await agent.ability_manager.list_tool_info()
            assert expected <= {item.name for item in infos}, "Exa tools absent from main agent"
            assert expected <= {item.name for item in await agent._react_agent.ability_manager.list_tool_info()}
            exposure = {name: agent.ability_manager.get(name).exposure.value for name in sorted(expected)}
            expected_exposure = "deferred" if progressive else "direct"
            assert set(exposure.values()) == {expected_exposure}, exposure
            result["main_agent"]["progressive" if progressive else "direct"] = {
                "registered": sorted(expected), "exposure": exposure,
                "inner_react_registry": "passed", "absent_before_mount": not bool(expected & before)}
            if adapter:
                result["main_agent"]["progressive" if progressive else "direct"]["chat_equipment_mount"] = "passed; empty selection has no Exa tools, selected package has all four"
                result["main_agent"]["progressive" if progressive else "direct"]["smart_permission_admission_mount"] = "passed; real admission and fresh-turn gate, policy activation isolated"
            from openjiuwen.core.foundation.llm.schema.tool_call import ToolCall
            dispatched, message = await agent.ability_manager._execute_single_tool_call(
                ToolCall(id="exa-guard", type="function", name="exa_research",
                         arguments=json.dumps({"arguments": {"query": "not executed"}, "allow_paid": False})),
                session=None)
            assert dispatched["error"]["code"] == "PAID_ACTION_REQUIRES_APPROVAL", dispatched
            assert "PAID_ACTION_REQUIRES_APPROVAL" in message.content
            result["main_agent"]["progressive" if progressive else "direct"]["main_registry_dispatch_guard"] = "passed; actual registered tool executed, no research run started"
            if progressive and adapter:
                from jiuwenswarm.agents.harness.common.tools.tool_retrieval_toolkits import ToolRetrievalToolkit
                toolkit = ToolRetrievalToolkit(deferred_tools_provider=adapter._collect_deferred_tool_infos)
                assert expected <= {item.name for item in toolkit.frozen_catalogue.flat_entries}
                for name in expected:
                    schema = json.loads(await toolkit.tool_search(operation="get_schema", tool=name))
                    assert schema["name"] == name and schema["schema"]["type"] == "object"
                result["main_agent"]["progressive"]["host_tool_search_all_four_schemas"] = "passed"
            await agent.unload_extension(record)
            assert not expected & {item.name for item in await agent.ability_manager.list_tool_info()}
            result["main_agent"]["progressive" if progressive else "direct"]["unmount_removes_tools"] = "passed"
        tools = {type(tool).__name__: tool for tool in parts.tools}
        with patch.dict(os.environ, {"EXA_API_KEY": ""}):
            guard = await tools["ExaResearchTool"].invoke({"arguments": {"query": "not executed"}})
            assert guard["error"]["code"] == "PAID_ACTION_REQUIRES_APPROVAL"
            result["paid_guard"] = "passed; no research run started"
            if args.live:
                search = await tools["ExaSearchTool"].invoke({"query": "Model Context Protocol Streamable HTTP 传输协议 官方文档", "numResults": 3})
                assert search["ok"], search
                texts = [item.get("text", "") for item in search["result"].get("content", [])]
                assert any("http" in value for value in texts), "No source URLs in actual search content"
                fetch = await tools["ExaFetchTool"].invoke({"urls": ["https://modelcontextprotocol.io/specification/2025-06-18/basic/transports"], "maxCharacters": 2000})
                assert fetch["ok"], fetch
                assert any(len(item.get("text", "")) > 100 for item in fetch["result"].get("content", [])), "Fetch returned no page content"
                advanced = await tools["ExaAdvancedSearchTool"].invoke({"arguments": {"query": "Model Context Protocol Streamable HTTP 传输协议 官方文档", "numResults": 2, "includeDomains": ["modelcontextprotocol.io"]}})
                assert advanced["ok"], advanced
                result["live"] = {"anonymous_search": "passed", "fetch": "passed", "filtered_search": "passed", "search_content_characters": sum(map(len, texts)), "research": "not run; no account/budget authorization"}
        if manager:
            manager.uninstall_plugin_package(imported)
            assert not installed.exists() and not manager.is_plugin_allowed(imported["id"])
            result["isolated_import_install_uninstall"] = "passed"
        output.parent.mkdir(parents=True, exist_ok=True)
        output.write_text(json.dumps(result, indent=2) + "\n", encoding="utf-8")
        print(json.dumps(result, indent=2))

asyncio.run(main())
