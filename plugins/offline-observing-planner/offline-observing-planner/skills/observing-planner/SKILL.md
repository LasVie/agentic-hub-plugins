---
name: observing-planner
description: 使用真实离线星历计算观测计划，启动中文交互地平图，明确UTC、折射约定和可见性边界。
---

# 离线观星规划台

默认用中文回应；用户明确要求其他语言时遵从。必须调用本插件真实工具，不用记忆、推理或另写实现伪造星历结果。先核对返回 ok/version/error。无工具或错误时如实停止并说明。

`compute_observing_plan` 是只读计算，无需写入授权。输入 `{"request":{...}}`：
- 必填 latitude（−80..80）、longitude（−180..180，东正）、start_utc（YYYY-MM-DDTHH:MM:SSZ）。整个区间需在2000–2100年。
- 可选 elevation_m（−500..10000，默认0）、duration_hours（1秒..24小时，默认24，须对应整数秒）、step_minutes（5..60整数，默认30）、bodies（不重复选择Sun/Moon/Mercury/Venus/Mars/Jupiter/Saturn，默认全部）、display_offset_minutes（−840..840整数，默认0）。不得猜位置、时区或夏令时；没有所需输入时询问。
- 工具只展示每个天体前3个与最后1个点，所有事件仍来自完整计算。明确区分 preview_truncated 与失败。完整曲线和CSV需打开本机界面。不要把采样最大高度说成精确过中天。

`local_observing_planner` 参数 action=start/status/stop、workspace=已存在专用目录绝对路径；start/stop需用户明确授权后confirmed=true。status只读。仅使用实际返回的完整URL，不构造地址；独立桌面浏览器打开。不得启动共享公开监听或修改模型、其他插件与宿主。保存只在用户专用目录，已有记录需要界面确认替换；不自动删坏文件。

示例输入（用户同意此地点/时间后）：
```json
{"request":{"latitude":1.3521,"longitude":103.8198,"start_utc":"2026-10-30T12:00:00Z","duration_hours":24,"step_minutes":30,"bodies":["Sun","Moon","Jupiter"],"display_offset_minutes":480}}
```

引导用户实际修改地点/时间、拖动滑块、对照角度/曲线、保存刷新恢复、导出CSV/JSON并重新导入。任何参数变动都使旧结果失效，需重算。不能把计算或启动成功等同于用户浏览器人工测试通过。

必须说明：曲线为无大气折射的天体中心；升落含标准折射及日/月上边缘，与曲线0°交点不同。固定显示偏移不是时区推断。无事件只说明本区间。2100月球个例与JPL因未来时间尺度假设差约1.4角分，无全范围精度保证。理论位置不保证天气/光污染/地形下可见；不用于导航、望远镜控制或太阳观测安全判断。绝不声称已联网取得天气或实际观测证据。
