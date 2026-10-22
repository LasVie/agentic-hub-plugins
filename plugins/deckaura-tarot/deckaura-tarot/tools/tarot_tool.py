"""Deckaura 随包 CLI 的本地宿主适配器；不调用网络或 shell。

修改说明（Agentic Hub 团队，2026-10-22）：将帮助、工具描述与错误文本翻译为简体中文，保留参数、协议值和执行逻辑。
"""
from __future__ import annotations

import asyncio
import json
from pathlib import Path
import shutil
import subprocess
from typing import Any

from openjiuwen.core.foundation.tool import Tool, ToolCard


SPREADS = ("daily", "three-card", "decision", "relationship", "celtic-cross", "yes-no")
SCRIPT = Path(__file__).resolve().parents[1] / "skills/tarot-reading/scripts/tarot.mjs"


def _error(code: str, message: str, **details: Any) -> dict[str, Any]:
    return {"ok": False, "error": {"code": code, "message": message, **details}}


def _arguments(inputs: dict[str, Any]) -> list[str]:
    if not isinstance(inputs, dict):
        raise ValueError("输入必须是 JSON 对象。")
    action = inputs.get("action")
    if not isinstance(action, str) or action not in ("lookup", "draw", "spread", "validate"):
        raise ValueError("action 必须是 lookup、draw、spread 或 validate。")
    allowed = {"action"}
    if action == "lookup":
        allowed |= {"card", "orientation"}
    elif action == "draw":
        allowed |= {"count", "seed", "reversals"}
    elif action == "spread":
        allowed |= {"spread", "seed", "reversals"}
    unknown = set(inputs) - allowed
    if unknown:
        raise ValueError("此操作不支持的参数：" + ", ".join(sorted(unknown)))
    args = [action]
    if action == "lookup":
        card = inputs.get("card")
        if not isinstance(card, str) or not card.strip() or len(card) > 100 or card.strip().startswith("--") or "\x00" in card:
            raise ValueError("card 必须是非空卡牌名称，最多 100 个字符，不能包含 NUL 或以 -- 开头。")
        orientation = inputs.get("orientation", "upright")
        if orientation not in ("upright", "reversed"):
            raise ValueError("orientation 必须是 upright（正位）或 reversed（逆位）。")
        args += [card.strip(), "--orientation", orientation]
    elif action in ("draw", "spread"):
        if action == "draw":
            count = inputs.get("count", 1)
            if type(count) is not int or not 1 <= count <= 78:
                raise ValueError("count 必须是 1 至 78 的整数。")
            args += ["--count", str(count)]
        else:
            spread = inputs.get("spread")
            if not isinstance(spread, str) or spread not in SPREADS:
                raise ValueError("spread 必须是以下值之一：" + ", ".join(SPREADS))
            args.append(spread)
        reversals = inputs.get("reversals", True)
        if type(reversals) is not bool:
            raise ValueError("reversals 必须是 JSON 布尔值。")
        args += ["--reversals", str(reversals).lower()]
        if "seed" in inputs:
            seed = inputs["seed"]
            if not isinstance(seed, str) or not seed or len(seed) > 256 or seed.startswith("--") or "\x00" in seed:
                raise ValueError("seed 必须是 1 至 256 个字符，不能包含 NUL 或以 -- 开头；请使用非敏感测试标签。")
            args += ["--seed", seed]
    return args


def run_tarot(inputs: dict[str, Any]) -> dict[str, Any]:
    """仅以校验后的参数运行固定本地 CLI，超时限制为十秒。"""
    try:
        args = _arguments(inputs)
    except ValueError as exc:
        return _error("invalid_input", str(exc))
    node = shutil.which("node")
    if not node:
        return _error("missing_node", "请安装 Node.js >=18，将 node 加入 WorkSwarm 后端的 PATH，然后重启该后端。")
    if not SCRIPT.is_file():
        return _error("missing_payload", "随包塔罗脚本缺失；请重新安装完整插件。")
    try:
        result = subprocess.run(
            [node, str(SCRIPT), *args],
            capture_output=True, text=True, encoding="utf-8", timeout=10,
            check=False, shell=False,
        )
    except subprocess.TimeoutExpired:
        return _error("timeout", "本地塔罗操作超过了十秒时限。")
    except (OSError, UnicodeError) as exc:
        return _error("execution_failed", f"无法执行本地 Node.js 运行时：{exc}")
    if result.returncode:
        try:
            detail = json.loads(result.stderr)
        except (ValueError, TypeError):
            return _error("execution_failed", "随包 CLI 执行失败；请检查 Node.js >=18 及已安装的完整文件。")
        return _error("operation_failed", str(detail.get("error", "塔罗操作失败。")), suggestions=detail.get("suggestions", []))
    try:
        output = json.loads(result.stdout)
    except ValueError:
        return _error("invalid_output", "本地 CLI 返回了无效 JSON。")
    if not isinstance(output, dict):
        return _error("invalid_output", "本地 CLI 返回了非预期的 JSON 值。")
    return {"ok": True, **output}


class TarotTool(Tool):
    def __init__(self) -> None:
        super().__init__(ToolCard(
            id="deckaura_tarot", name="deckaura_tarot",
            description="离线查询 Deckaura 牌义、可复现抽牌及六种反思牌阵。不作事实预测，不要将私人问题放入种子。",
            input_params={
                "type": "object", "additionalProperties": False, "required": ["action"],
                "properties": {
                    "action": {"type": "string", "enum": ["lookup", "draw", "spread", "validate"]},
                    "card": {"type": "string", "description": "待查询卡牌的英文标识，例如 The Star（星星）。", "minLength": 1, "maxLength": 100},
                    "orientation": {"type": "string", "enum": ["upright", "reversed"], "default": "upright"},
                    "count": {"type": "integer", "minimum": 1, "maximum": 78, "default": 1},
                    "spread": {"type": "string", "enum": list(SPREADS)},
                    "seed": {"type": "string", "minLength": 1, "maxLength": 256, "description": "可选的复现标签，不能是私人问题，也不能以 -- 开头。"},
                    "reversals": {"type": "boolean", "default": True},
                },
            },
        ))

    async def invoke(self, inputs: dict[str, Any], **kwargs: Any) -> dict[str, Any]:
        return await asyncio.to_thread(run_tarot, inputs)

    async def stream(self, inputs: dict[str, Any], **kwargs: Any):
        yield await self.invoke(inputs, **kwargs)
