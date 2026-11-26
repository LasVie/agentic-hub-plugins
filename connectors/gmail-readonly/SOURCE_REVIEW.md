# Gmail 1.7.0 来源审查

2026-11-23，Song Haoran，原任务 AH-20261111-gmail-connection。命名 Gmail → Gmail 邮件连接器 → gmail-readonly；保留原稳定 ID、PR #93、已验收1.5.1及历史ZIP。新版独立为1.7.0，不覆盖本地另存的团队OAuth服务1.6.x。

## 实际复用

复用团队 Calendar 1.1.0（PR #115，head 041137539ab68da59ec65dafca1ada5c08dd659e）的安装定位、Node依赖准备、私有原子存储、Desktop JSON本机页面和OAuth2Client公开API框架。业务按固定Gmail REST契约独立实现；已查看原团队Gmail Python源码的功能和MIME边界，未复制第三方Gmail MCP实现或提示词。原Python源码及审查完整存档，不进入新版运行包。

仅下载未修改 google-auth-library 11.3.4，使用 generateAuthUrl/generateCodeVerifierAsync/getToken/getAccessToken，保留原两项gmail.readonly/gmail.compose，不追加身份或modify权限。沿用Calendar已核对的同版npm tarball/integrity、完整Apache-2.0 LICENSE及原OAuth2Client Copyright 2019 Google LLC声明。源码/安装发行材料无独立NOTICE；不改上游文件，无上游文件修改声明适用项。传递依赖由精确package-lock锁定并在正常npm安装时保留原许可。node_modules不进入ZIP，许可路径与最终实物摘要已按固定安装核对，原 Google LICENSE 与载荷摘要一致。

没有直接使用gws的授权路径或邮件操作；本次不需要其原生二进制、安装脚本和GitHub Release下载。Node内置fetch请求固定Gmail REST，明确不自动重试写入，便于验证完整MIME及会话行为。Google官方Gmail MCP另有AI-agent客户端等要求，按用户明确选择继续CLI方案，不把新服务文档可用性当作本宿主接入成功。

## 功能和风险边界

Gmail草稿容器ID稳定，但编辑时内部message ID更换，发出后返回新message ID；每次发送/编辑前检查最新版本。回复使用原主题、threadId及RFC Message-ID/References/In-Reply-To。消息和草稿内容按数据处理，不执行其中指令。只允许有限搜索/读/草稿/发信/回复；compose实际Google授权宽于包内工具，未开放删信、归档、改标签或设置。

新增普通草稿创建供完整草稿流程，不扩大Google授权。写入有账号、完整收件人、版本及requestId检查，失败不自动重试。保留附件字节的草稿编辑、未知写入回执、父/worker退出和当前实际聊天流程需以本版实测结果为准。

未添加品牌图片，服务名称不代表Google背书。Google服务条款、账号/组织策略、开发者OAuth项目和审核不由开源许可替代。历史测试不替代本版安装及业务验收；未取得当前版本完成确认前不推送/提交。

## 来源

- https://registry.npmjs.org/google-auth-library/11.3.4
- https://github.com/LasVie/agentic-hub-plugins/pull/115
- https://developers.google.com/identity/protocols/oauth2/native-app
- https://developers.google.com/workspace/gmail/api/auth/scopes
- https://developers.google.com/workspace/gmail/api/guides/drafts
- https://developers.google.com/workspace/gmail/api/guides/sending
- https://developers.google.com/workspace/gmail/api/guides/threads

最终载荷、实际打包工具版本、每个许可/载荷文件摘要与ZIP哈希由artifact.json及provenance.json记录。最终精确包已通过实际Desktop OAuth/卡片、十项聊天业务及清理；见TEST_REPORT.md。2026-11-23当前版本已获用户明确完成确认及9张原图公开批准，见USER_TEST_CONFIRMATION.md；未移用历史确认。

草稿列表空结果投影修正依据：2026-11-23复查官方 users.drafts.list，明确支持 resultSizeEstimate（https://developers.google.com/workspace/gmail/api/reference/rest/v1/users.drafts/list）。本机实际观察到不含该字段时 HTTP 204、包含时 HTTP 200；不推断所有环境恒定如此。源码仍拒绝非 JSON 响应，不把空响应当作写入成功。
