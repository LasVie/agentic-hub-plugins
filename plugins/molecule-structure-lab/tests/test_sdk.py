"""Exercise the supported SDK manifest loader and resolver without a host or model.

Run with the target host's existing Python environment. Set
MOLECULE_WORKBENCH_NODE for this test process if Node is absent from its PATH.
The payload can be the source, extracted ZIP, or installed plugin directory.
"""
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
import platform
import sys
import tempfile
from urllib.parse import urlsplit

sys.dont_write_bytecode = True


def inventory(root):
    return {str(path.relative_to(root)): hashlib.sha256(path.read_bytes()).hexdigest()
            for path in sorted(root.rglob("*")) if path.is_file()}


def digest_inventory(files):
    return hashlib.sha256(json.dumps(files, sort_keys=True, separators=(",", ":")).encode()).hexdigest()


def compact_analysis(result):
    item = {key: value for key, value in result.items() if key != "svg"}
    if "svg" in result:
        raw = result["svg"].encode("utf-8")
        item.update(svg_bytes=len(raw), svg_sha256=hashlib.sha256(raw).hexdigest())
    return item


async def exercise(payload, workspace):
    from openjiuwen.core.foundation.tool import Tool
    from openjiuwen.harness.resources import load_plugin_package, resolve_plugin_parts
    from openjiuwen.harness.schema.build_context import BuildContext

    spec = load_plugin_package(payload / "manifest.json")
    context = BuildContext(language="cn", member_name="Cai Zhenze", project_dir=str(workspace),
                           extras={"source_root": str(payload)})
    parts = resolve_plugin_parts(spec, context)
    assert spec.id == "molecule-structure-lab"
    assert len(parts.tools) == 2 and len(parts.skills) == 1
    assert not parts.mcps and not parts.rails and not parts.subagents
    assert all(isinstance(tool, Tool) for tool in parts.tools)
    tools = {tool.card.id: tool for tool in parts.tools}
    assert set(tools) == {"analyze_molecule", "molecule_workbench"}
    skill = parts.skills[0]
    assert Path(skill.directory) == payload / "skills/molecule-workbench"
    assert skill.mode == "all"
    skill_text = (Path(skill.directory) / "SKILL.md").read_text("utf-8")
    assert "简体中文" in skill_text
    evidence = {"loader": "openjiuwen.harness.resources.load_plugin_package",
                "resolver": "openjiuwen.harness.resources.resolve_plugin_parts",
                "build_context": "openjiuwen.harness.schema.build_context.BuildContext",
                "plugin_id": spec.id, "tool_ids": sorted(tools),
                "skill": {"directory": skill.directory, "mode": skill.mode, "chinese_instructions": True},
                "analysis": {}}
    analyze = tools["analyze_molecule"]
    aspirin = await analyze.invoke({"smiles": "CC(=O)Oc1ccccc1C(=O)O", "smarts": "c1ccccc1"})
    assert aspirin["ok"] and aspirin["version"] == "1.0.1", aspirin
    assert abs(aspirin["descriptors"]["amw"] - 180.159) < 0.000001
    assert abs(aspirin["descriptors"]["tpsa"] - 63.6) < 0.000001
    assert aspirin["match"]["atoms"] == [4, 5, 6, 7, 8, 9]
    evidence["analysis"]["aspirin"] = compact_analysis(aspirin)
    ethanol = await analyze.invoke({"smiles": "CCO", "smarts": "c1ccccc1"})
    assert ethanol["ok"] and not ethanol["match"]["matched"]
    assert abs(ethanol["descriptors"]["amw"] - 46.069) < 0.000001
    evidence["analysis"]["ethanol"] = compact_analysis(ethanol)
    for name, inputs, code in [
        ("invalid_smiles", {"smiles": "C1CC"}, "invalid_smiles"),
        ("invalid_smarts", {"smiles": "CCO", "smarts": "["}, "invalid_smarts"),
    ]:
        result = await analyze.invoke(inputs)
        assert not result["ok"] and result["error"]["code"] == code, result
        evidence["analysis"][name] = result
    chunks = [item async for item in analyze.stream({"smiles": "CCO"})]
    assert len(chunks) == 1 and chunks[0]["ok"] and chunks[0]["version"] == "1.0.1"
    assert not chunks[0]["match"]["query_supplied"]
    evidence["analysis"]["stream"] = {"chunks": 1, "result": compact_analysis(chunks[0])}

    workbench = tools["molecule_workbench"]
    arguments = {"workspace": str(workspace)}
    initial = await workbench.invoke({**arguments, "action": "status"})
    assert initial["ok"] and not initial["running"]
    assert list(workspace.iterdir()) == []
    denied = await workbench.invoke({**arguments, "action": "start", "confirmed": False})
    assert not denied["ok"] and denied["error"]["code"] == "confirmation_required"
    assert list(workspace.iterdir()) == []
    started = await workbench.invoke({**arguments, "action": "start", "confirmed": True})
    assert started["ok"] and started["running"], started
    try:
        url = urlsplit(started["url"])
        assert url.hostname == "127.0.0.1" and url.port > 0
        connection = http.client.HTTPConnection(url.hostname, url.port, timeout=3)
        try:
            connection.request("GET", url.path)
            response = connection.getresponse()
            body = response.read().decode("utf-8")
            assert response.status == 200 and "离线分子结构工作台" in body
            page_evidence = {"status": response.status, "chinese_page": True,
                             "strict_page_csp": "'unsafe-eval'" not in response.getheader("Content-Security-Policy")}
            assert page_evidence["strict_page_csp"]
        finally:
            connection.close()
        active = await workbench.invoke({**arguments, "action": "status"})
        reused = await workbench.invoke({**arguments, "action": "start", "confirmed": True})
        assert active["running"] and reused["url"] == started["url"]
        status_chunks = [item async for item in workbench.stream({**arguments, "action": "status"})]
        assert len(status_chunks) == 1 and status_chunks[0]["running"]
    finally:
        stopped = await workbench.invoke({**arguments, "action": "stop", "confirmed": True})
        assert stopped["ok"] and not stopped["running"], stopped
    final = await workbench.invoke({**arguments, "action": "status"})
    assert final["ok"] and not final["running"], final
    evidence["lifecycle"] = {"initial_status_no_writes": True, "confirmation_rejection": True,
                              "start": True, "page": page_evidence, "status": True, "reuse_same_service": True,
                              "stream": True, "stop": True, "final_stopped": True,
                              "listener_host": "127.0.0.1", "port_allocation": "ephemeral"}
    return evidence


