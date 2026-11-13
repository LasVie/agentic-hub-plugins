# Google 文档连接器

读取指定标签页、新建文档、追加或替换指定标签页的正文。

用户选择卡片并使用自己 Google Cloud 项目的 Desktop OAuth 客户端。只申请 `documents`。在浏览器通过 PKCE 和本机回调完成授权，返回所选文件标识、链接、数据或写入结果。

读取会列出所有标签页，默认读取第一个标签页。修改前核对标签页和版本。替换只处理指定标签页正文中唯一匹配的一处文字，支持中文及表情。替换后的样式由 Google Docs 决定。

[Google REST 规范](https://developers.google.com/workspace/docs/api/reference/rest)
