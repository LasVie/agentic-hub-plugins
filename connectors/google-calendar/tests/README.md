# Node 测试

运行载荷不需要 Python。以下命令使用开发机 Node 22+ 和临时测试目录；正式宿主验证记录见 TEST_REPORT.md。

先对当前载荷执行 `calendar-cli.cjs prepare`，并将 JIUWENSWARM_DATA_DIR 指向一个源码仓库之外的临时目录。依赖准备完后，将 CALENDAR_REVIEW_AUTH_LIBRARY 指向该测试目录下的 `connector-data/google-calendar/node-v1/runtime/node_modules/google-auth-library`，运行 `node --test tests/test_calendar_node.cjs`。

7 项测试覆盖：主日历参数和分页、个人日程白名单、日期/时区、按 ID 读取与路径拒绝、真实官方认证库生成的单一 OAuth scope 和 PKCE/state、有限子进程超时及错误脱敏、写入结果不明时的先回读提示。这些测试不创建真实日程，也不替代 stock WorkSwarm 的实际卡片授权和聊天验收。

真实授权与写入只用用户批准的专用账号/数据。不得把 Desktop OAuth JSON、refresh/access token、临时回调 code 或密钥写进测试数据、日志、截图或 ZIP。故意无效凭据、受控回调/代理的检查不能写成自然过期、真实 Google 拒绝或真实服务故障；本轮实际 Google Cancel 的证据单独标明。
