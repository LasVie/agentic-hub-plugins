# 测试报告 — 日本雨量预警助手 1.0.0

Owner: Nguyen Trung Dung. Tested 2026-11-12 (Asia/Singapore), Windows 11, Python 3.11.9, openjiuwen 0.1.20.post1, pydantic 2.14.3（SDK 位于既有测试 venv）。
Task AH-20261112-japan-rain-alert; Candidate CAND-CLD-203. 本报告的所有结果都针对**最终 ZIP 的解压内容**；ZIP 哈希记录在 `test-packages/native-artifact.json` 与 `releases/agent-plugin/japan-rain-alert/1.0.0/artifact.json`，本文件不含 ZIP 哈希以免循环引用。

## 被测包

- 原生安装包：`test-packages/japan-rain-alert-1.0.0-native.zip`（交给用户在 WorkSwarm 导入的包）；
- 带市场外层的交付包：`releases/agent-plugin/japan-rain-alert/1.0.0/japan-rain-alert-1.0.0.zip`（由 `asset_release.py pack` 生成，成员未压缩）；
- 两个包解压后的内部 6 个文件逐路径、逐字节与源码目录 `japan-rain-alert/` 一致（SHA-256 逐项比较，三方相等）。

## 格式与安全检查

- `asset_release.py check plugins/japan-rain-alert`：`format_ok: true`。
- `asset_release.py preflight`（动态 JavaScript 签名）：对源码目录和两个确切的 ZIP 分别运行，均为 0 个 JS 文件、0 个已知签名。
- `asset_release.py check-repo`：本机 `core.autocrlf=true` 会让 47 个既有资产的 CRLF 许可文件报错，因此在 `core.autocrlf=false` 的干净克隆中加入本包后运行，通过（71 个源资产、84 个发布 ZIP，仅结构检查）。
- 解压核对：许可文件 `licenses/amedas-rain/LICENSE` 为 1066 字节，SHA-256 `65872a34…d81d92`，与上游固定提交 blob `cc33daf8…` 的内容逐字节一致，也与 `provenance.json` 的 `license_evidence` 一致；`THIRD_PARTY_NOTICES.md` 在包内；包内没有缓存、隐藏文件、符号链接或编译产物。

## 单元测试（离线，31 项）

`tests/test_jma_tools.py`，分别对**原生包解压目录**和**市场包内部解压目录**运行（环境变量 `JAPAN_RAIN_ALERT_PAYLOAD` 指向解压目录，并断言被导入的模块确实来自该目录）：两处均 `Ran 31 tests … OK`。覆盖：

- PNG 解码：色彩类型 0/2/3/4/6、五种行滤镜（含逐行不同）、调色板 1/2/4/8 位与 tRNS 透明度、交错/16 位/截断/索引越界/体积炸弹被明确拒绝；
- 解析与公式：邮编/经纬度解析、z10 瓦片编号、色阶最近色（含最弱一档）、Stull 湿球温度示例、WBGT 分级、参数校验、限流拒绝而非等待；
- 都道府县名：47 个站号互不相同，简体/日文/带 都府県县 的写法，同名站（山形、山口）不被选错；
- 五个工具在模拟数据源下的行为：定位（邮编、站名、简体别名、候选、境外、查无）、日降水量累加与不完整日标注、无数据返回错误而非零、警报按要素取最高级别并排除已解除与其他市町村、展望截断、区域无法解析、瓦片色块读取与 UTC→JST、空瓦片、不支持的瓦片格式、WBGT 日射修正有/无及缺测保持为空、逆地理编码限流被如实报告而其他失败降级并提示、每个结果都带来源署名与非官方声明。

## 真实宿主检查（无模型调用）

`tests/host_checks.py --live`，对两个解压目录分别运行：真实 DeepAgent + SkillUseRail + Runner 加载插件；五个 `jma_` 工具以 direct 方式对模型可见，描述均含中文；经 Runner 注册的工具对缺参数、未知字段、越界值返回 `INVALID_ARGUMENTS`；经 Runner 实际调用 `jma_locate`、`jma_rainfall`、`jma_warnings`、`jma_site_rain_risk`、`jma_wbgt` 成功（东京站 44132、2 天雨量、千代田区、3 个キキクル图层、WBGT 值），境外坐标被拒绝；卸载后工具全部消失；**加载、调用、卸载前后载荷目录逐文件哈希不变，即没有向插件目录写入任何文件**。`model_calls: 0`。证据：`host-native.json`、`host-wrapped.json`（保存在仓库外的 `D:/jiuwen_repos/outputs/jma-build/evidence/`）。

