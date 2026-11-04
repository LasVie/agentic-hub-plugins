# 网页会话记录器

记录用户在浏览器中的真实操作，导出中文 Markdown 时间线 `report.md` 和结构化事件日志 `events.jsonl`，辅助梳理网页流程与接口调用。记录在独立本地后台进程中运行，宿主将各次工具调用放到不同进程时，也能继续查询和停止同一会话。

## 工具与使用步骤

1. `web_record_start`：启动 Chrome、Edge 或 Chromium，或通过 `attach_url` 接入用户已授权的调试端点。返回 `session_id` 后，请用户在该浏览器中操作。
2. 等待用户完成；用 `web_record_status` 和同一 `session_id` 查询当前计数。
3. `web_record_stop`：使用同一 `session_id` 停止记录，读取返回的 `report_md` 与 `events_jsonl` 路径并按实际事件总结。会话停止后默认关闭本工具启动的浏览器；`keep_browser_open: true` 可保留浏览器。

本插件只观察操作，不会代替用户浏览，不会自动生成或执行网页重放脚本。

### 开始记录的参数

| 参数 | 说明 |
| --- | --- |
| `url` | 可选，开始记录时打开的网址。 |
| `attach_url` | 可选，接入已用 `--remote-debugging-port` 启动的授权浏览器，例如 `http://127.0.0.1:9222`。 |
| `headless` | 默认 `false`；无头模式主要用于自动化测试。 |
| `port` | 默认 `9222`；新建浏览器的远程调试端口，`0` 可由浏览器分配空闲端口。 |
| `browser_path` | 可选，浏览器可执行文件路径。 |
| `output_dir` | 可选，输出目录，默认 `./dsh-web-recorder-sessions/<session_id>`。 |

## 记录内容

点击、`input` / `change` / `submit` 事件、同文档导航（`popstate` / `hashchange`）、整页导航，以及网络请求和响应的元数据：方法、网址、资源类型、状态码、MIME 类型。Markdown 报告使用中文标题和事件说明；JSON 键、CDP 方法与事件类别代码保持原值。

## 依赖与限制

宿主需提供 OpenJiuwen、`aiohttp`，并预先安装 Chrome、Edge 或 Chromium。可自动查找浏览器，也可指定 `browser_path` 或 `DSH_WEB_RECORDER_BROWSER`；不会自动下载浏览器。不需要 Node、Playwright 安装或 MCP 服务。不支持 Firefox 和 WebKit。

使用 `url` 打开的页面会在导航前完成监测初始化。接入已有浏览器时，接入前已完成的请求无法恢复；断开调试连接、浏览器退出或页面机制也可能影响记录。仅报告实际捕获的事件，不保证任意网站的所有交互都可捕获。

## 隐私

输入值只记录长度，不记录其正文；网络请求与响应正文也不记录。但元素文本、网址和查询参数仍可能包含敏感信息。仅记录用户授权的会话，在分享或上传前检查两份输出。调试端点仅用于已授权浏览器。

## 原生设计

这是直接使用 Chrome DevTools Protocol 的独立原生实现。上游公开功能说明仅用于理解需求，未复制 DSH/Cordis 代码、提示或素材。本次 1.0.3 将界面、Skill、工具说明、诊断和报告改为中文，保留机器接口、捕获逻辑和原有隐私边界。
