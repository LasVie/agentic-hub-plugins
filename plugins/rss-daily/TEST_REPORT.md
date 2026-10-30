# 功能测试记录：资讯晨报助手 1.0.0

日期：2026-10-27；负责人 Wang Jie；任务 AH-20261027-rss-daily；候选 CAND-DSH-266。此处是开发测试，不是用户在 WorkSwarm 中的验收确认。

## 环境与边界

- macOS；系统 Python 3.9.6；已有独立开发环境 Python 3.11.17。不创建或修改 Conda base，不安装全局包。
- WorkSwarm 自带 Node 22.11.0，仅作为独立 MCP 测试客户端运行器；测试客户端使用已有 MCP JavaScript SDK。SDK 和 Node 不进入插件载荷，也不是插件运行依赖。
- 插件服务、后台抓取、锁和状态只使用 Python 标准库；演示及真实测试状态在系统临时目录，测试后清理，不更改宿主注册表或已安装插件。
- 未运行上游 DSH 安装脚本，没有声称测试上游所有原版功能。本次验证实际改编后的载荷。

## 已执行的源码测试

在独立工作目录 `agentic-hub-plugins-rss-daily` 执行：

```sh
PYTHONDONTWRITEBYTECODE=1 /usr/bin/python3 -B -m unittest discover -s plugins/rss-daily/tests -p 'test_*.py' -v
PYTHONDONTWRITEBYTECODE=1 /Users/dashing/Desktop/huaweisg/.environments/annotate-test/bin/python -B -m unittest discover -s plugins/rss-daily/tests -p 'test_*.py' -v
```

两套 Python 均为 **43 项通过**。覆盖：

- RSS2/Atom 实际解析、时区/过期过滤、网址与近似标题去重、五条演示原始记录得到三条新素材。
- 中文落稿、绑定原始来源和发布时间、拒绝伪造或重复素材 ID、拒绝自行注入网址、拒绝纯英文摘要。
- `DRAFT` 与 `FINALIZED` 不写确认历史；明确确认后只消费选中条目；重复/并发确认不重复记账。
- 四个并发抓取请求复用一个批次；跨实例恢复状态、十四天历史过期、新批次去重、演示与真实状态隔离。
- 原子写入、0600 文件/0700 数据目录、保留损坏文件、后台启动失败后可重试、过时运行状态转失败。
- 公开 HTTPS 限制、私网解析拒绝、重定向到私网拒绝、TLS 保留证书/域名校验、XML/UTF-16 实体拒绝、512 KiB 限制、HTML 清理与 Markdown 转义。
- 部分源失败保留错误并写入日报、全部源失败不能冒充空日报、未处理真实批次禁止替换源。
- stdio UTF-8 JSON 无日志污染、错误输入后继续请求、协议初始化和五工具列举、载荷运行前后内容不变。

上述网络失败及安全分支使用明确 mock；不冒充实际网络攻击或所有站点的兼容性验证。测试初次有一个测试程序误用 `mock_results`，已修正为检查实际 SSLContext 并完整重跑；不是忽略失败。

## 独立 MCP 客户端与真实网络

```sh
RSS_TEST_MCP_SDK=/Users/dashing/Desktop/huaweisg/upstream/claude-annotate/node_modules/@modelcontextprotocol/sdk/dist/esm \
  /Applications/WorkSwarm.app/Contents/Resources/node-runtime/bin/node \
  plugins/rss-daily/tests/mcp_smoke.mjs plugins/rss-daily/rss-daily --live
```

实际通过 **27 条断言**：按包内 MCP 配置与相对工作目录启动、真实初始化/列举/调用、两个独立客户端、并发批次、三条演示中文落稿、提前确认/伪造素材拒绝、确认幂等、重启恢复、确认后刷新零条、真实与演示隔离。

实网读取窗口 168 小时：少数派读取 10 条、有效 10；Solidot 13/13；Hacker News 20/19，过滤 1 条。三个源都返回并成功解析，按每源最多两条得到 **6 条实际候选素材，DRAFT，历史为零**。网络记录是本次时间点的真实返回，不保证未来源永远可用，也没有把自动抓取当作模型事实核查。

