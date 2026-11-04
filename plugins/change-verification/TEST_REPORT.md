# 变更影响与回归检查台 1.0.0 开发者测试

日期：2026-11-02。任务 `AH-20261102-change-verification`，候选 `CAND-DSH-145`，负责人 Wang Jie。下文保留开发者检查记录；用户已完成当前包简化流程并授权 PR，实际结果和范围追加在文末。十一张原图已按用户明确授权公开上传并核对，进入 GitHub PR 交付；不上传 Hub。

## 环境与真实来源

macOS，WorkSwarm 自带 Node 22.11.0，系统 Python 3.9.6、本地 Git、Chrome 156.0.8078.74。开发期独立 MCP SDK 和 Playwright 来自已有 `upstream/claude-annotate/node_modules`，不打入运行载荷。上游固定提交 `b4f3c8e3be2b756ad9966463a65331e69fdee5f8`，核心版本 0.3.5。只在新下载审查样本的 core 目录安装开发依赖，忽略生命周期脚本；实际 TypeScript 5.9.3、Vitest 3.2.7。没有修改全局环境、Conda base 或 WorkSwarm 应用文件。

## 已执行

1. 上游 core：`vitest run tests/deps-languages.test.ts tests/deps-index-filter.test.ts`：**11/11 通过**。覆盖多语言引用、样式关联、两层扩散及依赖/构建目录过滤。没有宣称验证整个上游设计、崩溃或外部缺陷模块。
2. `node --test plugins/change-verification/tests/runtime.test.mjs`：**17/17 通过**。真实创建独立演示 Git 提交，核对直接项、删除项旧依赖、提交差异片段、未提交内容不代替提交、Git 字面路径、层数/空变更、只读配置与工作区、不合法根/引用、受限文件、二进制/符号链接/大小预算、变更数量拒绝、缺失源码对象拒绝、结果/证据哈希持久化、修订冲突、并发更新、步骤完善边界、导出转义和 CSV 防公式。
3. 源码实际声明的 `python3 ../../runtime/launch.py`，在 `PATH=/usr/bin:/bin` 下，通过独立 MCP SDK 握手，六个工具可调用，Chrome 受控浏览器实际操作：**39 项断言通过**。没有运行时依赖安装，stderr 为空，浏览器无运行错误。
4. 浏览器实际保存一个开发者演示失败、一个跳过，其他三项保持未验证；保存截图哈希与原始上传字节一致，刷新与新 MCP 进程能读回。实际下载 HTML，离线图片可解码，备注 HTML 没有执行；导出四份文件并验证字节哈希。
5. HTTP 实际检查缺令牌、跨站来源、错误 Host、GET 写入、错误内容类型与报告路径穿越拒绝。首次开发测试使用 fetch 自定义 Host 时该请求头被客户端重写，断言失败；改用原始 HTTP 客户端后确认真实 Host 拒绝。该测试工具修正没有绕过服务检查。
6. 对下载的真实上游，实际比较 `24a6540e7cba06a357925cc0371124aa50e840bd` → `b4f3c8e3be2b756ad9966463a65331e69fdee5f8`：两个快照各访问 378 路径、索引 334 文件 / 2781818 字节、跳过 41 个保护或不支持类型及 3 个超限文件，返回 11 个直接变更、0 个间接候选，全部未验证。对比前后 `.git/config` 与工作区状态哈希相同。首次实际运行发现 `ls-tree -l` 对部分克隆缺失对象返回 BAD；已修正为区分不参与索引的资料与所需源码，缺所需源码时中文拒绝，不拉取或回退工作区。新增真实删除临时演示仓库 blob 的负例确认该边界。该真实 release 比较不表示验证上游业务功能。

开发者自动化截图与临时报告仅是局部验证证据，不能代替用户的 WorkSwarm 安装/工具路由、系统打开浏览器或验收截图。

## 最终 ZIP 检查

标准包 SHA-256：`e1ca8c8f2ef5e27f518f950fbf62b6da041bc32db118e3d9cde058d74a31faaa`。

WorkSwarm 测试包 SHA-256：`4d760812e23fe870e32a8fba986df5eaf332fd3bdce579f69ebc3052712dd40d`。

- `python3 tools/asset_release.py check plugins/change-verification` 通过，`pack` 实际生成标准包；宿主测试包从标准包同一内层导出，25 文件与源码、两份 ZIP、解压目录逐文件字节哈希一致。
- 解压路径 `local-tests/change-verification/1.0.0/extracted/change-verification`，通过环境变量 `CHANGE_VERIFICATION_PAYLOAD` 指向该目录，重新执行同一运行测试：**17/17 通过**。
- 独立 SDK/Chrome 测试以该解压目录为入口、从声明的 MCP cwd 和启动器运行：**39 项断言通过**；包括冷启动、实际分析、中文界面、HTTP 负例、结果/截图/哈希、导出离线图片、跨进程持久化，stderr 与浏览器运行错误均为空。不是 WorkSwarm 客户端实测。
- 解压中文 README、Skill、界面、默认文案与 UTF-8 检查通过；实际源文件与完整许可 SHA-256 核对通过，未混入 node_modules、pyc、隐藏目录或开发测试。
- `python3 tools/asset_release.py check-repo`：最初为 **54 source assets / 64 release ZIPs**；提交时基于最新 main（含另一成员新合入资产）再次检查为 **55 source assets / 65 release ZIPs**，结构通过。
- 提交前仓库 Python 回归实际运行 **580 项，490 通过，90 项因其他资产的可选依赖/平台条件跳过**，耗时 27.220 秒。新增 `tests/test_change_verification.py` 将本插件 17 项 Node/Git 回归接入仓库测试入口，该入口已包含在本轮完整回归中。未为其他资产额外补齐环境或重跑其联网 MCPB 专项；整体远程 CI 尚未创建运行。
- 记录：`tests/evidence/developer-checks.json`；真实上游读取统计 `tests/evidence/upstream-readonly.json`。开发者自动化图片没有作为用户验收截图提交。

## 当前包用户测试与交付核对

用户于 2026-11-02 14:52:33.138 Asia/Singapore 核对十一张截图后要求“ok啊，那继续吧，提交pr”。采用会话中简化后的步骤，`src/auth.ts` 保存跳过及实际备注，其余四项未验证；修订1。工具读回、中文报告及新对话重开均与实际记录一致。旧文档两项预期与后续简化指导的差异已在载荷外文档纠正，不要求用户为满足旧提示词重写结果。

十一张原图逐字节保存，无缩放、裁剪或转换；最后三张为新对话恢复。只读核对宿主安装的25个运行文件均匹配已测 ZIP，磁盘上的报告 ID、两个提交、修订、状态和备注匹配截图。完整确认见 USER_TEST_CONFIRMATION.md；图片清单见 evidence.json。用户本轮未上传条目图片，图片保存/内嵌和其他状态分支仅有开发者独立测试，不混作用户证据。

已保留明确的当前包完成确认；十一张原图托管于 https://github.com/dashingsss/agentic-hub-plugins/issues/5 ，公开下载的字节哈希均与收到的原图一致，随后在交付 PR 展示。候选仍 Planned，负责人接受独立待处理。不宣称演示业务已通过回归或完整静态覆盖。Windows 未验证；Linux 未实际执行本轮浏览器流程。项目执行、外部服务与 DSH 注入不属于本次范围。
