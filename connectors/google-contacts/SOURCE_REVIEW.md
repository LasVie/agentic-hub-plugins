# Google 联系人连接器 1.0.0 来源审查

2026-11-24，Song Haoran。任务 AH-20261124-google-contacts，候选 Not Applicable。Google Contacts → Google 联系人连接器 → google-contacts。

团队复用取自 Agentic Hub 仓库 Google Calendar 1.1.0，提交 041137539ab68da59ec65dafca1ada5c08dd659e。使用 CLI 卡片命令定位、Desktop OAuth 本机流程，改用本连接器专有目录，移除其他 Google 连接器配置的自动导入。根据公开 People API 接口独立编写业务代码。没有采用 OpenAI 目录的实现、提示词或图标。Calendar 依赖的 gws 与 google-auth-library 未进入此包；Node 运行时由宿主提供，包没有第三方客户端代码或品牌图片。

- https://developers.google.com/identity/protocols/oauth2/native-app
- https://developers.google.com/people/v1/contacts
- https://developers.google.com/people/api/rest/v1/people/searchContacts
- https://developers.google.com/people/api/rest/v1/people/get
- https://github.com/LasVie/agentic-hub-plugins/pull/115

四个 Google 文档仅作为了解接口行为的依据。People API 使用范围和 OAuth 按 Google 项目及账号授权管理。无用户联系人数据、OAuth 客户端或会话进入部署 ZIP。
