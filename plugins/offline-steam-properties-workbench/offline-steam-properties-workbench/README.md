# 离线水与蒸汽物性工作台 1.0.0

在本机真实运行 **CoolProp 8.0.0 / HEOS::Water**，计算纯水与蒸汽的密度、比焓、比熵、相态、饱和液/汽性质与汽化潜热。交互查看有界饱和扫描，下载项目 JSON、结果 CSV、曲线 SVG。计算不调用模型或云服务，不发送项目数据。

## 安装

- macOS 11+，Intel x86_64 或 Apple Silicon arm64；WorkSwarm 使用 **启用 GIL 的标准 CPython 3.11+（3.x）** 和已安装的 **NumPy 1.20+**，支持原生插件 manifest/Tool/ToolCard。
- 包含两种架构的 CPython 3.11 轮子和 CPython 3.12+ 稳定 ABI 轮子。插件不会运行 pip，也不修改宿主、SDK、其他插件或共享依赖。不支持 Windows、Linux 或其他解释器。
- 通过 WorkSwarm 本地插件导入并启用文件名带 `-workswarm.zip` 的原生包。带外层 plugin.yaml 的规范 ZIP 用于交付；两者插件内容相同。
- 首先用系统文件工具创建空的专用工作目录。不要使用下载目录根、共享目录或其他任务目录。
- 保留 `THIRD_PARTY_NOTICES.md`、完整原始许可和随包源代码材料。

## 真实计算

调用 `calculate_water_properties`：

```json
{"project":{"schema":"steam-properties/v1","name":"常压饱和水","state":{"pair":"PQ","pressure_pa":101325,"quality":0},"sweep":{"variable":"pressure_pa","start":10000,"end":2000000,"points":25}}}
```

数值核对来源：[CoolProp 8 官方接口文档](https://coolprop.org/coolprop/HighLevelAPI.html)。此示例预期饱和温度约 373.1243 K（99.9743 °C）、汽化潜热约 2256.47 kJ/kg。必须读取真实工具返回；预期值不能替代执行。

调用 `steam_workbench`：

```json
{"action":"start","workspace":"/请替换为已有专用目录的绝对路径","confirmed":true}
```

打开工具实际返回的 URL；不要编造地址或公开完整会话地址。再次启动相同目录会复用身份核验成功的服务。`status` 查询无修改授权要求；`stop` 需要 confirmed=true。只停止本插件经核验的服务，不按不可信磁盘 PID 杀进程。

工作台支持示例、编辑、计算、取消、曲线切换、悬停/键盘选点、SI 原始表、导入/保存/下载项目、CSV/SVG 导出、重置并保存、关闭。输入变化立即清除旧结果并使导出失效。保存和计算会持久化有效项目；刷新只恢复输入，须重新计算。导入不会执行代码或自动计算。

## 格式、单位与范围

项目仅允许 schema、name、state、sweep；schema 为 steam-properties/v1，名称 1–80 可打印字符。JSON 最多 256 KiB。未知/重复字段、控制字符、NaN、无穷大和错误类型会拒绝。examples 中含完整示例。

| pair | state 字段 | 范围 |
| --- | --- | --- |
| PT | pair、pressure_pa、temperature_k | 1000–20000000 Pa；273.16–800 K |
| PQ | pair、pressure_pa、quality | 1000–20000000 Pa；0–1 |
| TQ | pair、temperature_k、quality | 273.16–640 K；0–1 |

Q 是蒸汽**质量分数**，不是相对湿度或空隙率。0 为饱和液态，1 为饱和蒸汽。PT 在饱和线附近无法确定干度，需改用 PQ/TQ；不自动强制相态。

sweep 仅允许 variable（pressure_pa 或 temperature_k）、start、end、points。压力 1000–20000000 Pa；温度 273.16–640 K；起点小于终点；2–100 整数点，线性采样饱和曲线。

JSON、工具返回、CSV 与原始表采用 SI：Pa、K、kg/m³、J/kg、J/(kg·K)。主视图换算为 kPa、°C、kJ/kg、kJ/(kg·K)，标签明确。压力为**绝对压力**，不是表压。焓/熵使用 CoolProp 默认参考零点，不能与不同参考系直接相减。曲线连线只供观察，以实际采样表为准。

## 保存、恢复与关闭

仅向专用目录的 `.offline-steam-properties-workbench/` 写状态，目录 0700，文件 0600，原子保存。不覆盖链接、不安全权限或其他安装路径的状态。损坏项目显示中文提示和默认输入；明确保存/重置会先保留损坏原文件备份，不能把它当有效结果。

计算由本插件自己的子进程运行，禁止网络；CPU 12 秒、墙钟 15 秒，输出有界。每次将哈希核验过的轮子解包到本次私有临时目录，结束后清理，不安装进 site-packages。取消、超时或失败后可重试。

页面“关闭工作台”或工具 stop 会取消当前服务的活动计算并退出。关闭后以同一路径 status 核对 running=false。**禁用/卸载前先关闭工作台**：宿主没有此插件可用的禁用/卸载回调，禁用本身不保证立即停止私有进程。无活动 30 分钟后服务退出。

## 边界

只支持纯水/蒸汽；没有混合物、REFPROP 运行库、自定义后端/配置、脚本/表达式、冰相、化学反应、设备设计或管网流动求解。界面是本插件自己的本机工作台。数值不代表锅炉、压力容器等设备安全认证，也不保证业务结论。
