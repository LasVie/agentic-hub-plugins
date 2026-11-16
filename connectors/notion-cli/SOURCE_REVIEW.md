# Source review

Official Notion CLI → Notion 工作区连接器 → notion-cli. Song Haoran, AH-20261116-notion-cli, 2026-11-16. Candidate ID is Not Applicable.

The launcher and Skill are independently authored against the official public CLI authentication and request documentation and Notion API references. The existing Hub Notion 1.0.0 uses manually configured credentials and the 2.5.2 stdio server. Notion 工作区助手 1.0.0 uses the API with a configured token. This task adds browser login through the official CLI and a scoped append/readback workflow. Existing catalog packages were inspected for format and scope. Their source, prompts and media are not reused.

The official ntn 0.23.30 npm archive is pinned at SHA-256 f466d18f58808d8ee58cd1f027035b14a0bdf29dffef66e83c59ce62c63b86e6. The npm metadata records git head ce61d1ada2c290b4804fed73b49daad30b84271b. The archive matched npm's SHA-512 integrity metadata. Its complete package/LICENSE.md states the MIT license and copyright of Notion Labs, Inc. It is preserved unchanged as licenses/notion-cli/LICENSE. The launcher downloads and validates the official archive and extracts only the selected, hash-checked executable. No upstream binary or trademark asset is distributed in the connector ZIP.
