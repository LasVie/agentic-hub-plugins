# Code Simplifier / 代码简化

Package version **1.0.1** (2026-10-22): repackaged for local testing at Cai Zhenze's
request. The skill instructions are byte-identical to the supplied 1.0.0 package.
Only the package version, installation documentation, marketplace wrapper, and
bundled attribution/license paths changed in this repack. See
[THIRD_PARTY_NOTICES.md](THIRD_PARTY_NOTICES.md).

For **JiuwenSwarm → Create from file**, use `code-simplifier-1.0.1-native.zip`,
whose root contains `manifest.json`. The repository/Hub package is
`code-simplifier-1.0.1.zip`; it has the required
`code-simplifier/plugin.yaml` and `code-simplifier/code-simplifier/` layout.
Both ZIPs carry exactly the same inner payload. The current JiuwenSwarm local
importer recognizes a manifest at the root or one level below it, so import
the native ZIP or the extracted inner payload, rather than the marketplace ZIP.

版本 **1.0.1**：保留技能提示词，补齐包装与来源声明。JiuwenSwarm 本地“上传文件创建”
使用 `code-simplifier-1.0.1-native.zip`；市场标准包为 `code-simplifier-1.0.1.zip`。
两个 ZIP 的内层文件内容完全一致。


A skill-only JiuwenSwarm product plugin that improves readability and
maintainability while preserving functionality. By default it focuses on code
modified in the current session and follows the target project's instructions
and language conventions.

这是仅含技能的 JiuwenSwarm 产品插件：在保持功能与行为不变的前提下提升代码的可读性和可维护性。
默认只处理本次会话修改的代码，并遵循被修改项目自身的规范。

## Install, activate, and use / 安装、启用与使用

1. Open **Extensions → Plugins** (the Plugin Marketplace). If this checkout
   already bundles **Code Simplifier / 代码简化**, open its detail and click
   **Install / 安装**. Otherwise, install its listing from the Hub, or download
   `code-simplifier-1.0.1-native.zip` and choose **Create → Create from file /
   创建 → 上传文件创建**. After importing the ZIP, find the plugin under
   **My Extensions / 我的扩展**, open its detail, and click **Install / 安装**.
2. Click **Use / 使用** to start a conversation with the plugin selected.
   Use a built-in JiuwenSwarm agent in a non-team conversation, with access to
   the project and its file-editing tools. For an existing supported conversation,
   select the installed plugin through **+ → Extensions** in the input area.
3. Send: “Use Code Simplifier to simplify the code changed in this session,
   preserving behavior and following this project's instructions.”
   For a fresh conversation, specify the files/functions or diff to simplify.
4. Review the proposed edits and the reported checks. Installation alone does
   not select the plugin for every conversation.

中文操作：扩展 → 插件 → 代码简化 → 安装 → 使用；已有对话可通过输入区的
“+ → 扩展”选择已安装插件。使用内置智能体的非团队会话，并提供项目访问权限。
示例：“使用代码简化技能优化本次会话修改的代码，保持行为不变并遵循当前项目的规范。”
新对话中请明确指定文件、函数或差异范围。

如果当前发行版未内置本插件，可从 Hub 安装，或下载 ZIP 后选择“创建 → 上传文件创建”，
再到“我的扩展”找到插件并安装。ZIP 根目录应包含 `manifest.json`、`README.md`、
`LICENSE` 和 `skills/code-simplifier/SKILL.md`。

The resource catalog discovers this directory by its `manifest.json`. Installing
a bundled package copies it to
`<data-root>/agent/workspace/plugins/plugin_packages/built_in/code-simplifier/`.
The default data root is `~/.jiuwenswarm`; `JIUWENSWARM_DATA_DIR` overrides it.
The manifest retains `source: "local"` as required by the package-authoring
validator; the catalog derives the bundled `builtin` origin from its location.
An imported ZIP is stored under
`<data-root>/agent/workspace/plugins/plugin_packages/local/code-simplifier/`.
Do not import the ZIP or create a runtime `local/code-simplifier` copy when
the checkout already bundles the same ID: the importer rejects that conflict.
Use the bundled entry's **Install** action instead. Use the product installation
flow, rather than the creator's `register_plugin.py` script, for this resource package.

内置包安装后位于运行目录的 `built_in/code-simplifier/`。不要同时在 `local/`
下创建同 ID 副本或重复导入 ZIP；应通过产品界面安装已有的内置条目。

## Behavior and limits / 行为与限制

- The manifest declares one skill with `mode: "all"`. It uses the selected host
  agent's tools, permissions, and configured model; it adds no tools, rails,
  MCP servers, or dependencies.
- The original Claude plugin defines a separate subagent and asks it to act
  proactively after edits. This port supplies a skill to the existing agent.
  It provides no Claude subagent invocation, slash command, model override,
  background hook, or guarantee of automatic use after every edit. Request it
  explicitly after selecting the plugin.
- The current product plugin path is for supported non-team, built-in agent
  conversations. Team/swarm and automatic or external Harness modes do not
  use this same plugin activation path.
- Package validation and successful skill loading do not establish the quality
  of model-generated edits or prove that program behavior is unchanged.

本插件复用当前智能体及模型，不复刻 Claude 的独立子智能体或每次编辑后的自动调用。
请选中插件后明确发出简化请求。团队、自动或外部 Harness 模式不适用同一启用链路。
包校验和技能加载成功不代表实际改写质量或行为等价已得到验证。

## Upstream and modifications / 来源与修改

- Author: **Anthropic** (`support@anthropic.com`), as credited in the upstream
  `.claude-plugin/plugin.json`; upstream plugin version: `1.0.0`.
- Source: https://github.com/anthropics/claude-plugins-official/tree/main/plugins/code-simplifier
- Pinned upstream commit: `d1adba47161a271799de7b548225d929310046bd`.
- Adapted file: [agents/code-simplifier.md](https://github.com/anthropics/claude-plugins-official/blob/d1adba47161a271799de7b548225d929310046bd/plugins/code-simplifier/agents/code-simplifier.md).
- License: [Apache-2.0](LICENSE), copied verbatim from the upstream plugin.
  No separate upstream NOTICE file was present in the plugin or repository root
  at this revision.
- Changes on **2026-10-21**: adapted the agent prompt into
  `skills/code-simplifier/SKILL.md`; removed `model: opus`; replaced fixed
  CLAUDE.md/JavaScript/React rules with applicable target-project conventions;
  replaced autonomous invocation wording with explicit skill use; clarified
  scope preservation and verification limits; added the native manifest,
  bilingual product metadata, and this README.

原作者为 Anthropic；上游许可原文保留在 LICENSE。此次迁移将提示词改为原生技能，
移除了指定模型与自动调用要求，泛化项目规范，并补充范围、验证限制及原生包元数据。