另执行不联网 MCP 闭环，23 条断言通过。协议依据为官方 [MCP 生命周期](https://modelcontextprotocol.io/specification/2025-03-26/basic/lifecycle) 与 [工具协议](https://modelcontextprotocol.io/specification/2025-03-26/server/tools)，独立 SDK 可正常协商和关闭连接。

## 仓库回归

```sh
PYTHONDONTWRITEBYTECODE=1 /Users/dashing/Desktop/huaweisg/.environments/annotate-test/bin/python -B -m unittest discover -s tests -v
```

实际 **491 项，394 通过、97 跳过、0 失败**；新增入口会在隔离进程运行上述 43 项，不将一套测试混入其他插件的模块命名空间。跳过项保持仓库原有条件，没有补齐不相关插件环境。

## 宿主与打包验证边界

WorkSwarm 内置 `plugin-creator/validate_plugin.py --no-hot-load` 初次检查发现默认输入与首条快捷输入不一致，已在打包前修正。复核 **L0 为 0 错误/0 警告**；L1 仍有 1 错误，原文为“本 skill 不生成 mcps，不应声明该字段”，L2 明确跳过，整体退出码 1。该创建器明确拒绝所有 `mcps` 字段，适用范围是其生成的 skills/tools/rails 包；不能把它当作 MCP 插件宿主接入验证。保留 MCP 功能，不修改校验器、不绕过注册、不手改宿主配置。宿主是否能实际接入本包，仍需下一步 UI 导入和工具调用验证。

开发交接时尚未执行用户的扩展 UI 导入、模型中文编辑、对话内工具调用或原始截图验收，因此当时未声称 WorkSwarm 已加载/验收，没有 PR、远程推送或 Hub 操作。随后收到的当前包用户结果见文末。

## 最终归档复核

已使用仓库工具实际执行 `check plugins/rss-daily`、`pack plugins/rss-daily`，再由 `tests/build_workswarm.py` 从规范归档提取**同一载荷**生成 WorkSwarm 原生 ZIP。不是另一套源码，也未把外层 Hub 包误当作原生安装包。

| 包 | SHA-256 |
| --- | --- |
| `releases/agent-plugin/rss-daily/1.0.0/rss-daily-1.0.0.zip`（规范交付包） | `1253b65bb649ae2839dc8bc31c14d723c02468f7403af1bc27496ac05e2754ad` |
| `local-tests/rss-daily/1.0.0/rss-daily-1.0.0-workswarm.zip`（工作区测试包） | `2f8815b00cb46c6907de62781c0574b2ee4c58e70aecaafbeb98bf73dc247588` |

已逐文件校验：源码载荷、规范包内层、原生 ZIP 与实际解压内容 **13 个文件完全相同**；全部可按 UTF-8 解码；许可哈希与固定上游一致；不含测试脚本、任务文档、开发缓存、环境、SDK 或用户状态。中文 README、Skill、显示字段、工具描述、主要成功/错误返回已实际检查；原始 MIT 声明与 API 标识保留。

对 `local-tests/rss-daily/1.0.0/extracted/rss-daily` 实际运行：

```sh
RSS_DAILY_PAYLOAD=/Users/dashing/Desktop/huaweisg/local-tests/rss-daily/1.0.0/extracted/rss-daily \
  PYTHONDONTWRITEBYTECODE=1 /usr/bin/python3 -B -m unittest discover \
  -s plugins/rss-daily/tests -p 'test_*.py' -v
RSS_TEST_MCP_SDK=/Users/dashing/Desktop/huaweisg/upstream/claude-annotate/node_modules/@modelcontextprotocol/sdk/dist/esm \
  /Applications/WorkSwarm.app/Contents/Resources/node-runtime/bin/node \
  plugins/rss-daily/tests/mcp_smoke.mjs ../local-tests/rss-daily/1.0.0/extracted/rss-daily --live
```

解压载荷 **43 项功能测试通过、独立 SDK 27 条断言通过**。三源实网结果：少数派 10/10、Solidot 20/20、Hacker News 20/19，得到 6 条候选；与首次源码测试时动态 feed 条数不同，保留各次实际结果而不修改为一致。

`check-repo` 实际通过，44 个源码资产、53 个规范归档。规范包、原生包的可复现哈希与重新解压对比在交接前再次复核。规范包的 `artifact.json` 会记录本测试报告及 SOURCE_REVIEW 的最终哈希；这类开发记录更新不改动已冻结的 13 文件载荷。

## 用户实测补充：2026-10-27 17:56 UTC+8

Wang Jie 已按 `WORKSWARM_TEST_PROMPTS.md` 提供测试 1–4 的九张实际 WorkSwarm 截图，并要求核对效果正确即提交 PR。当前原生测试包与规范交付包哈希未变；已只读核对宿主安装的十三个载荷文件，全部一致。

截图与实际状态交叉核对符合预期：中文演示编排先等待确认，明确确认后三条历史；重复确认不增加数量或改变时间；新会话恢复状态，刷新后 EMPTY 且历史保留；demo/live 隔离；真实三源抓取六条，中文日报最终为 FINALIZED、真实历史 0，未自动确认阅读。

用户原话、时间、批次与确认记录见 `USER_TEST_CONFIRMATION.md`；九张原图清单见 `evidence.json`。只补充载荷外开发记录，不改已测试 ZIP。此确认可进入 PR，不替代上游维护者合并或 Project Lead 接受；没有 Hub 操作。

提交前已在最新 main `2e5aedd` 基础上复跑：插件 43 项通过；仓库 491 项，394 通过、97 跳过、0 失败。九张原图已上传至提交者有写权限的公开 fork，再下载逐张核对 SHA-256，与当前对话保存的 PNG 完全一致；随后会直接附在本次 PR 证据评论中。添加的 Git 属性仅保留 RSS 文件原始字节，不更改载荷或 ZIP。

此时最新 main 已新增两个其他资产，`check-repo` 为 **46 个源码资产、55 个规范归档，检查通过**；不改写前述开发交接时的 44/53 记录。
