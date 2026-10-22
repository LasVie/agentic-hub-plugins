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
        result = {"host_load": "passed", "tools": names, "skills": len(parts.skills),
                  "runtime": {"python": sys.version.split()[0], "mcp": importlib.metadata.version("mcp"), "jsonschema": importlib.metadata.version("jsonschema")},
                  "loader_sha256": hashlib.sha256((args.sdk_root / "openjiuwen/harness/resources/extension_loader.py").read_bytes()).hexdigest()}
        tools = {type(tool).__name__: tool for tool in parts.tools}
        with patch.dict(os.environ, {"EXA_API_KEY": ""}):
            guard = await tools["ExaResearchTool"].invoke({"arguments": {"query": "not executed"}})
            assert guard["error"]["code"] == "PAID_ACTION_REQUIRES_APPROVAL"
            result["paid_guard"] = "passed; no research run started"
            if args.live:
                search = await tools["ExaSearchTool"].invoke({"query": "official Model Context Protocol streamable HTTP transport documentation", "numResults": 3})
                assert search["ok"], search
                texts = [item.get("text", "") for item in search["result"].get("content", [])]
                assert any("http" in value for value in texts), "No source URLs in actual search content"
                fetch = await tools["ExaFetchTool"].invoke({"urls": ["https://modelcontextprotocol.io/specification/2025-06-18/basic/transports"], "maxCharacters": 2000})
                assert fetch["ok"], fetch
                assert any(len(item.get("text", "")) > 100 for item in fetch["result"].get("content", [])), "Fetch returned no page content"
                advanced = await tools["ExaAdvancedSearchTool"].invoke({"arguments": {"query": "Model Context Protocol streamable HTTP transport documentation", "numResults": 2, "includeDomains": ["modelcontextprotocol.io"]}})
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
