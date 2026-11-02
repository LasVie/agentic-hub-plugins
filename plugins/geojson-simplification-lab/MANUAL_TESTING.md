# 离线地图简化工作台：手动测试

插件版本：**1.0.1**。候选：`CAND-EXT-004`。任务：`AH-20261030-geojson-simplification-lab`。负责人：Cai Zhenze。

本文是待执行的测试说明，不代表用户已经测试通过。本次版本已完成打包及包身份核验，请核对以下文件和 SHA-256 后按步骤测试。

## 本次环境和安装包

- WorkSwarm：<http://127.0.0.1:6394/>。使用 macOS/Linux、宿主 Python 3.11+ 和近期桌面 Chrome；浏览器与服务位于同一台机器。
- [下载原生测试 ZIP](/Users/IDLE_And_R/.codex/worktrees/581d/agentic-hub-plugins/dist/geojson-simplification-lab/1.0.1/geojson-simplification-lab-1.0.1-workswarm.zip)：这是在 WorkSwarm **Extensions** 中导入的文件。SHA-256：`32b0bb79a8881d184ea5ad5f01a19357c3c6dfb313fe63dc769795d6f9753e1a`。
- [保留的同字节原生 ZIP](/Users/IDLE_And_R/.codex/worktrees/581d/agentic-hub-plugins/plugins/geojson-simplification-lab/test-packages/geojson-simplification-lab-1.0.1-workswarm.zip)：与上项完全相同，SHA-256 相同。
- [市场包装 ZIP](/Users/IDLE_And_R/.codex/worktrees/581d/agentic-hub-plugins/releases/agent-plugin/geojson-simplification-lab/1.0.1/geojson-simplification-lab-1.0.1.zip)：SHA-256：`5bc7e39e5db5fd92cfc07ad9638fd225f6a4c7cb5b0eaf26c3eaff1d1fa79141`。不要将此市场包装误当作原生测试包导入。
- [包身份记录](/Users/IDLE_And_R/.codex/worktrees/581d/agentic-hub-plugins/dist/geojson-simplification-lab/1.0.1/companion-artifact.json)：版本 `1.0.1`，`payload_identical: true`。已核验两种 ZIP 的全部 **75 个内层文件**文件名和字节完全相同；两种 ZIP 仅包装结构不同，因此整体哈希不同。

以上文件位于本任务工作树：

```text
/Users/IDLE_And_R/.codex/worktrees/581d/agentic-hub-plugins
```

开发验证安装已通过支持的卸载接口移除，自己的验证服务已停止；此专用宿主当前插件目录为空，便于你亲自导入。在 **扩展 → 我的扩展 → 创建 → 上传文件创建** 中导入原生测试包，再安装并启用，确认显示“离线地图简化工作台”和版本 1.0.1。浏览器中的地图计算不需要模型或地图账号。当前隔离 WorkSwarm 的聊天模型未启用；本次手动测试需要你在 **Settings** 中按平常方式配置自己的可用模型，再由你发送下文聊天指令并核对真实工具调用结果。已有自动检查不能替代这一步。不要通过修改数据库、复制另一会话的密钥或修改宿主来绕过设置；本任务不授权代理发起付费模型调用。

## 1. 使用专用目录检查真实工具

本次预留目录如下，仅创建空目录，未预写运行记录。不要改用其他插件或 Main 会话的目录：

```text
/Users/IDLE_And_R/.codex/worktrees/581d/agentic-hub-plugins/dist/geojson-simplification-lab/1.0.1/manual-workspace-user-20261030
```

在聊天中发送以下指令。目录首次测试应为空；如果你已用它启动过服务，应按真实状态核对，不能把后续复测当成首次启动。

```text
请使用已启用插件的真实 geojson_workbench 工具，workspace 为：
/Users/IDLE_And_R/.codex/worktrees/581d/agentic-hub-plugins/dist/geojson-simplification-lab/1.0.1/manual-workspace-user-20261030

先 action=status，只读检查状态。随后我明确授权用这个目录启动离线地图简化工作台，请 action=start、confirmed=true。再以相同参数调用一次 start，验证复用；最后调用 status。请逐项展示工具实际返回的 ok、version、running、reused 和 url，不要用命令行、猜测地址或文字模拟代替工具调用。若工具报错，请保留错误并停止后续操作。
```

预期结果：

1. 空目录首次 `status` 返回 `ok: true`、`version: "1.0.1"`、`running: false`，不创建运行记录。
2. 首次 `start` 返回 `running: true`、`reused: false` 和实际 `url`。
3. 第二次 `start` 返回 `reused: true`，地址与仍在运行的同一实例一致。
4. 最后 `status` 确认服务仍在运行。打开该次工具返回的实际地址；插件服务端口与 WorkSwarm 的 6394 端口不同，由系统分配，不能自行拼接。

如果出现 `invalid_runtime`，停止当前流程，保留原记录，不删除、覆盖、改权限或强停未知进程。它可能来自另一安装位置或异常记录；为当前安装准备新的专用空目录，再重试。更换安装位置时也使用新目录。`invalid_workspace` 表示目录路径不合要求：必须已存在、为绝对真实路径，且没有 `..` 或符号链接。

## 2. 相邻区示例与 20% 简化

