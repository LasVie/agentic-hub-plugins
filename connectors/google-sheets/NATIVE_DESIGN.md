# Google 表格连接器

新建表格、列出工作表、读取或更新指定区域、在逻辑表末尾追加行。

用户选择卡片并使用自己 Google Cloud 项目的 Desktop OAuth 客户端。只申请 `spreadsheets`。在浏览器通过 PKCE 和本机回调完成授权，返回所选文件标识、链接、数据或写入结果。

读取和写入须明确工作表名称和 A1 范围。默认用原始值写入；有公式的格子会拦截普通更新。用户明确要求写入或替换公式时分别使用 --formulas 或 --replace-formulas。追加范围用来定位逻辑表，实际写入范围以响应为准。Sheets 没有可用于此写入的修订锁，写入前核对范围，写入后回读。

[Google REST 规范](https://developers.google.com/workspace/sheets/api/reference/rest)
