#!/usr/bin/env python3
"""Direct tool testing for the windows-toolkit WorkSwarm Plugin port.

Loads the real tool classes from the packaged plugin and invokes them through
their public ``invoke()`` entry point, exactly as the WorkSwarm host would.

Read-only tools run unconditionally. Desktop-writing tools (clipboard write,
notification) run only when ``--allow-write`` is passed, per the delivery rule
that non-read-only functional tests need explicit approval.
"""
from __future__ import annotations

import asyncio
import importlib.util
import json
import sys
from pathlib import Path

PLUGIN = Path(__file__).resolve().parents[1] / "windows-toolkit"
TOOL_FILE = PLUGIN / "tools" / "windows_toolkit.py"

ALLOW_WRITE = "--allow-write" in sys.argv

results: list[dict] = []


def record(name: str, passed: bool, detail: str) -> None:
    results.append({"check": name, "result": "PASS" if passed else "FAIL", "detail": detail})
    print(f"[{'PASS' if passed else 'FAIL'}] {name}: {detail}")


def load_module():
    spec = importlib.util.spec_from_file_location("windows_toolkit", TOOL_FILE)
    module = importlib.util.module_from_spec(spec)
    assert spec.loader is not None
    spec.loader.exec_module(module)
    return module


async def main() -> int:
    module = load_module()

    # --- 1. hosts read (read-only) ---
    hosts = module.HostsListTool()
    out = await hosts.invoke({})
    ok = out.get("ok") is True and isinstance(out.get("content"), str) and isinstance(out.get("lines"), int)
    record("win_hosts_list returns content and line count", ok, json.dumps(out, ensure_ascii=False)[:200])
    hosts_content = out.get("content", "")

    # --- 2. netdiag: known-open loopback port ---
    # Start a local listener so OPEN is deterministic and offline.
    server = await asyncio.start_server(lambda r, w: w.close(), "127.0.0.1", 0)
    open_port = server.sockets[0].getsockname()[1]
    netdiag = module.NetdiagTool()
    out_open = await netdiag.invoke({"host": "127.0.0.1", "port": open_port})
    ok_open = out_open.get("ok") is True and out_open.get("tcp") == "OPEN"
    record(
        "win_netdiag reports OPEN on a listening loopback port",
        ok_open,
        f"port={open_port} tcp={out_open.get('tcp')} dns={out_open.get('dns')}",
    )

    # --- 3. netdiag: known-closed port (same host, just closed) ---
    server.close()
    await server.wait_closed()
    out_closed = await netdiag.invoke({"host": "127.0.0.1", "port": open_port})
    ok_closed = out_closed.get("ok") is True and out_closed.get("tcp") in {"CLOSED", "TIMEOUT"}
    record(
        "win_netdiag reports closed/timeout after the listener stops",
        ok_closed,
        f"port={open_port} tcp={out_closed.get('tcp')}",
    )

    # --- 4. input validation: bad port rejected without touching PowerShell ---
    out_bad = await netdiag.invoke({"host": "127.0.0.1", "port": 99999})
    ok_bad = out_bad.get("ok") is False and out_bad.get("error", {}).get("code") == "BAD_INPUT"
    record("win_netdiag rejects an out-of-range port", ok_bad, json.dumps(out_bad, ensure_ascii=False)[:160])

    # --- 5. input validation: missing host ---
    out_missing = await netdiag.invoke({})
    ok_missing = out_missing.get("ok") is False and out_missing.get("error", {}).get("code") == "BAD_INPUT"
    record("win_netdiag rejects a missing host", ok_missing, json.dumps(out_missing, ensure_ascii=False)[:160])

    # --- 6. clipboard read (read-only observation) ---
    clip_read = module.ClipboardReadTool()
    out_clip = await clip_read.invoke({})
    ok_clip = out_clip.get("ok") is True and isinstance(out_clip.get("text"), str) and isinstance(out_clip.get("empty"), bool)
    record("win_clipboard_read returns text and empty flag", ok_clip, f"empty={out_clip.get('empty')} chars={len(out_clip.get('text',''))}")

    # --- 7/8. non-read-only tools: only with explicit approval ---
    if ALLOW_WRITE:
        marker = "windows-toolkit 端口写测试 2026-10-23"
        clip_write = module.ClipboardWriteTool()
        out_write = await clip_write.invoke({"text": marker})
        ok_write = out_write.get("ok") is True and out_write.get("chars") == len(marker)
        record("win_clipboard_write replaces clipboard content", ok_write, f"chars={out_write.get('chars')}")

        out_reread = await clip_read.invoke({})
        ok_roundtrip = out_reread.get("text") == marker
        record("clipboard read-back matches what was written", ok_roundtrip, f"text={out_reread.get('text','')[:60]!r}")

        notify = module.NotifyTool()
        out_notify = await notify.invoke({"title": "窗口工具箱测试", "message": "这是一次本地通知测试"})
        ok_notify = out_notify.get("ok") is True
        record("win_notify shows a system popup", ok_notify, json.dumps(out_notify, ensure_ascii=False)[:160])

        bad_notify = await notify.invoke({"title": "x"})
        ok_bad_notify = bad_notify.get("ok") is False and bad_notify.get("error", {}).get("code") == "BAD_INPUT"
        record("win_notify rejects missing message", ok_bad_notify, json.dumps(bad_notify, ensure_ascii=False)[:160])
    else:
        print("[SKIP] clipboard write / notify: pass --allow-write to run desktop-writing checks")

    # --- manifest/tool cross-check ---
    manifest = json.loads((PLUGIN / "manifest.json").read_text(encoding="utf-8"))
    declared = [t["class"] for t in manifest["tools"]]
    missing = [c for c in declared if not hasattr(module, c)]
    record("every manifest tool class exists in the module", not missing, f"declared={declared} missing={missing}")

    failed = [r for r in results if r["result"] == "FAIL"]
    print()
    print(f"TOTAL {len(results)} checks, {len(results) - len(failed)} passed, {len(failed)} failed")
    return 1 if failed else 0


if __name__ == "__main__":
    sys.exit(asyncio.run(main()))
