# 本机环境探针

版本：1.0.0。主动观测本机系统、标准位置工具链和 TCP 监听端口，保存与比较快照，提供中文筛选界面；不结束进程、不读取密钥。

## 安装与打开

在 WorkSwarm「我的扩展」导入 manifest 位于根目录的 `environment-inspector-1.0.0-native.zip`，启用本插件。Agentic Hub 包装 ZIP 是单独的交付格式，外层包含 plugin.yaml，不是桌面原生导入包。

本机须有兼容的 WorkSwarm Python Tool/ToolCard SDK 和 Node.js 22.6+（或 24+），支持内置 SQLite 与 TypeScript 类型擦除。适配版使用这两个内置实验开关，不下载运行时或模型。已针对 macOS / WorkSwarm 捆绑 Node22.11 验证；其他系统须另测。Git/环境探针使用 /usr/bin 等标准系统命令。

向会话说明你要使用「本机环境探针」，提供现有工作目录绝对路径，然后调用 `environment_inspector` 的 help/status/open_ui。数据在该工作目录 `.agentic-hub-plugins/environment-inspector/`；多个目录与插件彼此独立，词库还按学习者编号区分。

open_ui 返回本机交互链接，在浏览器打开。链接含短期凭据，不要发给其他人；地址栏会移除凭据，刷新页面请重新使用完整链接。服务只监听127.0.0.1，空闲30分钟或运行4小时关闭；stop_ui显式关闭，数据保留。页面仅服务自己的静态文件与绑定目录API，不是文件服务器。

## 工具操作

- `help`：查看本工具操作说明。
- `open_ui`：为当前工作目录启动本机中文交互工作台。仅绑定127.0.0.1；完整链接含短期访问凭据，不要分享。
- `stop_ui`：关闭本插件该工作目录的界面服务，保留数据。
- `status`：读取已保存观测快照。
- `probe`：expected_revision；主动执行只读本机标准位置工具 --version 与 lsof TCP监听观测。失败保持unavailable，不代表系统没有服务。
- `compare`：before_id, after_id；比较两份不同的已保存快照，端口不可观测时不推断增减。
- `export_snapshots`：导出已保存快照，不读取密钥/配置文件/用户名/设备名/网卡地址。

所有写操作须先 status 取得当前 revision，再填写 expected_revision；遇到并发更新会拒绝覆盖，请重新读取。界面与会话工具共用同一数据，看到错误时不要假设保存成功。数据导出为JSON。

## 范围与限制

只读观测本机操作系统、标准位置工具版本与TCP监听端口，明确区分可用、未观测与失败，保存及比较快照。不会结束进程、修改系统、读取密钥或配置文件。仅当前macOS已验证，Linux与Windows不作已测试保证。

没有额外服务账号、遥测、后台模型或远端API。浏览器只能修改本插件绑定的本地记录；Git与环境只读系统/仓库事实，插件自身的快照数据会写入上述隐藏目录。非功能需求不靠界面按钮声称完成，实际证据与已知未测范围见开发目录TEST_REPORT.md。

## 来源与许可

完整版权/许可见THIRD_PARTY_NOTICES.md及licenses/upstream/LICENSE。上游功能只迁移本说明列出的子集，不包含上游完整宿主界面或自动化能力。
