# 学习式编程指导

修改说明：2026-10-22，本次将展示信息、本文、活动教学提示词及 `learning-contribution` Skill 全部中文化，并更新来源记录。原作者为 Anthropic；本适配保留 Apache-2.0 许可与既有署名。译文保留关键教学流程，实际字节不同于早期英文版本。

在真实编程任务中解释实现取舍，准备函数或代码骨架，并邀请学习者完成一处有意义的 5–10 行关键逻辑。插件通过宿主已有的模型和工作区工具提供逐步指导。

## 主要功能

- 说明当前实现使用的概念、设计选择和取舍。
- 先准备文件、函数签名、必要上下文和明确的 TODO，再提出一个范围有限的练习。
- 将业务逻辑、错误处理策略或算法选择等有意义的决定留给学习者，并等待其输入。
- 收到学习者的代码后，按用户要求继续讨论、审阅并运行宿主允许的检查。
- 对例行配置、明显的样板代码等场景，不刻意制造练习。

## 安装与使用

### 在 JiuwenSwarm 中本地测试

1. 在扩展面板选择“创建 → 上传文件”，导入 `learning-output-style-1.0.4-native-test.zip`。
2. 确认插件版本为 `1.0.4`，启用插件，在使用原生 JiuwenSwarm/openJiuwen Harness 的新编程对话中选中它。
3. 提出一个具体的小功能任务，例如：

   > 带我实现一个 Python 重试函数：先解释固定延迟和指数退避的取舍，创建 `learning_demo/retry_demo.py` 的函数骨架，留一处关键延迟策略让我完成，并等我输入。

4. 检查是否给出了具体文件、函数和 TODO，是否解释了关键取舍，以及是否在填入该逻辑前等待你。
5. 提交自己的实现，再要求宿主审阅并执行适当检查。运行命令和文件修改仍遵守宿主的权限与项目规则。

也可明确调用 `learning-contribution`，要求围绕当前功能准备一处有意义的代码贡献。

### 通过 Agentic Hub 安装

此流程仅适用于对应版本实际通过平台审核并可获取之后：从 Agentic Hub 下载，在兼容的 JiuwenSwarm 宿主中安装和启用，然后在新对话中选中插件并提出任务。发布包文件名为 `learning-output-style-1.0.4.zip`。

市场 ZIP 使用 `learning-output-style/plugin.yaml` 外层和 `learning-output-style/learning-output-style/` 内层结构。本地测试 ZIP 直接放置相同的内层载荷，适用于宿主文件导入入口。两者载荷文件一致，ZIP 哈希不同。

## 必要依赖

- 支持 `prompt_sections` 和 Skill 加载的 JiuwenSwarm/openJiuwen 原生宿主。
- 宿主中已配置且可用的模型，以及任务所需的文件、编辑和测试权限。
- 插件不新增外部账号、API 密钥、MCP 连接、Python/Node 软件包或 Bash 运行时依赖；宿主及模型服务仍受其自身配置和使用条件约束。

## 适用范围与限制

本插件用于实际功能开发过程中的交互教学。独立代码手册、导读和带检查点的上手教程，优先复用 `code-analysis-toolbox` 的 `hands-on-tutorial-design` 能力；该资产为可选项，不会被自动安装。

本插件不提供完整课程体系、学习日程或多角色教学团队。它加载的是模型提示词，不能保证每次回复严格遵循全部教学步骤；实际行为还受到模型、对话上下文和其他已启用能力的影响。

教学上下文通过原生 `prompt_sections` 加载，未执行上游的 Bash Hook。除已验证的原生宿主路径之外，其他 Harness 实现的兼容性尚未验证。需要检查是否关闭生效时，请使用未选中该插件的新对话；旧对话仍可能受已有历史影响。

## 版本说明

当前中文版本包含活动教学提示词和 Skill 的中文译文，默认以中文讲解、邀请和反馈；用户明确要求其他语言时遵从其要求。技术 slug `learning-output-style`、Skill 标识、路径、代码语法及核心教学流程保留。原始英文来源保存在仓库审查证据中，其 SHA-256 与中文载荷 SHA-256 分开记录；原始许可及署名文件保持原文。

## 来源与许可

改编来源：Anthropic 的 `learning-output-style`，上游版本 `1.0.0`，固定提交 `d1adba47161a271799de7b548225d929310046bd`。

来源链接：https://github.com/anthropics/claude-plugins-official/tree/d1adba47161a271799de7b548225d929310046bd/plugins/learning-output-style

完整 Apache-2.0 许可见 `licenses/claude-plugins-official/LICENSE`；署名、覆盖材料及修改说明见 `THIRD_PARTY_NOTICES.md` 和 `NOTICE`。已核对的上游根目录及插件子目录未提供适用的 NOTICE 文件，本适配保留既有改编声明，不虚构上游 NOTICE。本包不表示获得 Anthropic 官方背书，也不改变上游许可。
