"""Generate the stock WorkSwarm MCP config from the readable Node entry point."""
import json
from pathlib import Path

root = Path(__file__).resolve().parent.parent
entry = (root / "src/trello-mcp.cjs").read_text(encoding="utf-8")
config = {
    "mcpServers": {
        "trello": {
            "command": "node",
            "args": ["-e", entry],
            "env": {"TRELLO_API_KEY": "${TRELLO_API_KEY}", "TRELLO_API_TOKEN": "${TRELLO_API_TOKEN}"},
            "timeout_s": 45,
        },
    },
}
(root / "trello/mcp.json").write_text(
    json.dumps(config, ensure_ascii=False, indent=2) + "\n", encoding="utf-8"
)
