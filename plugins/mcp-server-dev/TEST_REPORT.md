# Patch verification: mcp-server-dev 1.0.1

User testing was explicitly completed on 2026-10-22 in the current conversation, with an original full-resolution screenshot and authorization to submit/merge the marketplace version. See USER_TEST_CONFIRMATION.md for both ZIP hashes, the screenshot hash and the reported host test environment/results. The confirmed marketplace ZIP is unchanged. After rebasing onto current main, repository discovery ran 50 tests: 24 passed and 26 unrelated Deckaura tests skipped because that SDK is unavailable in the local test environment. Repository format/release checks passed. MCP Apps visual rendering and remote deployment remain declared exclusions. GitHub delivery and final Project Lead acceptance are separate from the completed user test; subsequent Hub operations belong to Song Haoran.

Date: 2026-10-22 (Asia/Singapore). Original task AH-20261022-mcp-server-dev;
Candidate CAND-ANT-011; owner Vannes Wijaya. Local test release only.

The user supplied an original screenshot of a blank card with a question-mark avatar after importing 1.0.0. Root cause: native list/detail helpers consume display_name/display_description, while the frontend reads their zh/en properties directly. The previous manifest only declared name/description. Version 1.0.1 adds nonempty bilingual display fields and aligns version declarations; the three Skills and generator behavior are otherwise unchanged.

Validation: 24 repository unit tests passed, including a new native-display contract regression. Read-only native host list/detail helper execution plus the host frontend localization function reproduce empty title/description for 1.0.0 and produce mcp-server-dev, nonempty bilingual descriptions, and initial M for 1.0.1. These host sources are selected in memory from a local checkout, never copied into the plugin. All three Skills remain present in the detail response.

The final local ZIP was extracted and used for the real App protocol/UI resource tests and official MCPB validate/pack/unpack/relocation tests; all passed. Both package variants contain the same 17 runtime files. Repository evidence is retained in PATCH_FUNCTIONAL_TEST.log and HOST_CARD_TEST.json beside this report. Final ZIP hashes are recorded in releases/agent-plugin/mcp-server-dev/1.0.1/artifact.json; the user handoff also includes test-package.json in the workspace outputs directory. No user acceptance, actual running-host installation/visual UI success, PR merge or Hub submission is claimed for 1.0.1. The historical 1.0.0 report follows unchanged.

---

# 功能测试：mcp-server-dev 1.0.0

测试日期：2026-10-22（Asia/Singapore）。任务 AH-20261022-mcp-server-dev；候选 CAND-ANT-011。
本报告的通过仅表示开发功能与仓库包装检查，不是 Hub 已提交/已发布、宿主安装通过或总控验收。

## 环境及可重复命令

macOS Darwin 25.6.0 / arm64；Python 3.12.14；Node v24.19.0；npm 10.9.4。
仓库依赖 PyYAML 6.0.3。测试工具锁定 SDK 1.32.1、ext-apps 1.7.5、zod 4.6.7、esbuild 0.28.1、MCPB CLI 2.1.2。
所有 npm 安装使用锁文件和 integrity；测试目录为独立临时目录。无 API Key、业务数据、云端部署或付费调用。

```bash
python -m pip install -r requirements-dev.txt
PYTHONDONTWRITEBYTECODE=1 python -m unittest discover -s tests -v
python tests/run_mcp_server_dev_integration.py
python tools/asset_release.py check plugins/mcp-server-dev
python tools/asset_release.py pack plugins/mcp-server-dev
python tools/asset_release.py check-repo
```

Node/npm 在本机通过 MCP_DEV_NODE 和 MCP_DEV_NPM_CLI 明确指定；在普通 PATH 环境无需设置。
integration 的 --payload 可改为最终 ZIP 解出的 mcp-server-dev/mcp-server-dev/，验证实际分发字节。
原始执行输出经可移植路径替换保存于 FUNCTIONAL_TEST.log，不代替真实截图。

## 实际结果

- unittest：20/20 通过，其中既有包装器 15 项、插件生成器 5 项（包括 8 组路由组合）。检查已有目录不被覆盖、符号链接拒绝、slug 注入/越界、quoted author 的 JSON 保真、非法/超大 spec 以错误码 2 退出。
- App：从生成器创建独立工程，npm ci，Node 逐文件 --check，实际 esbuild 构建。官方 SDK 客户端连接真实 stdio 服务器，initialize 取得工程版本 0.1.0，tools/list 得 add 工具及只读注解，tools/call(2,3) 得 5。
- App 资源：实际 resources/list/read；验证 ui://add/result.html、text/html;profile=mcp-app、完整本地 HTML、aria-live 和 textContent；没有远程 module import。
- 失败与恢复：超界数字、字符串参数、未知工具均被拒绝；随后正常调用 -2+7 仍得 5。客户端正常关闭子进程。
- MCPB：独立生成/安装生产依赖。官方 CLI validate 正确 manifest 成功，缺少必要字段的 manifest 被拒绝。pack 生成真实 .mcpb，检查路径安全、源码/清单/上游许可及 SDK/zod 实际 LICENSE；无测试 CLI 混入。
- MCPB 解包：官方 CLI unpack 到新目录，从不同 cwd 通过真实 SDK 客户端重新 initialize/list/call；2+3=5，错误与恢复再次通过。最终测试示例包文件数 2467；它是测试工程产物，不混入插件 ZIP。
- 依赖许可采集：App 与 MCPB 均生成实际安装包 LICENSE/NOTICE 清单；App 额外断言 ext-apps 的完整迁移许可文本被保留，避免误信 npm MIT 字段。
- 静态/格式：11 个 JSON/Python/Node 源码或结构文件解析及 Node --check 全通过；Markdown 本地链接存在；固定模板锁文件无本机绝对路径/越界键。
- 真实功能不是包装器测试的替代名称；以上过程实际安装依赖、启动服务器、发协议请求、构建 UI、生成并解包 MCPB。

## 已修复的失败与复测

初始机器缺 PyYAML，安装仓库固定开发依赖后复测通过。
第一次 npm 12 + /tmp 前缀生成的 lock 含错误相对路径，npm ci 拒绝；使用 npm 10.9.4 在各项目工作目录重建干净锁文件，完整 clean install 集成复测通过。
许可采集正则曾漏掉 LICENSE.md，已修正并在最终集成复测；只把真实最终结果标为通过。
PR 首轮 CI（run 39711915654）发现测试导入在载荷中生成 __pycache__，导致 check-repo 正确拒绝；已让测试加载器禁止对载荷写字节码，不放宽包装规则。不设置 PYTHONDONTWRITEBYTECODE 的完整 unittest + check-repo 本地复测通过。

## 发行验证与限制

发行 ZIP 需与源码载荷逐文件哈希一致、Apache 许可哈希一致、六处修改声明存在、仅含市场外壳和唯一运行载荷。
最终 ZIP 已解包并完成同一 integration 驱动的完整生成/构建/协议/MCPB 往返测试，全部通过；17 个载荷文件与 artifact.json 每项哈希一致，Apache 许可哈希及六处修改声明均已核对；执行记录见 RELEASE_TEST.log。

未验证：真实 MCP Apps 宿主 UI 渲染/主题行为、目标桌面 MCPB 安装、远程 HTTP/OAuth、生产业务后端、无开发工具机器安装、Windows/Linux 运行、Agentic Hub 接受上传。
示例 MCPB 明确需要 Node >=20；本地协议/打包通过不自动承诺以上环境兼容。
当前仍缺用户提供的真实测试截图、最终 Hub 提交截图、真实 Hub 状态及 Song Haoran 明确验收；不能自行设置已完成或已交付。
