# 离线观星规划台 v1.0.0：人工测试交接

候选 CAND-EXT-005；任务 AH-20261030-offline-observing-planner；负责人 Cai Zhenze。

## 当前包与安装

本机 WorkSwarm：<http://127.0.0.1:6393/>，独立后端端口 29310。已通过支持的扩展接口安装本版本，未修改宿主、SDK、依赖、其他插件或模型配置。

人工测试使用原生伴随包：
`/Users/IDLE_And_R/Downloads/Huawei/agentic-hub-plugins/dist/offline-observing-planner/1.0.0/offline-observing-planner-1.0.0-workswarm.zip`

SHA-256：`6e9d379e35ce0b5a7d8e2d373c5eab3668cbbd091f47895ae340997749fb9b68`

规范交付包（本阶段不上传）：
`/Users/IDLE_And_R/Downloads/Huawei/agentic-hub-plugins/releases/agent-plugin/offline-observing-planner/1.0.0/offline-observing-planner-1.0.0.zip`

SHA-256：`64903378e0b7906a0a9b178ff2046cf66d273c9f54a7e551497a48813a099ef9`

两包的 13 个运行文件逐字节一致；规范包多一层市场外壳。已检查许可、声明路径、UTF-8 和解压后的实际计算。不要把整个规范外壳包当成根级 manifest 原生包导入。

打开「扩展 → 我的扩展」，找到「离线观星规划台」，点击「使用」开启新会话。若需要重新导入，选择「创建 → 上传文件创建」，上传上述 `-workswarm.zip`，确认名称及版本后安装；若出现不同版本或文件冲突，停止并报告，不删除其他插件。

## 发给 WorkSwarm 的测试提示

以下提示由你手动发送；准备过程未调用模型。专用空目录已创建。

```text
请只使用「离线观星规划台」的真实工具，测试 v1.0.0。不要编写替代工具、生成模拟网页或伪造结果，不联网，不修改宿主、模型配置或其他插件。

1. 实际调用 compute_observing_plan，request 为：
{"latitude":1.3521,"longitude":103.8198,"elevation_m":0,"start_utc":"2026-10-30T12:00:00Z","duration_hours":24,"step_minutes":30,"bodies":["Sun","Moon","Mercury","Venus","Mars","Jupiter","Saturn"],"display_offset_minutes":480}
展示实际 ok、version、engine_version、sample_count、月球与木星第一个采样点高度/方位、升落和曙暮光。核对插件版本为 1.0.0；说明 preview_truncated 是展示缩略，不代表计算未完成。

2. 只将 start_utc 改为 2026-10-30T18:00:00Z，再次真实调用，比较月球高度。然后分别将 latitude 改成90、将时间改成没有Z的2026-10-30T12:00:00，检查实际中文拒绝结果，不自动修正参数。

3. 我明确授权使用以下已存在的专用工作目录，启动仅本机访问的观星界面：
/Users/IDLE_And_R/Downloads/Huawei/agentic-hub-plugins/dist/offline-observing-planner/1.0.0/manual-workspace
实际调用 local_observing_planner：action=start，workspace=上述完整路径，confirmed=true。随后用同一目录调用 action=status，展示真实版本、running、两次 session_id 是否一致及完整浏览器 URL。保留已有计划与会话；遇到其他安装或损坏记录则停止，不删除或替换。

4. 保持服务运行，指导我在本机独立 Chrome 标签页打开真实返回的地址，按交接清单操作。地址含本机会话凭据，截图时隐藏地址栏。不要把计算或启动成功当作人工测试通过；等待我独立操作后确认。不要提交、发布或上传任何内容。
```

## 浏览器人工检查

1. 选择新加坡示例并计算。应有 49 个时刻、7 个天体；12:00Z 月球高度约 −38.212°、木星约 −74.018°。这些是回归参考值，必须以实际工具/界面结果核对。
2. 拖动滑块到 18:00Z，月球高度应约 36.733°，图表与数值表同步。UTC+08 显示时间应比 UTC 多8小时；并非自动时区或夏令时推断。
3. 更改纬度为40，确认旧图表和数值立即清除、CSV 禁用；重新计算后产生新结果。固定偏移只改显示时间，不改同一 UTC 的物理位置。
4. 保存参数，修改后读取；刷新再读取，检查地点/时间/对象恢复。已有保存计划需要确认替换；不想覆盖可取消。读取/导入后应重新计算，不展示旧星历。
5. 导出 JSON，再导入该文件并重算；导出 CSV，检查实际行数、UTC、天体和高度/方位。49时刻×7天体应为343数据行，不含表头。
6. 检查无效 UTC、超范围纬度及跨越2100年边界的区间报错；不应保留旧成功结果。阅读升落/折射约定与未来月球精度限制。
7. 保存显示版本、图表变化、数值和保存/导出等关键操作的原始截图；隐藏带凭据的地址栏。测试完成后明确反馈本版本和包是否通过。

## 已完成与待完成

已完成：27项数值/参考/运行时测试；安装后真实 SDK 注册2工具+1Skill并执行12次调用；实际 WorkSwarm 导入/安装/目录和直接/前端代理 WebSocket；中文浏览器计算、滑块、失效清除、保存/刷新、JSON导入导出和CSV核对。SDK调用在单独进程，**不是实际聊天工作进程调用**。用户会话与人工验收待完成。

只支持2000–2100年、纬度±80°、最长24小时的七个太阳系天体。未来月球参考个例与JPL约差1.4角分；不保证全范围1角分精度。无天气、地形、光污染或真实可见性预测，无恒星、卫星、望远镜控制或导航。桌面macOS已测试，Linux/Windows/移动端未实测；Windows不支持当前运行时。

服务空闲约30分钟自动关闭；关闭后在原会话再次调用 start 可恢复同目录保存参数。测试完可明确授权 action=stop、confirmed=true 关闭本插件服务，已保存计划保留。无需重启 WorkSwarm 或改模型配置。
