# LaTeX 引用守卫

修改说明：2026-10-22，版本 1.0.3 将展示信息和使用说明改为中文；补全 Skill、工具说明和可读提示的中文；工具接口与文献处理算法保持不变。

检查 BibTeX 文献库、补全缺失元数据，并对照文献库检查明确指定的 LaTeX 文件中的引用键。

## 主要功能

- `bib_lint`：发现重复键和缺少的必填字段；显式写入时移除后出现的重复条目并规范格式。
- `bib_fill`：按 DOI 或标题查询 Crossref，只补全空白字段。
- `cite_audit`：比较一个或多个明确指定的 TeX 文件与一个 `.bib` 文件，报告缺失引用键及未使用的条目。

## 安装与使用

在兼容 WorkSwarm/JiuwenSwarm 的扩展面板导入 `dsh-latex-guard-1.0.3-native-test.zip`，确认版本 `1.0.3`、一个 Skill 和三个工具，然后在目标会话中选中插件。

示例：“对照 references.bib 审计 paper.tex 的引用键，列出缺失和未使用条目，不修改文件。”

检查或补全时先保持 `write=false` 预览；只有用户明确要求才写入。写入前保留原文件或确保已经纳入版本控制。BibTeX 解析器无法覆盖每一个条目标记时，工具会拒绝写入，以免丢失未识别内容。

市场包 `dsh-latex-guard-1.0.3.zip` 采用外层 `dsh-latex-guard/plugin.yaml` 和内层 `dsh-latex-guard/dsh-latex-guard/`；本地测试 ZIP 直接包含相同载荷，两种 ZIP 的哈希不同。

## 必要依赖与限制

需要支持原生 Python Tool API 的宿主和本地文件权限。`bib_lint` 与 `cite_audit` 处理本地文件；只有 `bib_fill` 需要网络，会将查询用的 DOI 或标题发送给公共 Crossref 服务，无需额外账号或 API 密钥。自然语言调度使用宿主已配置的模型。

不需要 TeX 发行版、Node.js、npm、DSH 运行时或 MCP 连接。本插件不编译 LaTeX，也不验证论文内容或书目信息的学术正确性。Crossref 的可用性与匹配质量可能影响补全结果，写入前应检查预览。当前版本不包含 `latex_check`。

## 来源与许可

源自 Flan246 的 `dsh-latex-guard` 移植。固定来源、实际复用范围与完整 MIT 许可位置见 `THIRD_PARTY_NOTICES.md` 及随包许可目录；原文与署名继续保留。本说明不改变上游许可，也不表示获得上游背书。
