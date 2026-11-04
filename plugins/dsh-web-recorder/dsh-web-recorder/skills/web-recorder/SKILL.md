---
name: web-recorder
description: 记录用户操作的浏览器会话，捕获点击、输入长度、导航和网络元数据，导出中文 Markdown 时间线与 events.jsonl，用于梳理网页流程和接口调用。
---

# 网页会话记录器

默认使用简体中文说明步骤与结果；保留工具名、参数名、路径、会话 ID 和协议标识原值。记录用户实际进行的操作并形成证据，不替用户操作浏览器，也不自动生成或执行重放脚本。

## 工具

- `web_record_start`：启动新的 Chrome、Edge 或 Chromium；或用 `attach_url` 接入已启动且获用户授权的 DevTools 端点。返回 `session_id`。`url` 指定开始时打开的页面；`headless: true` 主要用于自动化测试；`output_dir` 指定结果目录。
- `web_record_status`：查询同一 `session_id` 的状态与当前计数，或列出活动会话。
- `web_record_stop`：停止指定会话，写出时间线 `report.md` 与逐行 JSON 日志 `events.jsonl`，返回实际计数和文件路径。

## 工作流程

1. 确认用户希望记录的浏览器与范围，仅接入用户已授权的调试端点。调用 `web_record_start`；最好先开始记录，再让用户浏览。
2. 明确告诉用户在打开的浏览器中完成希望记录的操作。保留本次 `session_id`，停下来等待用户完成；不能在同一轮自行假定操作已经结束。
3. 用户明确完成或要求停止后，用同一 `session_id` 调用 `web_record_stop`。根据返回路径读取实际报告，概述时间线与网络或接口元数据。
4. 若开始、状态或停止失败，报告真实错误。某类事件未出现时应明确说明未捕获，不能补写或推测成已发生事件。

## 捕获范围与隐私

记录点击、`input` / `change` / `submit`、同文档与整页导航、网络请求及响应的元数据。输入只保存长度，不保存正文；网络正文不被捕获。元素文本、网址和查询参数仍可能包含敏感信息，分享前检查 `report.md` 和 `events.jsonl`。接入前已经完成的网络请求无法恢复。

## 运行条件

宿主需提供 OpenJiuwen 和 `aiohttp`，并安装 Chrome、Edge 或 Chromium；可自动查找，或设置 `browser_path` / `DSH_WEB_RECORDER_BROWSER`。本插件不会下载浏览器，不需要 Node、Playwright 或 MCP 服务，不支持 Firefox 或 WebKit。不要将环境缺少依赖写成已成功开始记录。
