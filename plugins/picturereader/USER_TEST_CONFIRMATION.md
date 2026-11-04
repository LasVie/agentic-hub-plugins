# 当前中文版本 1.0.1：受委托测试与授权范围

- 原负责人：Siu Lok Yin；包内 publisher：WorkSwarm；Task `AH-20261023-picturereader`；Candidate `CAND-DSH-177`。
- 精确原生包 SHA-256：`dce99062ee78e84454345be5ae0bd705660593bdb9836a6e96d2d17945db0066`。
- 精确规范包 SHA-256：`94e4e4f161a2792097f6c2592990a47709e664ae4c765298d7fdcd534071a386`。
- 2026-11-04，根 Agent 在用户已打开的 WorkSwarm 原生界面实际导入、选择并运行当前包的中文 prompt；14:47–14:48 的会话 `web_1a1a55030d9_5f82abe2c5d5` 使用 `gpt-6.1-sol`，完成六次真实原生调用并留存原图，安装四文件、裁剪像素与实际输出已独立核对。环境与边界见 TEST_REPORT.md / GUI_TEST_RECORD_1.0.1.json。

## 实际授权，不伪造用户亲测或新口头通过

本对话中用户明确要求：“你帮我完成测试，用我本地打开的workswarm，测试导入和prompt，如果成功，留存screenshot并pr更新现有内容，但注意负责人的名字不要改，其他的field按需更新，可以使用多agent加速，需要我打开ultra和我说”。总控随后转达用户本轮直接指令“未合并的合并进去，然后全部推送”。这些实际指令覆盖 Agent 测试、原图与当前任务的直接 PR/Hub 工作；消息没有可用永久链接，不补造链接或新确认时刻。

本次记录的是 **AI 在明确委托下完成的当前精确包测试**；`human_performed_testing=false`，没有新造“用户本人已测试1.0.1”或“用户刚口头说通过”。七张 JPEG 与一张长 PNG 是同一流程不同视图，按真实来源逐字节保留。long PNG 的渲染摘要、工具 trace 与实际安装哈希共同关联包身份；已有英文1.0.0的用户确认不得扩大到1.0.1。

原图目录 `test-evidence/20261104-zh-1.0.1/` 及 evidence.json 已齐；永久 PR 原图附件、真实 CI/交付与任何 Hub 结果仍须发生后分别核实，当前未 push 或创建新 PR。本次测试不是 Hub 提交、公开发布或项目总控最终验收声明。

## 历史用户确认（原文保留）

# User Test Confirmation — picturereader 1.0.0

- Confirmation date: 2026-10-23 (Asia/Singapore)
- Task: `AH-20261023-picturereader`
- Candidate: `CAND-DSH-177`
- Exact manifest-at-root WorkSwarm ZIP SHA-256: `4118f7c64584247ca3b3087b53beb3dd74171f9dae2f52bf24c412a92fb268fa`
- Canonical Hub ZIP SHA-256: `38f9be3b3787640541a1d07e08214d3469230c3623b75834ebf1dc4bc0f7400a`
- User statement: `ok picture reader is ok just submit`
- Original evidence: `test-evidence/jiuwenswarm-share-20261023-130342.png`
- Evidence dimensions: 2250 × 24045 RGBA PNG
- Evidence SHA-256: `809f95f22d77295af1445651c17fe810c8f724cc6936a555aa2a6ad4cb5d8631`

The screenshot visibly records the WorkSwarm run of the requested workflow: original `image_scan`, reported measurements and grid interpretation, five `image_sample` coordinates, `image_crop` output, rescan of the crop, and confirmation that the source image remained unchanged.

This confirms user testing of the exact native ZIP identified above. It is not evidence of Agentic Hub submission, publication, or Project Lead acceptance.
