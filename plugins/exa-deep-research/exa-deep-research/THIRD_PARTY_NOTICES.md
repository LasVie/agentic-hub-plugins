# Third-party notices

This is a repository-maintained adaptation, not an official Exa release.

- Upstream: https://github.com/exa-labs/exa-mcp-server
- Version: 3.4.2; pinned commit: 0b499f095c4ca145eee07b09137641c037d58449
- Original rightsholder: Copyright (c) 2025 Exa Labs.
- License: MIT; complete text and disclaimer: `licenses/exa-mcp-server/LICENSE`.
- Reused material: search and exa-agent skills, and all search reference Markdown.
- Changes: native tool names, valid skill IDs, host-neutral delegation,
  evidence counting, credential/error handling, explicit metered-run approval,
  native manifest and openJiuwen tool adapter.
- The adapter uses the public MCP protocol; no upstream TypeScript server,
  Node packages, logos, fonts, icons or third-party result data is bundled.
- MCP SDK and jsonschema are separately installed runtime dependencies; their
  distributions supply their own license notices. They are not vendored.
- The remote Exa service is governed by its own service terms and quotas.

No upstream NOTICE or additional skill-directory license was present at the
pinned commit. This notice preserves upstream attribution and does not assign
a new license to repository-owned integration code.
