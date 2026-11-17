# 人工测试：离线水与蒸汽物性工作台 1.0.0

请测试提供的原生 `offline-steam-properties-workbench-1.0.0-workswarm.zip`。规范交付 ZIP 的内层插件内容相同。版本、两包 SHA-256 见 test-packages/companion-artifact.json。

安装要求：macOS11+，标准 CPython3.11+（启用GIL），已安装 NumPy1.20+，兼容 WorkSwarm 原生插件。上传原生 ZIP 并启用插件。不要修改宿主或其他插件，不要付费调用。

1. 在系统中创建一个新的空专用目录。把下方 workspace 替换为其绝对路径；不要使用别的实验工作目录。
2. 让 WorkSwarm 实际调用 `calculate_water_properties`，参数如下。读取工具真实返回，不能用预期值、估计或临时生成实现冒充：

```json
{"project":{"schema":"steam-properties/v1","name":"人工测试：常压水","state":{"pair":"PQ","pressure_pa":101325,"quality":0},"sweep":{"variable":"pressure_pa","start":10000,"end":2000000,"points":25}}}
```

预期：饱和温度373.1243K左右；液体比焓419057.73J/kg、蒸汽2675529.33J/kg、汽化潜热2256471.59J/kg左右。将quality分别改为1和0.5重算；0.5比焓约1547293.53J/kg。记录实际值及是否符合。

3. 实际调用 `steam_workbench`：

```json
{"action":"start","workspace":"/替换为刚创建的专用目录","confirmed":true}
```

打开工具真实返回的 URL。若目录/引擎不可用，应报告具体错误并停止冒充成功；不要反复询问同一次启动授权，不要自动关闭工作台。

4. 工作台中重置并计算，核对常压水结果与单位。切换比焓/密度/潜热曲线；鼠标移动与左右方向键、Home/End 查看采样点，展开 SI 原始表核对。选择“过热蒸汽”和“温度扫描”示例并计算。
5. 修改压力或干度，确认旧结果/CSV/SVG 立即失效。计算中点击取消，再次计算应恢复。饱和线附近 PT 应出现中文提示，可用 PQ/TQ 恢复。
6. 保存并导出项目 JSON、结果 CSV、曲线 SVG。刷新只恢复输入，不恢复旧结果；导入刚下载的 JSON 再计算应一致。测试重复字段/非法数值/额外script字段，应中文拒绝且不执行内容；重置后恢复。不要把界面 kPa/°C 直接当成 JSON 的 Pa/K。
7. 保存后点击“关闭工作台”。反馈关闭后，让 WorkSwarm 实际调用同一workspace的 `steam_workbench`、action=status，核对running=false。不要提前用stop代替关闭按钮测试。禁用/卸载前先关闭服务。

请反馈当前包是否测试完成/通过、实际错误，并保留当前版本关键操作/数值/曲线/导入错误/关闭状态的**原始完整分辨率截图**。人工通过前不进行GitHub交付。请勿公开分享含访问令牌的工作台URL。
