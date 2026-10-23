"""WorkSwarm/OpenJiuwen port of MIT-licensed dsh-win-toolkit 0.1.3.

Copyright (c) 2026 dsh-mcp-bridge contributors. Modified to expose explicit
Python/OpenJiuwen tools for WorkSwarm; see ../licenses/dsh-win-toolkit/LICENSE.

Upstream source: https://github.com/Edge-Echo/dsh-win-toolkit
Pinned npm version: 0.1.3 (gitHead 665bc6947c52e5f66e73233eff4950d11525430c)
中文化修改：2026-10-23，翻译工具说明、可读提示与错误消息；保留工具语义、
参数、PowerShell 脚本逻辑与 Base64 传参方式。

Security model (inherited from upstream, preserved deliberately):
every user-provided value crosses the PowerShell boundary as Base64 and is
decoded inside PowerShell, so no argument is ever string-interpolated into a
command line. Values are never passed through a shell.
"""
from __future__ import annotations

import base64
import json
import subprocess
from typing import Any, AsyncIterator, Dict

from openjiuwen.core.foundation.tool import Tool, ToolCard

POWERSHELL = "powershell.exe"
DEFAULT_TIMEOUT_MS = 20000
MAX_STDOUT = 4 * 1024 * 1024


def _b64(value: str) -> str:
    return base64.b64encode(value.encode("utf-8")).decode("ascii")


def _ps_str(value: str) -> str:
    """PowerShell expression that decodes a Base64 UTF-8 literal."""
    return (
        "[System.Text.Encoding]::UTF8.GetString("
        f"[System.Convert]::FromBase64String('{_b64(value)}'))"
    )


