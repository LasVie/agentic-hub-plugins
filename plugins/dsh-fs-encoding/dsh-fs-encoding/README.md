# File Encoding Guardian

Five explicit native WorkSwarm tools safely handle legacy-encoded text: `encoding_read`, `encoding_write`, `encoding_edit`, `encoding_grep`, and `encoding_undo`. No MCP connector, Node runtime, account, API key, or hosted service is required.

The Plugin preserves BOM and line-ending style, refuses characters the target encoding cannot represent, and does not silently convert existing files. It does not intercept WorkSwarm's built-in tools. See `THIRD_PARTY_NOTICES.md`.
