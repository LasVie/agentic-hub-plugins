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


## 中文版本修改说明（2026-10-22）

版本 `1.0.2` 将展示信息与使用说明中文化；保留技术标识、原始许可和署名。 MCP 生成器及三个 Skill 的插件版本标记同步更新，示例工程仍为 0.1.0。 本说明不替代或改变上方原始许可条款。

## 中文运行内容补全（2026-10-22）

本次将三个 Skill 的默认交流与生成内容语言设为简体中文，并将生成器的规划、帮助、错误、许可检查提示以及 App/MCPB 模板的工具说明、校验提示、界面和构建消息中文化。四个改编 JavaScript 模板保留原始出处和修改声明，并追加本次修改说明。协议标识、schema 键、依赖版本及锁文件、原始许可全文不变；示例工程仍为 0.1.0。第三方 SDK/CLI 原生的协议诊断和许可文本可能为英文，分发时不应改写原文。


## 中文运行版本 1.0.3（2026-10-22）

按最新中文交付要求翻译实际 Skill、工具说明、帮助及可读提示；模板与资料按实际复用范围记录。技术标识和原始法律声明保持原值。最终包及宿主验证范围见资产测试记录。


## 中文运行版本 1.0.4（2026-10-22）

按最新中文交付要求翻译实际 Skill、工具说明、帮助及可读提示；模板与资料按实际复用范围记录。技术标识和原始法律声明保持原值。最终包及宿主验证范围见资产测试记录。
