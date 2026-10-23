# 词汇练习室

版本：1.0.0。按学习者保存英文词条、出现次数与连对掌握状态；在中文交互界面完成四选一、错词复习和导出，无需额外账号。

## 安装与打开

在 WorkSwarm「我的扩展」导入 manifest 位于根目录的 `word-vault-local-1.0.0-native.zip`，启用本插件。Agentic Hub 包装 ZIP 是单独的交付格式，外层包含 plugin.yaml，不是桌面原生导入包。

本机须有兼容的 WorkSwarm Python Tool/ToolCard SDK 和 Node.js 22.6+（或 24+），支持内置 SQLite 与 TypeScript 类型擦除。适配版使用这两个内置实验开关，不下载运行时或模型。已针对 macOS / WorkSwarm 捆绑 Node22.11 验证；其他系统须另测。Git/环境探针使用 /usr/bin 等标准系统命令。

向会话说明你要使用「词汇练习室」，提供现有工作目录绝对路径，然后调用 `word_vault_local` 的 help/status/open_ui。数据在该工作目录 `.agentic-hub-plugins/word-vault-local/`；多个目录与插件彼此独立，词库还按学习者编号区分。

open_ui 返回本机交互链接，在浏览器打开。链接含短期凭据，不要发给其他人；地址栏会移除凭据，刷新页面请重新使用完整链接。服务只监听127.0.0.1，空闲30分钟或运行4小时关闭；stop_ui显式关闭，数据保留。页面仅服务自己的静态文件与绑定目录API，不是文件服务器。

## 工具操作

- `help`：查看本工具操作说明。
- `open_ui`：为当前工作目录启动本机中文交互工作台。仅绑定127.0.0.1；完整链接含短期访问凭据，不要分享。
- `stop_ui`：关闭本插件该工作目录的界面服务，保留数据。
- `status`：learner（默认 learner-1）；返回该学习者词库、统计与最近练习，不公开未答题目的答案索引。
- `add_words`：expected_revision, learner, entries:[{term,meaning}]，每次1至50条；重复词元计次，释义修改会重置掌握状态。
- `start_quiz`：expected_revision, learner, size（1至10，默认4）, wrong_only（可选）；四个不同释义才可出题。
- `answer`：expected_revision, learner, quiz_id, question_id, option_index（0至3）；答案按本地保存的题目核对，三次连对掌握。
- `export_bank`：learner；导出该学习者词库。

所有写操作须先 status 取得当前 revision，再填写 expected_revision；遇到并发更新会拒绝覆盖，请重新读取。界面与会话工具共用同一数据，看到错误时不要假设保存成功。数据导出为JSON。

## 范围与限制

按学习者分开保存词条、出现次数与连续答对次数，提供真实计分的四选一和错词复习。释义由用户或当前会话提供，不包含拍照识词、借用的记忆卡设计、第三方词表、自动查词或语音服务。

没有额外服务账号、遥测、后台模型或远端API。浏览器只能修改本插件绑定的本地记录；Git与环境只读系统/仓库事实，插件自身的快照数据会写入上述隐藏目录。非功能需求不靠界面按钮声称完成，实际证据与已知未测范围见开发目录TEST_REPORT.md。

## 来源与许可

完整版权/许可见THIRD_PARTY_NOTICES.md及licenses/upstream/LICENSE。上游功能只迁移本说明列出的子集，不包含上游完整宿主界面或自动化能力。
