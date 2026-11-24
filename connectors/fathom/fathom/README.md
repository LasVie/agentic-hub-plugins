# Fathom 会议连接器

在 WorkSwarm 聊天中查询账号可访问的 Fathom 录制会议，并读取指定会议的现有摘要和逐字稿。

1. 登录 Fathom，打开用户设置中的 **API Access** 并生成个人 API Key。
2. 在 WorkSwarm 安装连接器，点击卡片的「连接」，在密钥字段填写后保存。授权范围由 Fathom 账号的会议访问权限决定。
3. 在聊天中说「查询标题含项目复盘的 Fathom 会议，给出匹配会议的摘要和逐字稿前 25 条」。

标题匹配针对 Fathom 返回的当前页，可使用下一页游标继续。日期按 Fathom 的会议创建时间过滤。摘要保留原文并省略 Fathom 录制分享链接。逐字稿按条分页，并保留原文、说话者和时间戳。摘要或逐字稿尚未生成时，可等待 Fathom 处理后重试。

需要 WorkSwarm 自带 Node.js 22 和到 `api.fathom.ai` 的 HTTPS 网络。卡片连接使用 Fathom 个人 API Key。Fathom 官方说明免费计划也提供 API。生成测试内容需要先让 Fathom 完成一场录制。遇到未授权时，在卡片中重新填写当前账号的有效密钥。请勿把密钥发到聊天。
