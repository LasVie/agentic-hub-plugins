"""Regenerate the native MCP configuration from the reviewed entry point."""

import json
from pathlib import Path

root = Path(__file__).resolve().parent.parent
source = (root / "src" / "icloud-mail-mcp.py").read_text(encoding="utf-8")
config = {
    "mcpServers": {
        "icloud-mail": {
            "command": "python3",
            "args": ["-I", "-u", "-c", source],
            "env": {
                "ICLOUD_EMAIL": "${ICLOUD_EMAIL}",
                "ICLOUD_APP_PASSWORD": "${ICLOUD_APP_PASSWORD}",
            },
            "timeout_s": 45,
        }
    }
}
(root / "icloud-mail" / "mcp.json").write_text(
    json.dumps(config, ensure_ascii=False, indent=2) + "\n", encoding="utf-8"
)
