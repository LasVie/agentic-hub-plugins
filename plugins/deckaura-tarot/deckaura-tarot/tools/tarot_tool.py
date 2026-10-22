"""Native host adapter for the bundled Deckaura CLI; no network or shell calls."""
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
        raise ValueError("Input must be a JSON object.")
    action = inputs.get("action")
    if not isinstance(action, str) or action not in ("lookup", "draw", "spread", "validate"):
        raise ValueError("action must be lookup, draw, spread or validate.")
    allowed = {"action"}
    if action == "lookup":
        allowed |= {"card", "orientation"}
    elif action == "draw":
        allowed |= {"count", "seed", "reversals"}
    elif action == "spread":
        allowed |= {"spread", "seed", "reversals"}
    unknown = set(inputs) - allowed
    if unknown:
        raise ValueError("Unsupported parameters for this action: " + ", ".join(sorted(unknown)))
    args = [action]
    if action == "lookup":
        card = inputs.get("card")
        if not isinstance(card, str) or not card.strip() or len(card) > 100 or card.strip().startswith("--") or "\x00" in card:
            raise ValueError("card must be a nonempty card name of at most 100 characters, without NUL or a leading --.")
        orientation = inputs.get("orientation", "upright")
        if orientation not in ("upright", "reversed"):
            raise ValueError("orientation must be upright or reversed.")
        args += [card.strip(), "--orientation", orientation]
    elif action in ("draw", "spread"):
        if action == "draw":
            count = inputs.get("count", 1)
            if type(count) is not int or not 1 <= count <= 78:
                raise ValueError("count must be an integer from 1 to 78.")
            args += ["--count", str(count)]
        else:
            spread = inputs.get("spread")
            if not isinstance(spread, str) or spread not in SPREADS:
                raise ValueError("spread must be one of: " + ", ".join(SPREADS))
            args.append(spread)
        reversals = inputs.get("reversals", True)
        if type(reversals) is not bool:
            raise ValueError("reversals must be a JSON boolean.")
        args += ["--reversals", str(reversals).lower()]
        if "seed" in inputs:
            seed = inputs["seed"]
            if not isinstance(seed, str) or not seed or len(seed) > 256 or seed.startswith("--") or "\x00" in seed:
                raise ValueError("seed must be 1-256 characters, without NUL or a leading --; use a non-sensitive test label.")
            args += ["--seed", seed]
    return args


def run_tarot(inputs: dict[str, Any]) -> dict[str, Any]:
    """Run only the fixed local CLI with validated arguments and a ten-second bound."""
    try:
        args = _arguments(inputs)
    except ValueError as exc:
        return _error("invalid_input", str(exc))
    node = shutil.which("node")
    if not node:
        return _error("missing_node", "Install Node.js >=18 and put node on the WorkSwarm backend PATH, then restart that backend.")
    if not SCRIPT.is_file():
        return _error("missing_payload", "The bundled tarot script is missing; reinstall the complete plugin.")
    try:
        result = subprocess.run(
            [node, str(SCRIPT), *args],
            capture_output=True, text=True, encoding="utf-8", timeout=10,
            check=False, shell=False,
        )
    except subprocess.TimeoutExpired:
        return _error("timeout", "The local tarot operation exceeded ten seconds.")
    except (OSError, UnicodeError) as exc:
        return _error("execution_failed", f"Cannot execute the local Node.js runtime: {exc}")
    if result.returncode:
        try:
            detail = json.loads(result.stderr)
        except (ValueError, TypeError):
            return _error("execution_failed", "The bundled CLI failed; check Node.js >=18 and the installed payload.")
        return _error("operation_failed", str(detail.get("error", "Tarot operation failed.")), suggestions=detail.get("suggestions", []))
    try:
        output = json.loads(result.stdout)
    except ValueError:
        return _error("invalid_output", "The local CLI returned invalid JSON.")
    if not isinstance(output, dict):
        return _error("invalid_output", "The local CLI returned an unexpected JSON value.")
    return {"ok": True, **output}


class TarotTool(Tool):
    def __init__(self) -> None:
        super().__init__(ToolCard(
            id="deckaura_tarot", name="deckaura_tarot",
            description="Offline Deckaura card lookup, reproducible draws and six spreads for reflection. No factual prediction. Do not put private questions in seeds.",
            input_params={
                "type": "object", "additionalProperties": False, "required": ["action"],
                "properties": {
                    "action": {"type": "string", "enum": ["lookup", "draw", "spread", "validate"]},
                    "card": {"type": "string", "description": "Card name for lookup, e.g. The Star.", "minLength": 1, "maxLength": 100},
                    "orientation": {"type": "string", "enum": ["upright", "reversed"], "default": "upright"},
                    "count": {"type": "integer", "minimum": 1, "maximum": 78, "default": 1},
                    "spread": {"type": "string", "enum": list(SPREADS)},
                    "seed": {"type": "string", "minLength": 1, "maxLength": 256, "description": "Optional reproducibility label, not a private question; must not start with --."},
                    "reversals": {"type": "boolean", "default": True},
                },
            },
        ))

    async def invoke(self, inputs: dict[str, Any], **kwargs: Any) -> dict[str, Any]:
        return await asyncio.to_thread(run_tarot, inputs)

    async def stream(self, inputs: dict[str, Any], **kwargs: Any):
        yield await self.invoke(inputs, **kwargs)
