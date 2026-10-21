# 来源记录格式

这是事实审查记录的技术格式，不包含尚待总控讨论的许可证法律意见或项目统一许可决定。AI 必须核查实际材料，不能仅填一个状态让校验器放行。

每个资产父目录包含 `SOURCE_REVIEW.md`、`provenance.json`、`TEST_REPORT.md`。来源审查写明上游 URL、固定版本、许可原文/作用范围、逐文件复用情况、关联已有资产、不同点和待确认事项。功能测试报告记录实际命令、环境、代表性成功/失败案例与输出，禁止把包装器的单元测试当成插件功能测试。

原生实现使用模板中的 mode=native、permission_status=original、reused_paths=[]，并完成 NATIVE_DESIGN.md。sources 可以记录公开功能说明，但不能把复制来的实现说成原创。

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

证据路径相对内层载荷。许可是否覆盖这些材料、是否允许预期用途和发行方式仍需 AI 对原文逐项核对。检测不到、范围冲突或存在疑问时填 unknown 并报告；不能伪造 verified。许可文本与来源说明随包如何保留，应按实际适用条款及总控后续决定处理。

artifact.json 固定记录 ZIP 哈希、载荷每文件哈希、来源审查哈希和功能测试报告哈希。ZIP 合入后若补 Hub ID/提交状态/截图，可在对应版本目录新增 delivery.json 并提交后续维护 PR；不要因此悄悄重写已交付 ZIP。