def _run_ps(script: str, timeout_ms: int = DEFAULT_TIMEOUT_MS) -> Dict[str, Any]:
    """Run a PowerShell script and return parsed JSON output.

    Returns a structured error dict instead of raising, so the host shows a
    readable Chinese message rather than a stack trace.
    """
    # Windows PowerShell 5.1 writes stdout in the active OEM codepage; without
    # this preamble any non-ASCII text comes back as '?'. Setting UTF-8 here is
    # required for the Chinese messages and clipboard contents this port emits.
    preamble = (
        "[Console]::OutputEncoding = [System.Text.Encoding]::UTF8; "
        "$OutputEncoding = [System.Text.Encoding]::UTF8"
    )
    try:
        completed = subprocess.run(
            [POWERSHELL, "-NoProfile", "-NonInteractive", "-Command", f"{preamble}; {script}"],
            capture_output=True,
            timeout=max(1, timeout_ms // 1000),
            creationflags=getattr(subprocess, "CREATE_NO_WINDOW", 0),
        )
    except FileNotFoundError:
        return _error("POWERSHELL_MISSING", "未找到 powershell.exe：本插件仅支持 Windows 宿主。")
    except subprocess.TimeoutExpired:
        return _error("TIMEOUT", f"PowerShell 调用超过 {timeout_ms} 毫秒未返回。")

    if completed.returncode:
        message = (completed.stderr or b"").decode("utf-8", "replace").strip()
        return _error("POWERSHELL_FAILED", f"PowerShell 执行失败：{message[:400] or '无错误输出'}")
    if len(completed.stdout) > MAX_STDOUT:
        return _error("OUTPUT_TOO_LARGE", "PowerShell 输出超过 4 MiB 上限。")

    raw = completed.stdout.decode("utf-8", "replace").strip()
    if not raw:
        return _error("EMPTY_OUTPUT", "PowerShell 没有返回内容。")
    try:
        parsed = json.loads(raw)
    except json.JSONDecodeError:
        return _error("INVALID_JSON", f"PowerShell 返回的不是有效 JSON：{raw[:200]}")
    if not isinstance(parsed, dict):
        return _error("INVALID_SHAPE", "PowerShell 返回的 JSON 不是对象。")
    return parsed


def _error(code: str, message: str) -> Dict[str, Any]:
    return {"ok": False, "error": {"code": code, "message": message}}


class _BaseTool(Tool):
    """Shared invocation plumbing: input validation and async offloading."""

    async def _invoke_ps(self, script: str, timeout_ms: int = DEFAULT_TIMEOUT_MS) -> Dict[str, Any]:
        import asyncio

        def call() -> Dict[str, Any]:
            return _run_ps(script, timeout_ms)

        try:
            return await asyncio.to_thread(call)
        except Exception as exc:  # noqa: BLE001 - surface a readable message
            return _error("UNEXPECTED", f"本机操作未确认成功：{exc}")

    async def invoke(self, inputs: Dict[str, Any], **kwargs: Any) -> Dict[str, Any]:
        if not isinstance(inputs, dict):
            return _error("BAD_INPUT", "输入须为对象。")
        try:
            return await self._run(inputs)
        except ValueError as exc:
            return _error("BAD_INPUT", str(exc))

    async def stream(self, inputs: Dict[str, Any], **kwargs: Any) -> AsyncIterator[Dict[str, Any]]:
        yield await self.invoke(inputs, **kwargs)

    async def _run(self, inputs: Dict[str, Any]) -> Dict[str, Any]:  # pragma: no cover
        raise NotImplementedError


class ClipboardReadTool(_BaseTool):
    def __init__(self) -> None:
        super().__init__(
            ToolCard(
                id="win_clipboard_read",
                name="win_clipboard_read",
                description="读取当前 Windows 剪贴板中的文本；剪贴板没有文本时返回空标记。",
                input_params={"type": "object", "properties": {}, "additionalProperties": False},
                parallel_safe=False,
            )
        )

    async def _run(self, inputs: Dict[str, Any]) -> Dict[str, Any]:
        script = "; ".join(
            [
                '$ErrorActionPreference = "Continue"',
                'try { $t = Get-Clipboard -Raw -ErrorAction Stop } catch { $t = "" }',
                '$out = [ordered]@{ ok = $true; text = "$t"; empty = ([string]::IsNullOrEmpty("$t")) }',
                "$out | ConvertTo-Json -Compress",
            ]
        )
        return await self._invoke_ps(script)


class ClipboardWriteTool(_BaseTool):
    def __init__(self) -> None:
        super().__init__(
            ToolCard(
                id="win_clipboard_write",
                name="win_clipboard_write",
                description="用给定文本替换当前 Windows 剪贴板内容。属于桌面写操作，仅在用户明确要求时调用。",
                input_params={
                    "type": "object",
                    "properties": {"text": {"type": "string", "description": "要写入剪贴板的文本"}},
                    "required": ["text"],
                    "additionalProperties": False,
                },
                parallel_safe=False,
            )
        )

    async def _run(self, inputs: Dict[str, Any]) -> Dict[str, Any]:
        text = inputs.get("text")
        if not isinstance(text, str):
            raise ValueError("text 必须是字符串。")
        script = "; ".join(
            [
                f"Set-Clipboard -Value ({_ps_str(text)}) -ErrorAction Stop",
                '$out = [ordered]@{ ok = $true; chars = (Get-Clipboard -Raw).Length }',
                "$out | ConvertTo-Json -Compress",
            ]
        )
        return await self._invoke_ps(script)


class NotifyTool(_BaseTool):
    def __init__(self) -> None:
        super().__init__(
            ToolCard(
                id="win_notify",
                name="win_notify",
                description="显示一个约 6 秒后自动关闭的 Windows 通知弹窗，用于长任务结束时提醒用户。",
                input_params={
                    "type": "object",
                    "properties": {
                        "title": {"type": "string", "description": "通知标题"},
                        "message": {"type": "string", "description": "通知正文"},
                    },
                    "required": ["title", "message"],
                    "additionalProperties": False,
                },
                parallel_safe=False,
            )
        )

    async def _run(self, inputs: Dict[str, Any]) -> Dict[str, Any]:
        title = inputs.get("title")
        message = inputs.get("message")
        if not isinstance(title, str) or not isinstance(message, str):
            raise ValueError("title 与 message 必须是字符串。")
        script = "; ".join(
            [
                f"$w = New-Object -ComObject WScript.Shell; $null = $w.Popup({_ps_str(message)}, 6, {_ps_str(title)}, 0x40)",
                "$out = [ordered]@{ ok = $true }",
                "$out | ConvertTo-Json -Compress",
            ]
        )
        return await self._invoke_ps(script)


class HostsListTool(_BaseTool):
    def __init__(self) -> None:
        super().__init__(
            ToolCard(
                id="win_hosts_list",
                name="win_hosts_list",
                description="只读读取 Windows hosts 文件（C:\\Windows\\System32\\drivers\\etc\\hosts）的内容与行数。",
                input_params={"type": "object", "properties": {}, "additionalProperties": False},
                parallel_safe=True,
            )
        )

    async def _run(self, inputs: Dict[str, Any]) -> Dict[str, Any]:
        hosts = "$env:WINDIR + '\\System32\\drivers\\etc\\hosts'"
        script = "; ".join(
            [
                f"$c = Get-Content ({hosts}) -ErrorAction Stop | Out-String",
                f"$n = @(Get-Content ({hosts}) -ErrorAction SilentlyContinue).Count",
                '$out = [ordered]@{ ok = $true; content = "$c"; lines = $n }',
                "$out | ConvertTo-Json -Compress",
            ]
        )
        return await self._invoke_ps(script)


class NetdiagTool(_BaseTool):
    def __init__(self) -> None:
        super().__init__(
            ToolCard(
                id="win_netdiag",
                name="win_netdiag",
                description="对给定主机做 DNS 解析与 TCP 端口连接测试（默认 443），返回解析地址与 OPEN/CLOSED/TIMEOUT。",
                input_params={
                    "type": "object",
                    "properties": {
                        "host": {"type": "string", "description": "要测试的主机名或 IP 地址"},
                        "port": {"type": "integer", "description": "要测试的 TCP 端口，默认 443"},
                    },
                    "required": ["host"],
                    "additionalProperties": False,
                },
                parallel_safe=True,
            )
        )

    async def _run(self, inputs: Dict[str, Any]) -> Dict[str, Any]:
        host = inputs.get("host")
        if not isinstance(host, str) or not host.strip():
            raise ValueError("host 必须是非空字符串。")
        port = inputs.get("port", 443)
        if not isinstance(port, int) or isinstance(port, bool) or not 1 <= port <= 65535:
            raise ValueError("port 必须是 1..65535 的整数。")
        host_expr = _ps_str(host)
        script = "; ".join(
            [
                '$ErrorActionPreference = "Continue"',
                f'try {{ $dns = [System.Net.Dns]::GetHostAddresses({host_expr}) | ForEach-Object {{ $_.IPAddressToString }} }} '
                'catch { $dns = @("DNS_FAILED") }',
                f"$c = New-Object System.Net.Sockets.TcpClient; try {{ $t = $c.ConnectAsync({host_expr}, {port}); "
                'if ($t.Wait(5000)) { $tcp = "OPEN" } else { $tcp = "TIMEOUT" } } '
                'catch { $tcp = "CLOSED" } finally { $c.Dispose() }',
                '$out = [ordered]@{ ok = $true; dns = @($dns); tcp = $tcp }',
                "$out | ConvertTo-Json -Compress",
            ]
        )
        return await self._invoke_ps(script)
