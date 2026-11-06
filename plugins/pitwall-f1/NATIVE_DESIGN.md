# 独立实现规格：OpenF1 工具

适用范围：`tools/pitwall_tools.py` 中 OpenF1 部分（`f1_list_sessions`、`f1_session_results`、`f1_drivers`、`f1_laps`、`f1_pit_stops`、`f1_tyre_stints`、`f1_weather`、`f1_race_control`），以及校验、限流、缓存、错误处理和中文输出。这部分不含上游 Pitwall F1 代码。

## 需求来源

- 用户（Nguyen Trung Dung）2026-11-06 在会话中选择方案：不要求 F1 TV 登录，移植 6 个只依赖 Jolpica 的上游工具，并另写 OpenF1 原生工具补充 2023 年起的场次数据。
- 上游 Pitwall F1 因其官方计时流（livetiming.formula1.com）现在返回 401/403 而无法在无账号条件下提供场次数据；上游不使用 OpenF1。
- 功能需求来自 OpenF1 公开文档与官网说明（https://openf1.org/ ，免费额度：2023 年起历史数据、无需认证、每秒 3 次/每分钟 30 次、标注个人使用）以及对其端点（sessions、session_result、drivers、laps、pit、stints、weather、race_control）的实际匿名请求观察。工具的输入输出由这些公开接口字段和用户需求决定，没有复用任何授权不明的实现。

## 材料接触记录

开发中接触过上游 Pitwall F1 源码，但仅限其 Jolpica 工具和赛站别名表（已按 MIT 以 ported 方式记录）；上游没有 OpenF1 实现，因此不存在可被改写的同功能代码。OpenF1 部分没有查看或参考任何第三方 OpenF1 客户端实现。

## 组件边界与设计

- 场次选择：`session_key`，或 `year`（≥2023）+ `race` + 可选 `session_type`（默认正赛）。`race` 用中英文关键词匹配 OpenF1 的 country_name/location/circuit_short_name；匹配多个场次时返回 AMBIGUOUS_SESSION 与候选，不自动挑选。
- 车手选择：编号、三字母缩写或姓氏，在该场次车手表中匹配；无匹配或多匹配分别报错。
- 输出：`ok/tool/source/retrieved_at_utc/arguments/message/summary_zh/data/warnings_zh`；字段缺失保持为空；天气汇总最小/最大/平均；圈速平均仅排除出站圈并明示口径。
- 限流：进程内每分钟 28 次、间隔 0.4 秒，低于 OpenF1 免费额度；达到上限直接返回 RATE_LIMITED，不等待、不重试。同一 URL 5 分钟内缓存（最多 128 条）。
- 安全：只读 GET；不使用账号、令牌或环境变量；不读写本地文件；来源文本（如赛事控制信息）标注为数据，不是指令。

## 测试

`tests/test_adapter.py`（离线，33 项）覆盖参数拒绝先于网络、URL 构造、歧义、HTTP 状态映射、限流、缓存、输出整形与缺失值；`tests/live_checks.py` 对真实服务运行；`tests/host_checks.py` 用真实 openjiuwen DeepAgent/Runner 加载并调用。
