# 小说创作台

版本：1.0.0。管理本地小说项目、人物、章节与修订历史；在中文编辑器中添加可重新定位的原文批注，不自动生成或改写正文。

## 安装与打开

在 WorkSwarm「我的扩展」导入 manifest 位于根目录的 `story-workbench-1.0.0-native.zip`，启用本插件。Agentic Hub 包装 ZIP 是单独的交付格式，外层包含 plugin.yaml，不是桌面原生导入包。

本机须有兼容的 WorkSwarm Python Tool/ToolCard SDK 和 Node.js 22.6+（或 24+），支持内置 SQLite 与 TypeScript 类型擦除。适配版使用这两个内置实验开关，不下载运行时或模型。已针对 macOS / WorkSwarm 捆绑 Node22.11 验证；其他系统须另测。Git/环境探针使用 /usr/bin 等标准系统命令。

向会话说明你要使用「小说创作台」，提供现有工作目录绝对路径，然后调用 `story_workbench` 的 help/status/open_ui。数据在该工作目录 `.agentic-hub-plugins/story-workbench/`；多个目录与插件彼此独立，词库还按学习者编号区分。

open_ui 返回本机交互链接，在浏览器打开。链接含短期凭据，不要发给其他人；地址栏会移除凭据，刷新页面请重新使用完整链接。服务只监听127.0.0.1，空闲30分钟或运行4小时关闭；stop_ui显式关闭，数据保留。页面仅服务自己的静态文件与绑定目录API，不是文件服务器。

## 工具操作

- `help`：查看本工具操作说明。
- `open_ui`：为当前工作目录启动本机中文交互工作台。仅绑定127.0.0.1；完整链接含短期访问凭据，不要分享。
- `stop_ui`：关闭本插件该工作目录的界面服务，保留数据。
- `status`：读取项目、人物、章节、原文批注与修订历史。
- `create_project`：expected_revision, name；一个工作目录一个项目，不覆盖已有项目。
- `save_character`：expected_revision, id, name, role, goal；保存/修改人物设定。
- `save_chapter`：expected_revision, id, title, content, chapter_revision（更新已有章节时必填其hash）；保存旧版本并重新定位批注。
- `annotate`：expected_revision, chapter_id, chapter_revision, quote, note, start_hint/end_hint（可选，JavaScript UTF-16索引）；仅可批注已保存原文。
- `resolve_annotation`：expected_revision, annotation_id；标记解决并保留记录。
- `export_project`：导出完整项目与历史；不生成正文。

所有写操作须先 status 取得当前 revision，再填写 expected_revision；遇到并发更新会拒绝覆盖，请重新读取。界面与会话工具共用同一数据，看到错误时不要假设保存成功。数据导出为JSON。

## 范围与限制

保存小说项目、人物设定、章节正文、原文批注与旧版本。作为既有小说写作技能的本地编辑伴随工具，不重复写作语料或自动生成正文，不包含上游整套后端与智能体。

没有额外服务账号、遥测、后台模型或远端API。浏览器只能修改本插件绑定的本地记录；Git与环境只读系统/仓库事实，插件自身的快照数据会写入上述隐藏目录。非功能需求不靠界面按钮声称完成，实际证据与已知未测范围见开发目录TEST_REPORT.md。

## 来源与许可

完整版权/许可见THIRD_PARTY_NOTICES.md及licenses/upstream/LICENSE。上游功能只迁移本说明列出的子集，不包含上游完整宿主界面或自动化能力。
