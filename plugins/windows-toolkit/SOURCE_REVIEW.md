# 来源与查重审查

## 任务与差异

- 任务 ID：AH-20261023-dsh-win-toolkit
- 候选 ID：CAND-DSH-019
- 关联历史/新增资产 ID：无（候选查重结论为 Confirmed New Capability）
- 名称映射：上游 `dsh-win-toolkit` → 中文展示名 `Windows 本机工具箱` → 内部 slug `windows-toolkit`
- 功能差异与复用/独立实现结论：候选已在 Plugin Candidates 与以下资产逐项比较后判为独立新能力：

| 关联资产 | Asset ID | 差异 |
| --- | --- | --- |
| chrome-devtools-mcp | 2f99a9222dce41f4bd5ac440bf4496f4 | 浏览器自动化；不暴露剪贴板、通知、hosts 或 DNS/TCP 诊断 |
| page-acceptance | 747494162b0c4725ae6ca95b9803b501 | 页面验收流程；不涉及本机 OS 工具 |
| mcp-manager | 4862208069dc4ed9b1838f6ddfabbcc4 | MCP 生命周期管理；不提供上述本机能力 |

## 材料与授权证据

上游 `dsh-win-toolkit` 以 MIT 许可发布，本次复用其工具语义与 PowerShell 脚本逻辑。许可全文随包保留并逐字节核对。

| 实际使用路径/材料 | 上游 URL 与固定提交/版本 | 适用许可与覆盖范围 | 许可文件及 SHA-256 | 复制/修改情况 |
| --- | --- | --- | --- | --- |
| `tools/windows_toolkit.py` | https://github.com/Edge-Echo/dsh-win-toolkit ；npm `dsh-win-toolkit@0.1.3`，gitHead `665bc6947c52e5f66e73233eff4950d11525430c` | MIT，覆盖仓库全部代码 | `licenses/dsh-win-toolkit/LICENSE`，`e7f61d728785dac8cc772f416f5d33fa618b35d141b972cf7d41b21bbfd873a6` | 改写：DSH `defineTool` 注册替换为 WorkSwarm `Tool`/`ToolCard`；保留脚本语义与 Base64 边界；新增中文错误、输入校验、UTF-8 前置 |
| `skills/windows-toolkit/SKILL.md` | 同上（依据上游 `README.md` / `README.zh.md` 的工具语义） | MIT | 同上 | 新写中文 Skill 说明 |
| `README.md` | 同上 | MIT | 同上 | 新写中文 README |
| `licenses/dsh-win-toolkit/LICENSE` | 同上 `LICENSE` | MIT | 同上 | 逐字节复制，未修改 |

未复用：`cordis.patch.yml`、`lib/cli.js`、`lib/env.js`、各 `.d.ts` 等 DSH 宿主专用文件；上游 README 的截图与 banner 素材未纳入。

## 最终 ZIP 许可复核

- 原版权/署名及文件头保留位置：`tools/windows_toolkit.py` 文件头保留上游版权与修改声明；`licenses/dsh-win-toolkit/LICENSE` 保留原始 MIT 全文
- THIRD_PARTY_NOTICES.md 路径与逐上游覆盖情况：`THIRD_PARTY_NOTICES.md`，逐项列出上游、版本、许可、复用与修改范围
- MIT / Apache-2.0 等许可全文路径：`licenses/dsh-win-toolkit/LICENSE`
- 上游 NOTICE：无（上游仓库未提供 NOTICE 文件）
- Apache-2.0 修改文件上的显著声明位置：不适用（上游为 MIT）
- 品牌素材、数据、依赖、服务条款等独立限制：无；插件不包含第三方图标、字体或数据集，也不需要外部服务账号
- 解包检查命令、文件清单与哈希核对结果：见 `package-verification.json`、`packaging-repair-verification.json` 与 `TEST_REPORT.md`
- 原生开发时的需求来源、材料接触记录与 NATIVE_DESIGN.md：不适用（本任务为已授权复用，`mode: ported`）
- AI 结论：**verified** — MIT 全文已随包保留，复用范围限定为工具语义与脚本逻辑，未纳入未授权材料
- 待解决事项：无许可阻塞；原 1.0.0 用户测试确认已保留，当前 LF 重建版 1.0.1 的明确完成确认仍待收到。Hub 操作由 Song Haoran 负责。

## LF packaging repair — 2026-10-23

The original 1.0.0 ZIP payload used CRLF while Git stored LF, causing the real
PR42 package-contract failure. Version 1.0.1 packages an LF checkout. Source,
native importer ZIP and canonical ZIP contain the same six payload files.
Only line endings and the manifest version changed; no runtime semantics or
locale text changed. The license remains byte-identical to the pinned upstream
copy with the SHA-256 above. Required notices and attribution remain bundled.

Current native SHA-256: `18c6b8d439992404bb308ac37084405a92869d38523c64d473dbf42d499421d4`.
Current canonical SHA-256: `844450ba04d52481dbdb762eb515ddca4fcea179a1191f82d33f8a0a90b874a4`.
The original packages and reports remain historical evidence. No new-version
user completion, frontend test, merge, Hub action or Project Lead acceptance is
claimed. See `LF_REBUILD_REPORT.md` for the diagnosed bug and actual checks.
