"""Embed the reviewed Node entry point in the stock WorkSwarm configuration."""

import json
from pathlib import Path

root = Path(__file__).resolve().parent.parent
source = (root / "src" / "monday-mcp.cjs").read_text(encoding="utf-8")
config = {
    "mcpServers": {
        "monday": {
            "command": "node",
            "args": ["-e", source],
            "env": {"MONDAY_PERSONAL_TOKEN": "${MONDAY_PERSONAL_TOKEN}"},
            "timeout_s": 45,
        }
    }
}
(root / "monday" / "mcp.json").write_text(
    json.dumps(config, ensure_ascii=False, indent=2) + "\n", encoding="utf-8"
)
