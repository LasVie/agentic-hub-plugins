# Third-party notices

Upstream: Anthropic's mcp-server-dev, in anthropics/claude-plugins-official.
Pinned revision: d4226d062928f8d9505dbdeadd10217d23361052.
Source: https://github.com/anthropics/claude-plugins-official/tree/d4226d062928f8d9505dbdeadd10217d23361052/plugins/mcp-server-dev

Upstream author metadata says "Anthropic", support@anthropic.com. The inspected plugin files contain no additional copyright-holder/year notice; the LICENSE appendix contains literal placeholders, which have been preserved unchanged, not asserted as a copyright claim.

License: Apache License 2.0, full unchanged text in licenses/claude-plugins-official/LICENSE.
No applicable upstream NOTICE exists at the pinned repository root, plugin root or selected subdirectories.

Adapted material:
- skills/build-mcp-app/SKILL.md: adapted from the same upstream path; narrowed to tested UI-resource/stdio development.
- skills/build-mcpb/SKILL.md: adapted from the same upstream path; runtime prerequisite corrected, replaced examples.
- templates/app/server.mjs: derived from the tool/resource registration examples in upstream skills/build-mcp-app/SKILL.md; replaced business logic, transport and HTML loading.
- templates/app/widget.mjs and templates/app/build.mjs: adapted browser App lifecycle and local bundling patterns from upstream skills/build-mcp-app/SKILL.md; use a compiled ESM bundle and safe text output.
- templates/mcpb/server.mjs: adapted the standard SDK stdio registration pattern in upstream skills/build-mcpb/SKILL.md; replaced local filesystem access with bounded addition.

Prominent modification statements appear on each adapted file. No brand images, fonts, datasets, logos, third-party service credentials or precompiled SDKs are included.

Other files are repository-authored integration and test material; no new repository-wide license or copyright ownership is asserted. The Apache license above applies to the upstream material, not automatically to all repository-authored files. New-code licensing remains a controller decision.

Generated examples install separately pinned @modelcontextprotocol/sdk 1.32.1, @modelcontextprotocol/ext-apps 1.7.5, zod 4.6.7 and (build-only) esbuild 0.28.1, plus lockfile dependencies. sdk, zod and esbuild have MIT texts. ext-apps metadata says MIT but its actual LICENSE describes a transition: Apache-2.0 for new/relicensed contributions, retained MIT for others, and CC-BY-4.0 for documentation (no documentation is copied). Generated builds collect the complete actual installed license/NOTICE texts in licenses/npm; review the full scope before redistributing. Their implementation is not bundled in this plugin ZIP. Preserve each installed dependency's actual LICENSE and required notices in any generated-project distribution. SDK services, trademarks and host compatibility are separate from this license.

When copied into a generated example, the paths above identify the plugin template source, not files necessarily present in that example.
