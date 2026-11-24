# Google 联系人连接器 1.0.0 设计

Google Contacts → Google 联系人连接器 → google-contacts。任务 AH-20261124-google-contacts，候选 Not Applicable。

复用团队 Google Calendar 1.1.0 的 WorkSwarm 卡片约定、本机 PKCE 授权、Desktop OAuth 文件校验与私有存储。各连接器的授权目录独立。业务用 Node 内置 fetch 直接调用 People API，只开放搜索和按资源名读取。先发送 Google 要求的空查询预热，再用用户给出的条件搜索；详情读取指定 CONTACT 数据源。连接状态用实际 People API 探测。没有 npm 安装或外置服务依赖。

首版保留 Google 搜索前缀匹配语义。聊天用虚构联系人验证，测试数据由 Google 联系人页面准备。
