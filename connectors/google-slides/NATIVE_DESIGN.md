# Google 幻灯片连接器

读取、创建和修改原生 Google 幻灯片。

用户选择卡片并使用自己 Google Cloud 项目的 Desktop OAuth 客户端。只申请 `presentations`。在浏览器通过 PKCE 和本机回调完成授权，返回所选文件标识、链接、数据或写入结果。

先读取演示文稿，取得页面 ID 和版本。替换仅应用到指定页内所有完全匹配的文字。修改后回读该页。当前编辑范围是标题、正文和文字替换，图表、图片与母版可在 Google Slides 中编辑。

[Google REST 规范](https://developers.google.com/workspace/slides/api/reference/rest)
