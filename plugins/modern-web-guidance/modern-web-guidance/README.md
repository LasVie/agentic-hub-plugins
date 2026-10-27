# 现代网页技术指南

版本 **1.0.0**。GoogleChrome Modern Web Guidance 的 JiuwenSwarm 中文精选适配版，维护者 Gan Mingrui，不是 Google 官方发布的 JiuwenSwarm 插件。

提供 12 篇可离线检索和读取的中文指南：容器查询、`:has()` 父级样式、点击遮罩关闭弹窗、自然高度动画、单页视图过渡、LCP 图片、长任务拆分、首屏外渲染、交互后表单校验、中文输入法回车、响应式表格、深浅主题。每篇含实现要点、兼容/降级说明、检查项和固定来源。

本版复用上游 BM25 检索并增加中文分词，不是上游全部 192 条指南的翻译，也不包含语义模型。模糊长句未必命中，可换具体中文主题或 API 名称；`list` 可查看全部范围。

## 安装

需要兼容原生 Plugin / ToolCard 的 JiuwenSwarm（WorkSwarm）和 PATH 中的 **Node.js 20+**。不需要额外账号、API Key、模型下载或 npm 安装。对话模型仍使用宿主现有配置。

1. 支持市场包装格式的导入入口使用 `modern-web-guidance-1.0.0.zip`。
2. 本地入口若只接受以 `manifest.json` 为根的 ZIP，使用交付目录中的 `modern-web-guidance-1.0.0-native.zip`，两者原生载荷一致。
3. 导入后启用“现代网页技术指南”，新建或刷新会话，确认 `modern_web_guidance` 工具可见。
4. 输入：“用现代网页技术指南查询中文输入法回车误提交，读取指南再给出方案。”

提示找不到 Node.js 时，用 `node --version` 核对 20+，并重启宿主让 PATH 生效。无需 `npm install` 或 `npx ...@latest`。导入成功不等于会话已经启用插件。

## 工具用法

```json
{"action":"help"}
```

```json
{"action":"search","query":"首屏 LCP 图片优先级","limit":3}
```

```json
{"action":"retrieve","ids":["optimize-image-priority"]}
```

`list` 列出全部指南。`retrieve` 只接受真实 ID，一次最多三个。结果含上游版本 `0.0.196`、获取日期 `2026-10-27` 和来源。工具不写文件、不执行示例。

独立诊断可在原生插件目录用 PowerShell 执行：

```powershell
'{"action":"list"}' | node .\runtime\cli.mjs
```

中文命令行查询需确保输入编码为 UTF-8；宿主接口已显式使用 UTF-8。

## 人工验收

- “中文输入法回车误提交”：应读取 `ime-safe-enter-submit`，解释组合输入、Enter、Shift+Enter 和兼容判断。
- “Safari 弹窗点击遮罩关闭”：应读取 `light-dismiss-a-dialog`，说明特性检测和内部空白不误关。
- “首屏 LCP 图片”：应区分关键图片、普通首屏外图片和隐藏轮播图。
- “PostgreSQL 数据库索引”：应说明本包未覆盖，不能编造指南。
- `help` 应显示版本 1.0.0、指南数 12。保留插件版本页、实际工具调用及中文结果的原始截图。

真实 IME、辅助技术、Safari 及具体项目性能仍需在相应环境验收。兼容性是固定快照，不承诺实时正确。示例仅供参考，插件不会自动运行它们。

## 来源与许可

npm 版本固定为 0.0.196；BM25 固定到 GoogleChrome/modern-web-guidance-src 提交 `8a0a736723558e9ae484e4b6bbf3cc6a8d6ba4ad`。范围见 `THIRD_PARTY_NOTICES.md`，完整许可及上游归属文本在 `licenses/`，每份改编文件均有修改声明。
