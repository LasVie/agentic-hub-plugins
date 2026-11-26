# Asana1.1.0 source and permission review

Reviewed2026-11-19 before implementation; see NATIVE_DESIGN.md. Owner Song Haoran; task AH-20261117-asana-connector; stable ID repo:agent-mcp:asana. Name mapping: Asana → Asana 任务连接器 → asana. Original 1.0.0 records and ZIP bytes remain unchanged in the original maintenance workspace; this PR delivers only exact 1.1.0 and the relevant prior 1.1.0 review snapshots.

This is an independently authored standard stdio MCP adapter to the Asana REST API, not Asana's official hosted MCP. It preserves the original PAT-based project/task functionality and avoids requiring a new MCP OAuth app. Fixed service origin app.asana.com/api/1.0. Four bounded tools for status/list/read/create; no generic request, update/delete, project creation, assignee or attachment operation. Node built-in readline/fetch/URL/AbortController only. No runtime npm packages, Python, pip, vendor implementation, copied prompts, artwork, fonts or business data are distributed. The host provides Node22; no Node binary is redistributed. Source entry is in tests/standard-mcp.cjs and embedded literally in mcp.json by tests/build_standard.py before test exports; no installed-file path or dynamic-code evaluator required.

Official sources inspected live2026-11-19: https://developers.asana.com/reference/gettasksforproject ; https://developers.asana.com/reference/createtask ; task detail via https://developers.asana.com/reference/gettask . Only API contracts are used; no documentation prose or vendor code copied. These API references do not grant rights to logos or service accounts. None are assumed. The original provenance file retains the no-copied-paths record; no unreviewed upstream material added. Native Implementation Only remains the candidate's license conclusion. No new relicensing decision.

ASANA_PERSONAL_TOKEN retains its original host credential-schema key. Tokens are injected by normal WorkSwarm credential provisioning and used only for HTTPS requests to Asana. No credential-file reader/copying, secret logging, redirects or automatic mutation retries. Client errors are Chinese, response and request sizes bounded. API identifiers and user-authored content remain unchanged. The existing preview-only Asana logo is not bundled.

Actual stock-host compatibility, packaging, current Chinese read/create/readback, failure behavior, user testing and originals must be verified separately. Source review alone does not establish a functional pass or Hub acceptance. Keep this local until exact-package user completion and original evidence; no old1.0.0 approval reused for1.1.0.

## 2026-11-23 补充复核

当前精确 1.1.0 原生包与 Hub 包保持原字节；正常卡片安装、用户从宿主安全表单输入 PAT、实际中文查询／新建一次测试任务／独立回读，以及业务后断开与进程清理已完成。未改动业务代码、权限、品牌材料、WorkSwarm 源码或认证实现。官方 PAT 文档 https://developers.asana.com/docs/personal-access-token 于本轮复核；令牌作为不透明凭据使用，不按格式推断有效性。原任务、候选、名称与范围保持不变。当前结果和未测边界见中文 TEST_REPORT.md；Song Haoran 已于 2026-11-23 在当前对话明确确认完整 1.1.0 测试通过并要求附实测原图提交 PR。载荷及冻结 ZIP 保持不变。