def main():
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument("--payload", type=Path, required=True)
    parser.add_argument("--output", type=Path)
    args = parser.parse_args()
    payload = args.payload.resolve(strict=True)
    output = args.output.resolve() if args.output else None
    if output and output.is_relative_to(payload):
        parser.error("Evidence output must be outside the immutable plugin payload.")
    before = inventory(payload)
    previous_cwd = Path.cwd()
    # SDK diagnostic logs, if any, remain in this test's temporary directory.
    with tempfile.TemporaryDirectory(prefix="molecule-sdk-test-", dir="/private/tmp" if Path("/private/tmp").exists() else None) as directory:
        temporary = Path(directory).resolve()
        workspace = temporary / "workspace"
        workspace.mkdir()
        sdk_cwd = temporary / "sdk-cwd"
        sdk_cwd.mkdir()
        try:
            os.chdir(sdk_cwd)
            with contextlib.redirect_stdout(sys.stderr):
                results = asyncio.run(exercise(payload, workspace))
        finally:
            os.chdir(previous_cwd)
    after = inventory(payload)
    assert before == after, "Native SDK resolution/invocation changed the plugin payload."
    try:
        sdk_version = importlib.metadata.version("openjiuwen")
    except importlib.metadata.PackageNotFoundError:
        sdk_version = "unknown"
    evidence = {"passed": True, "checked_at": datetime.now(timezone.utc).isoformat(),
                "payload": str(payload), "version": "1.0.1", "python": platform.python_version(),
                "platform": platform.system(), "native_runtime_support": "macOS/Linux POSIX; Windows unsupported",
                "openjiuwen_version": sdk_version, "model_requests_sent": 0,
                "payload_files_unchanged": True, "payload_file_count": len(before),
                "payload_inventory_sha256": digest_inventory(before), **results}
    encoded = json.dumps(evidence, ensure_ascii=False, indent=2) + "\n"
    if output:
        output.write_text(encoded, encoding="utf-8")
    print(json.dumps({key: value for key, value in evidence.items() if key != "analysis"}, ensure_ascii=False))


if __name__ == "__main__":
    main()
