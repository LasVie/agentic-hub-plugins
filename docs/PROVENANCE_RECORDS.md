# 来源记录格式

这是事实审查记录的技术格式，随包许可与署名要求见 [AGENTS.md 的许可与分发要求](../AGENTS.md#许可与分发要求)。本仓自身的统一许可证仍未选定。AI 必须核查实际材料，不能仅填一个状态让校验器放行。

每个资产父目录包含 `SOURCE_REVIEW.md`、`provenance.json`、`TEST_REPORT.md`。来源审查写明上游 URL、固定版本、许可原文/作用范围、逐文件复用情况、关联已有资产、不同点和待确认事项。功能测试报告记录实际命令、环境、代表性成功/失败案例与输出，禁止把包装器的单元测试当成插件功能测试。

原生实现使用模板中的 mode=native、permission_status=original、reused_paths=[]，并完成 NATIVE_DESIGN.md。sources 可以记录公开功能说明，但不能把复制来的实现说成原创。如果交付载荷混合原创与实际搬入的第三方材料，整体使用 mode=ported 并逐项记录复用；仅通过依赖声明在外部安装的组件也需核查许可和服务约束，但不能把未打包的文件冒充随包证据。

实际复用时按事实填写，例如下列结构中的路径和哈希都必须替换为真实证据：

```json
{
  "mode": "ported",
  "permission_status": "verified",
  "sources": [{
    "url": "https://github.com/owner/upstream",
    "revision": "固定完整提交或版本",
    "license_expression": "实际核对的许可表达式",
    "license_evidence": [{"path": "licenses/upstream-LICENSE.txt", "sha256": "该文件真实的SHA-256"}]
  }],
  "reused_paths": ["references/reused-material.md"],
  "audit_file": "SOURCE_REVIEW.md"
}
```

证据路径相对内层载荷。许可是否覆盖这些材料、是否允许预期用途和发行方式仍需 AI 对原文逐项核对。检测不到、范围冲突或存在疑问时填 unknown 并报告；不能伪造 verified。

`ported` 资产的内层载荷按本仓约定包含：

```text
<slug>/
├── SKILL.md 或 manifest.json
├── THIRD_PARTY_NOTICES.md
└── licenses/<upstream>/
    ├── LICENSE             # 实际上游许可全文及版权声明
    └── NOTICE              # 上游有适用 NOTICE 时保留
```

`THIRD_PARTY_NOTICES.md` 逐上游记录固定来源、原作者/权利人原有声明、适用路径、许可和修改摘要；不得编造权利人。目录和汇总文件名是本仓约定。MIT 保留版权及完整许可文本；Apache-2.0 还须核对适用声明、上游 NOTICE，以及修改文件上的显著修改声明。集中摘要不替代这些原有声明。原生资产仅对实际复用的第三方依赖/素材提供相应许可材料，不凭空生成上游。

发行前在 `SOURCE_REVIEW.md` 逐项记录最终 ZIP 内的许可、署名、NOTICE 与修改声明路径及复核结果。当前工具校验的是来源字段、证据哈希和包结构，不会自动判定全部许可义务已经履行；AI 必须内容审查，不能把 CI 通过等同于法律放行。

artifact.json 固定记录 ZIP 哈希、载荷每文件哈希、来源审查哈希和功能测试报告哈希。ZIP 合入后若补 Hub ID/提交状态/截图，可在对应版本目录新增 delivery.json 并提交后续维护 PR；不要因此悄悄重写已交付 ZIP。
