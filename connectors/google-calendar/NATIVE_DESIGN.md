# Google 日历连接器 1.1.0 设计

历史 1.0.0 设计保留在 history/1.0.0。独立 Node 进程负责卡片 init/status/auth/unAuth。OAuth 使用官方 Node 认证库，PKCE S256、随机 state 和本机随机端口/随机路径，固定 Google 端点及原 calendar.events.owned；会话只写本机 600 文件，断开改变授权尝试编号以防迟到回调恢复会话。业务由锁定 gws 0.22.5 执行固定 list/get/insert，只接收由官方 Node 认证库刷新的短期 access token 环境变量，屏蔽原始错误。有限子进程/超时/退出清理避免宿主 MCP 缓存残留。

中文技能用 JSON 文件传参数，包装器按操作白名单校验。主日历查询可分页；新建仅单次个人、私密、空闲、无提醒、无通知，预生成随机 ID，结果未知时先按 ID 回读。卡片状态实际查询主日历，不仅检查本地文件。Desktop 回调只支持浏览器与宿主同机；远程服务端不是本版已验证范围。
