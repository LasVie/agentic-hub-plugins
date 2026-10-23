# 流程执行台

版本：1.0.0。校验多阶段流程模板，冻结每次运行快照，以实际文件 SHA-256 记录环节完成证据，提供中文交互看板。

## 安装与打开

在 WorkSwarm「我的扩展」导入 manifest 位于根目录的 `process-workbench-1.0.0-native.zip`，启用本插件。Agentic Hub 包装 ZIP 是单独的交付格式，外层包含 plugin.yaml，不是桌面原生导入包。

本机须有兼容的 WorkSwarm Python Tool/ToolCard SDK 和 Node.js 22.6+（或 24+），支持内置 SQLite 与 TypeScript 类型擦除。适配版使用这两个内置实验开关，不下载运行时或模型。已针对 macOS / WorkSwarm 捆绑 Node22.11 验证；其他系统须另测。Git/环境探针使用 /usr/bin 等标准系统命令。

向会话说明你要使用「流程执行台」，提供现有工作目录绝对路径，然后调用 `process_workbench` 的 help/status/open_ui。数据在该工作目录 `.agentic-hub-plugins/process-workbench/`；多个目录与插件彼此独立，词库还按学习者编号区分。

open_ui 返回本机交互链接，在浏览器打开。链接含短期凭据，不要发给其他人；地址栏会移除凭据，刷新页面请重新使用完整链接。服务只监听127.0.0.1，空闲30分钟或运行4小时关闭；stop_ui显式关闭，数据保留。页面仅服务自己的静态文件与绑定目录API，不是文件服务器。

## 工具操作

- `help`：查看本工具操作说明。
- `open_ui`：为当前工作目录启动本机中文交互工作台。仅绑定127.0.0.1；完整链接含短期访问凭据，不要分享。
- `stop_ui`：关闭本插件该工作目录的界面服务，保留数据。
- `status`：读取当前模板与运行记录。
- `validate_template`：template 为 JSON对象：process:{name}, phases:[{id,name,links:[{id,name,prompt,on_success}]}]；支持 next/end/break/goto:环节id。
- `save_template`：expected_revision, template；校验后保存，既有运行不会换用新模板。
- `start_run`：expected_revision, run_id；创建唯一运行编号并冻结模板。
- `complete_step`：expected_revision, run_id, step_id, note, evidence_files（1至10个工作区内相对文件路径）；记录真实文件SHA-256后流转，不能跳步骤。
- `resume_run`：expected_revision, run_id；显式恢复暂停运行。
- `export_process`：导出模板、快照与文件证据；不执行命令、模型或代理。

所有写操作须先 status 取得当前 revision，再填写 expected_revision；遇到并发更新会拒绝覆盖，请重新读取。界面与会话工具共用同一数据，看到错误时不要假设保存成功。数据导出为JSON。

## 范围与限制

保存用户定义的多阶段JSON模板与独立运行快照，校验环节流转，以工作目录内的真实文件哈希记录完成证据，提供交互看板。没有后台调度、自动模型评分、自动智能体或任意命令执行。

没有额外服务账号、遥测、后台模型或远端API。浏览器只能修改本插件绑定的本地记录；Git与环境只读系统/仓库事实，插件自身的快照数据会写入上述隐藏目录。非功能需求不靠界面按钮声称完成，实际证据与已知未测范围见开发目录TEST_REPORT.md。

## 来源与许可

完整版权/许可见THIRD_PARTY_NOTICES.md及licenses/upstream/LICENSE。上游功能只迁移本说明列出的子集，不包含上游完整宿主界面或自动化能力。