SDK 在加载 SKILL.md 时打印一条 `Failed to load description … 'NoneType' object has no attribute 'fs'` 警告；对已通过用户测试的 pitwall-f1 运行同一脚本得到完全相同的警告，属于该测试脚本无工作区的环境现象，不是本包问题。

## 真实服务检查（2026-11-12 02:41 UTC，即新加坡时间 10:41、日本时间 11:41）

`tests/live_checks.py`，对两个解压目录各运行 25 个用例：均为 20 个成功、5 个预期错误（`PLACE_NOT_FOUND`、`OUT_OF_COVERAGE`、`AMBIGUOUS_PLACE`、两个 `INVALID_ARGUMENTS`）。成功用例涵盖邮编 100-0005、坐标、日文站名、简体“东京”、日语地址（長野県松本市丸の内3，最近站松本 1.0 km）、旭川（预报区 上川・留萌地方 012000）、“冲绳”“神奈川県”“山形”、雨量（东京 4 天、邮编 2 天、station_code）、警报（千代田区无警报；旭川无警报；那覇/“冲绳县”有真实的波浪注意報）、两处 1 km 网格、WBGT。典型耗时：定位 0.1～6 秒，4 天雨量约 10 秒（约 30 个数据块请求，受限流间隔约束），其余 0.5～3 秒。证据：`live-native.json`、`live-wrapped.json`。

- **独立复算**：不导入本包的 stdlib 脚本（`independent_check.py`）从气象厅原始数据重新累加东京站 4 天雨量，得到 11-09 11.5 mm、11-10 6.0 mm、11-11 0.0 mm、11-12 0.0 mm（合计 17.5 mm），与工具逐日一致；WBGT 在 11-11 08:30/13:00 与 11-12 08:30 的原始气温湿度重新代入公式，与工具逐项一致（7.0、9.8、9.4），尚未到来的 11-12 13:00 正确返回空值。结果见 `independent-check-output.txt`。
- **解码器对真实数据**：`tests/real_tile_check.py` 在当天确有降水的真实瓦片（z6 的 56/24、57/24、56/25，分别有 2077、89、14 个有色像素）上，本包的 `decode_png` 输出与 Pillow 逐字节相同；并在三个有降水的坐标上，工具的解析雨量档位与独立读取 z10 瓦片 3×3 像素的结果一致。这次检查发现上游色阶表缺少最弱一档 (242,242,255)，已补为“0～1 mm/h（微弱降水）”（依据见 SOURCE_REVIEW.md），修复后重新构建并重测。Pillow 只在这个可选的开发检查中使用，不在包内。
- **都道府县**：`prefectures_check.py` 对 47 个都道府县名逐一定位：全部落在对应府县厅所在地的观测站，市町村代码在对应都道府县内，且解析出预报区（47/47，0 个问题）。

## 中文检查

- 包内说明（manifest 显示名与描述、README、SKILL.md、五个工具的描述）均为简体中文，UTF-8；工具的默认输出（`summary_zh`、`warnings_zh`、错误提示）均为简体中文，日文地名、观测站名和警报名称保留原写法。
- 用中文输入走了主要流程：“东京”“冲绳”“冲绳县”“神奈川県”“山形”“那覇”等定位，以及中文提示词对应的参数；错误与帮助信息为中文（如“zipcloud 查不到邮编 999-9999”“该位置在日本以外…”“匹配到 65 个观测站，请换更完整的地名…”）。
- 用真实语言模型在 WorkSwarm 前端里的对话测试由用户完成，见下一节。

## 用户在 WorkSwarm 前端的测试（2026-11-12 11:13～11:22，新加坡时间）

测试人 Nguyen Trung Dung，在 WorkSwarm 中启用“日本雨量预警助手”，用真实语言模型跑了 15 个提示（东京 4 天雨量、邮编 100-0005 警报、坐标 1 km 网格、东京暑热指数、旭川警报与展望、冲绳、松本地址雨量、山形、“大”（多站歧义）、邮编 999-9999、伦敦坐标、30 天雨量、“我现在的位置”、停工标准对照、明天是否下雨）。聊天导出和截图为用户提供的原图，已在对话中逐张查看：

