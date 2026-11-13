# Google 云端硬盘连接器

搜索文件和目录、下载普通文件、导出 Google 原生文件。

用户选择卡片并使用自己 Google Cloud 项目的 Desktop OAuth 客户端。只申请 `drive.readonly`。在浏览器通过 PKCE 和本机回调完成授权，返回所选文件标识、链接、数据或写入结果。

名称搜索遵循 Google Drive 的名称匹配规则。使用结果中的链接或标识访问文件。处理下载时由用户明确目标目录与文件，输出路径不能覆盖已有文件。普通文件限 25 MiB，原生文件导出限 10 MiB。目录、快捷方式不可直接下载。用 --drive 明确指定共享云端硬盘。

[Google REST 规范](https://developers.google.com/workspace/drive/api/reference/rest/v3)