1. 页面应显示“离线地图简化工作台”“插件 1.0.1”和“Mapshaper 0.7.101”，中文正常，无乱码。
2. 点击“载入相邻区示例”。保持目标保留比例 **20%**，点击“运行简化”。
3. 应显示“简化完成”，结果顶点少于原图顶点，两区仍可见。切换“原图”“简化结果”复选框，对照蓝色虚线与绿色边界，重点观察两个区域的公共边界。
4. 检查要素数前后仍为 2；检查顶点、环、组成部分与紧凑 JSON 字节数。目标 20% 是简化阈值选择，不保证结果顶点恰好为原来的 20%。顶点统计不包含各环最后的重复闭合点。
5. 在“要素属性”中逐项切换，检查示例的 `id` 与中文属性保留。属性以只读 JSON 显示，不能执行其中的 HTML 或指令。

请保留显示版本、20% 比例、边界对照、前后统计与要素属性的原始清晰截图。该示例是虚构区域，不用于真实行政区划或测绘判断。

## 3. 下载、重新导入和设置失效

1. 导出 GeoJSON 和 SVG。浏览器应分别下载 `地图简化-20pct.geojson`、`地图简化-20pct.svg`（浏览器可为重名下载加后缀）。原文件不应被覆盖。
2. 打开 SVG，确认能看到几何与固定样式。SVG 不是带交互控件、属性脚本或底图的网页。
3. 重新选择刚下载的 GeoJSON，点击运行；确认文件可读、两项要素及 `id` / 属性保留。可先把比例设为 100% 再运行作检查，但 100% 不承诺逐字节不变或几何完全不变。
4. 再载入自带相邻区示例，以 20% 运行。改变比例但不点击运行：旧结果、旧统计、旧属性和导出按钮应立即失效。重新运行后才可导出当前比例结果。
5. 在“GeoJSON 原文”中加一个合法空格但不点击运行，也应立即清除旧结果并禁用导出。点击“恢复导入原文”：恢复最近导入的原文、比例改为 100%，仍需重新运行。
6. 如果计算过程中来得及点击“取消计算”，应显示取消状态，旧结果不可导出；随后正常运行应恢复。小示例可能很快完成，未实际取消成功时不要把该项记为已验证。12 秒上限属于自动保护，不要求通过构造超大数据来手工触发。

## 4. 中文错误与恢复

先确保已有一次成功结果。把原文替换为以下未闭合环，再运行：

```json
{"type":"FeatureCollection","features":[{"type":"Feature","id":"未闭合环","properties":{"名称":"错误检查"},"geometry":{"type":"Polygon","coordinates":[[[0,0],[1,0],[1,1],[0,1]]]}}]}
```

应出现中文输入错误，并保留可识别的技术错误码；旧结果和下载按钮不可继续使用。再次点击“载入相邻区示例”，设为 20% 并运行，应恢复正常。请保留错误和恢复结果的原始截图。

还可将示例中一个数字属性改成 `9007199254740993`，确认程序拒绝不安全整数；把该编号写成字符串后可作为属性保留。不要期待数值格式、空格或对象字段排版逐字节保留。

## 5. 损失提醒与已知边界

- 输入仅支持有限的二维 WGS84 `Polygon` / `MultiPolygon` FeatureCollection：2 MiB、200 个要素、40,000 个坐标以内，坐标数包含闭合点。拒绝点线、Z/M、未闭合或零面积环、重复 JSON 字段、超范围坐标、`crs` / `bbox` 扩展和跨日期变更线数据。
- 共享边界必须具有精确相同的坐标。工作台没有底图、坐标投影转换、远程导入、任意命令或自动修复功能。
- 形状保护尽力保留每个要素的主要环，**不保证每个小岛、孔洞或组成部分都保留**。如用自己已知有效的小岛或带孔数据测试，请提高或降低比例，对照环和组成部分数量及损失提醒；不要把没有提醒理解为没有几何变化。
- 损失报告只统计环和组成部分的减少，不是所有变化的完整清单。工具不承诺面积守恒、输入/输出的全面几何有效性或测绘认证。自带两区示例不保证触发小岛或孔洞损失提醒。
- 地图数据在本机浏览器中计算，不上传给模型；导出由浏览器下载。中文错误、引擎加载失败或超时不得被当成成功结果。

## 6. 停止与测试确认

测试结束后可发送：

```text
我明确授权停止本次离线地图简化工作台。请以刚才的同一个 workspace 调用真实 geojson_workbench，action=stop、confirmed=true，再 action=status 验证 running=false。不要停止其他插件或进程。
```

插件仅停止经身份验证的本实例；空闲约 30 分钟也会自动退出。如果状态已停止，按实际结果记录，不要为得到预期日志伪造运行过程。

完成后，请明确回复本次版本及实际原生 ZIP SHA-256、测试通过或未通过、仍存在的问题，并提供显示当前版本关键操作/结果的**原始全分辨率截图**。发布交接还会核对对应市场 ZIP SHA-256 和内层一致性。截图不应暴露模型密钥、个人文件内容或完整带令牌的插件 URL；可在截图前隐藏地址栏，不要用日志代替截图。截图、代理自测或下载文件本身都不等于你的明确测试完成确认。

仅当当前精确包的测试明确完成、阻塞问题解决且原始截图齐全后，才能进入 GitHub 交付阶段。本步骤不向 Agentic Hub 提交或发布任何内容。