- 五个工具均被真实调用且返回成功：`jma_rainfall`、`jma_warnings`、`jma_site_rain_risk`、`jma_wbgt`（截图 2～5 为工具调用面板），截图 1 显示插件已启用。
- 版本核对：截图中的结果含 `alias_note` 字段和“无降水（该格没有降水色块）”措辞，二者只存在于最终构建中，与交给用户的 ZIP 一致。
- 行为与预期一致：东京/那覇/松本/山形取到正确的观测站；冲绳按“府县厅所在地”处理并向用户说明（“只代表那覇市”）；多站歧义返回 65 个候选而不替用户挑选；邮编查不到、境外坐标、30 天超限均明确报错，没有写成零；缺测的 13:00 暑热指数说明“不是零”；暑热指数说明未做日射修正、估算偏低；用户要求对照停工标准时只并列数值，“停工与否由你方负责人决定”；不预测，只转述气象台展望；每个回答都带数据来源和“非官方、经加工”的说明；不知道位置时要求用户提供坐标/邮编/地址而不猜测。
- 观察（不是缺陷）：多数回答是英文。用户说明这是因为其 WorkSwarm 的首选语言设为英文；工具输出本身为简体中文，提示里写明“用中文概括”以及“大”一例时回答为中文。SKILL.md 正文没有单独的“默认简体中文”条款，若以后需要在英文界面下也默认中文，可在新版本里加入。
- 用户结论：“screenshot and chat export image is in verification_screenshot folder in the workspace, please verify and proceed to the next steps”，并说明英文回答是其语言设置所致、“shouldn't be an issue”。无阻塞问题。

用户提供的原始图片（SHA-256）：

| 文件 | SHA-256 |
| --- | --- |
| Screenshot 2026-11-12 112300.png（插件已启用） | 853ab821f00c07a66af1f70a9908000c1cfb2499c01cc807526c2a73ccba77f9 |
| Screenshot 2026-11-12 112313.png（jma_rainfall） | 4bd1966fdb19bc9bd3fda47154709400778d72a11272ed7d32b150b9bbdfef1a |
| Screenshot 2026-11-12 112328.png（jma_warnings） | 587e253a8ed27568ce29624e43a973399d71c68797e7e4cb3d2c3bc8d711cb13 |
| Screenshot 2026-11-12 112342.png（jma_site_rain_risk） | 0e6f88c9729abbf5ff52f86ea88e4bee6c9343e54d37124be300c6305a41b0be |
| Screenshot 2026-11-12 112355.png（jma_wbgt） | f4de92827f46d00b257433f65f7769ecc2738da7693b4fa7c02c8b9d74237bf9 |
| jiuwenswarm-share-20261112-112251.png（完整聊天导出，2250×51588） | 2047fb22b8ac55d3232aa9ad7a9fa6b3caa400317f9487f31352ab38df874cc4 |

这些图片附在交付 PR 的证据评论中；本仓库不提交它们。

## 未覆盖与局限（如实记录）

- 上面的宿主检查是 SDK 级别（真实 DeepAgent/Runner，无模型）；前端对话测试由用户完成，见下一节。
- 当天东京等地没有降雨和警报，高于 1 级的キキクル色和较强的降雨档位只用按上游色阶表构造的合成瓦片验证；真实数据验证只覆盖了弱降水档（见上）。
- 日射修正路径只用模拟数据测过：环境省官方实况文件只在 4 月下旬至 10 月下旬提供，测试时（11 月）不可用，所以真实运行中是“未做日射修正”，工具会明示估算值可能偏低。
- 本包内置限流：国土地理院每分钟 30 次、zipcloud 每分钟 10 次、气象厅每分钟 150 次；连续快速查询超过上限会得到 `RATE_LIMITED`，不是故障。
- 上游脚本本身没有被运行（本地安全策略阻止执行下载的代码）；本包的行为由自己的测试和独立复算验证。

## 开发过程中的一次事故（与包无关，已处理）

写独立复算脚本时漏了循环里的日期递增，该脚本在后台对气象厅同一批 8 个数据文件无间隔地重复请求了约 11 分钟（按循环节奏估计约 2,000～3,000 次），发现后立即终止，修复脚本（增加递增和 0.3 秒间隔）并重跑。事后 JMA 三个端点仍正常返回 200，没有发现被限制。该脚本不在包内，也不会随包分发；包内工具自带限流，不会出现这种行为。

## 已知问题

无阻塞性问题。用户测试前请知悉：第一次查询要下载观测站表和区域表，会慢几秒；4 天雨量约 10 秒；邮编查询依赖第三方 zipcloud，失败时可改用地址或经纬度。
