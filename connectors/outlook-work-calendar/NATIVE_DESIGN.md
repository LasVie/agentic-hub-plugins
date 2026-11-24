# Outlook 工作日历连接器设计

通过 WorkSwarm 0.2.8 的 `cli-oauth` 卡片连接。用户提供组织租户的目录 ID 和桌面公共客户端的应用 ID。卡片打开仅绑定本机回环地址的入口，微软授权使用 Authorization Code + PKCE，回调地址为注册的 `http://localhost` 加一次性监听端口。认证和刷新令牌由同一租户发放，业务调用固定到 Microsoft Graph 全球服务。

使用 `Calendars.ReadBasic` 委派权限和 `offline_access` 续期。授权后探测当前用户的主日历。在指定时间范围请求 `/me/calendar/calendarView` 获取单次和重复事件实例，限制返回字段，可按标题匹配当前页。后续页只使用同一 Graph 路由的服务游标。按返回的事件 ID 独立调用 `/me/calendar/events/{id}` 读取相同的基本信息。
