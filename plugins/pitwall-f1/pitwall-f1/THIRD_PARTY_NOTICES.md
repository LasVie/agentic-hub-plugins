# 第三方声明

## Pitwall F1

- 上游：https://github.com/darshjoshi/pitwall-f1 ，固定提交 `04d65d386d96b85362e2eec37f39ca9018b13ee3`（版本 1.0.0）。
- 版权声明：Copyright (c) 2026 Darsh Joshi。
- 许可：MIT。完整许可文本（含免责声明）随包提供：`licenses/pitwall-f1/LICENSE`，内容与上游固定提交的 `LICENSE` 逐字节一致。
- 实际复用范围：上游 `pitwall.py` 中的两部分——(1) `CIRCUIT_NAME_MAP` 赛站/国家/城市到 Ergast circuitId 的对照表；(2) Jolpica-F1 历史成绩、积分榜、分站冠军、赛道最快圈的 Ergast 请求路径思路。这些内容在 `tools/pitwall_tools.py` 中改编，文件头部注明了来源。
- 修改摘要：改为简体中文输出和结构化结果；增加中文赛站别名、参数校验、请求限流与缓存、显式错误码；`f1_historical_results` 的取数规则、`f1_race_winners_history` 的单次请求方式与 `f1_circuit_fastest_lap` 的口径说明与上游不同；把上游的车手积分榜、车队积分榜与总积分榜合并为 `f1_championship_standings`。
- 未复用：上游的 FastF1 工具、F1 官方计时流工具、实时 SignalR 工具、绘图、`.claude-plugin`/`.mcp.json` 配置、`skills/f1/SKILL.md`、README 与图片资源。本插件的 `SKILL.md` 与 README 为独立编写。
- 授权范围说明：MIT 许可覆盖上游源代码；不授予 Formula 1 商标、数据、字体、图片或任何第三方服务的权利。

## 数据服务（未随包分发，不属于代码授权范围）

- Jolpica-F1（https://api.jolpi.ca/ergast/f1）：Ergast 数据的社区延续，运行时匿名访问；使用请遵守其公开的访问规则。
- OpenF1（https://api.openf1.org/v1）：运行时匿名访问其免费历史数据。OpenF1 官网标注免费额度为个人使用，每秒 3 次、每分钟 30 次请求；本插件内置限流并留有余量，不用于批量抓取或商业服务。OpenF1 部分的代码为本团队独立编写，不含上游代码。
- 本插件不附带任何赛事数据集、图片或标志，也不使用 F1 官方计时流或需要账号的接口。

## 商标声明

本插件是非官方工具，与 Formula 1、FIA、Formula One Management 及各车队无关联、未获其认可。F1、FORMULA 1 及相关标志是 Formula One Licensing B.V. 的商标；其他名称归各自权利人所有。
