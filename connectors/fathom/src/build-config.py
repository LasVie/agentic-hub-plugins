"""Generate the stock WorkSwarm MCP config from the readable Node entry point."""
import json
from pathlib import Path

root = Path(__file__).resolve().parent.parent
entry = (root / "src/fathom-mcp.cjs").read_text(encoding="utf-8")
config = {
    "mcpServers": {
        "fathom": {
            "command": "node",
            "args": ["-e", entry],
            "env": {"FATHOM_API_KEY": "${FATHOM_API_KEY}"},
            "timeout_s": 45,
        },
    },
}
(root / "fathom/mcp.json").write_text(
    json.dumps(config, ensure_ascii=False, indent=2) + "\n", encoding="utf-8"
)
