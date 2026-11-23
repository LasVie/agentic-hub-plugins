# 第三方来源与许可

运行时使用未修改的 Google 官方 `google-auth-library` 11.3.4（googleapis/google-cloud-node，core/packages/google-auth-library-nodejs），Apache-2.0；OAuth2Client 源文件原版权声明为 Copyright 2019 Google LLC。完整 Apache-2.0 文本随包位于 `licenses/google-auth-library/LICENSE`。不修改或复制上游认证实现，不删除下载发行版中的原始文件头、许可证或声明。当前核对的发行材料未另附上游 NOTICE。

精确 npm 版本、tarball URL、integrity 和传递依赖许可在 `scripts/package-lock.json`（实际路径 skills/gmail-readonly-guide/scripts/package-lock.json）记录。首次 npm ci 禁用安装脚本，下载的依赖保留各自原始许可。node_modules 和第三方二进制不放入本包。

连接器代码、中文技能及文档由团队实现，复用本仓库 Calendar 1.1.0 的 Node 准备/存储/OAuth 框架；不包含第三方 Gmail MCP 插件代码或提示词，不沿用旧 Python 运行依赖，也未复制 Google 文档示例实现。本声明不改变仓库团队代码的许可。

Gmail、Google 和相关服务名称属于各自权利人。本包未包含新的 Google 品牌图片，不表示官方背书。开源许可不授予 API 账号权限、Google 服务访问资格或一般商标许可。

来源：https://registry.npmjs.org/google-auth-library/11.3.4
https://github.com/googleapis/google-cloud-node/tree/main/core/packages/google-auth-library-nodejs
https://developers.google.com/identity/protocols/oauth2/native-app
https://developers.google.com/workspace/gmail/api/guides/sending
