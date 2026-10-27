# 糊涂勇者历险记 1.0.0：开发验证记录

任务 AH-20261027-fools-errand；候选 CAND-CLD-142；负责人 Wang Jie；日期 2026-10-27。

## 测试状态

Wang Jie 已在 WorkSwarm 中完成当前中文 1.0.0 包的本轮实际测试，并于 2026-10-27 15:30:55（Asia/Singapore）明确授权按 AGENTS.md 交付 GitHub。已收到当前会话中的真实用户截图，选取七张成功操作原图用于 PR 附件；确认及范围见 USER_TEST_CONFIRMATION.md。运行载荷、规范 ZIP 和原生测试 ZIP 均未改动。以下保留开发阶段的实际检查及尝试，后文补充 GUI 用户测试结果，不用静态检查代替实际游玩。

## 必须分开的证据

- 结构及文本检查：可验证路径、中文机制、数值规则描述和许可，不证明模型实际执行。
- 宿主热加载：可验证真实解析/注册 Skill，不证明模型已按规则游玩。
- 实际模型/WorkSwarm 功能测试：验证开场、选择、状态连续性、结束及无跨会话恢复。
- 用户测试：Wang Jie 操作当前 ZIP，提供原始截图并明确确认后，才满足后续交付门槛。

本包没有可执行运行代码，不为凑覆盖率添加后台引擎。未执行项始终写明未测试。

## 环境与实际命令

- macOS arm64；已有隔离开发环境 `.environments/annotate-test/bin/python` 3.11.17、PyYAML。没有新建 Conda 环境、安装 Python 包、修改 base 或全局配置。
- 本次使用的是已有隔离开发 Python，不意味着终端用户运行游戏需要它。运行载荷只有 manifest、README、Skill、第三方说明和许可，没有执行脚本或新增依赖。
- 读取 WorkSwarm 自带 plugin-creator 的完整 SKILL.md、manifest 规范与相关校验器；仅对给定源码/解压目录执行校验，没有调用 init 或 register，也没有绕过校验安装。

在 `agentic-hub-plugins-fools-errand/` 执行：

```sh
PYTHONDONTWRITEBYTECODE=1 /Users/dashing/Desktop/huaweisg/.environments/annotate-test/bin/python tools/asset_release.py check plugins/fools-errand
PYTHONDONTWRITEBYTECODE=1 /Users/dashing/Desktop/huaweisg/.environments/annotate-test/bin/python -m unittest discover -s tests -p 'test_fools_errand.py' -v
PYTHONDONTWRITEBYTECODE=1 /Users/dashing/Desktop/huaweisg/.environments/annotate-test/bin/python -m unittest discover -s tests -p 'test_*.py'
```

## 开发检查结果

1. 仓库资产格式检查通过。
2. 12 项新增检查全部通过：身份和 provenance、原生展示及快捷输入一致性、只声明一个实际 Skill、无新增可执行运行时、显式触发及缺失状态说明、初始数值与体面零点规则、等待玩家和自由行动、任务/物品契约、五类角色与知识边界、结束及无跨会话存档、禁止外部操作的文字约束、原许可与署名、确定性包装及原生载荷一致性/禁止覆盖旧包。部分条目合并在同一测试中，具体以测试文件的 12 个 test 方法为准。
3. 上述游戏规则检查是文本契约断言，不是模型行为测试，不证明模型一定遵循数值或触发规则。真实执行的打包器测试验证了档案及哈希操作，不是完整游戏引擎测试。
4. 初次全库运行受限于沙箱，本地音乐库和离线阅读器的回环 HTTP 服务启动失败。未修改它们的代码；允许本地端口后分别重跑 24 和 35 项均通过。完整回归输出为 502 项、97 项环境跳过、其余通过；日志位于 `.research/fools-errand-1.0.0/repository-tests.log`。这些跳过不算通过，也不属于本插件的运行依赖。

## 早期开发阶段的宿主校验与 CLI 尝试

WorkSwarm 内置 `validate_plugin.py <payload-path> --no-hot-load` 对源码及最终解压载荷均返回：L0 PASS（零错误、零警告）、L1 PASS（零错误、零警告）、L2 SKIP；整体 RESULT: PARTIAL，退出码 1。没有把 PARTIAL 写成 PASS。

随后去掉 `--no-hot-load` 对源码实际执行，L0/L1 仍通过，但 L2 返回：`当前 Python 环境未安装 openjiuwen（No module named 'openjiuwen'）`。尝试在单进程 PYTHONPATH 中使用应用 Resources 也没有得到可导入的完整 harness 模块（`No module named 'openjiuwen.harness.deep_agent'`）；未安装或解包应用运行时来绕过它，没有改应用文件。缺少开发运行时不证明插件本身不兼容，但本轮不能声称真实热加载通过。

实际通过 WorkSwarm 自带 CLI `jiuwenswarm-tui --session fools-errand-dev-20261027-01` 建立独立测试对话，选择默认工作区而非提升项目目录信任；请求读取本包 Skill 并开始一回合。返回：

```text
还没有配置可用的模型：请在设置里配置模型，或登录获取限时免费模型
```

因此没有实际读出 Skill、开场或状态结果；没有把开发者写的示例当作模型输出。CLI 已退出，未修改模型、账号、安全设置、已有会话或插件注册。GUI 已选模型的可用性需另行验证，不能从 CLI 默认配置失败推断 GUI 一定失败。

## 最终包和解压检查

执行 `python tools/asset_release.py pack plugins/fools-errand` 生成规范包，再通过本插件外层 `build_local_test.py` 生成同载荷原生包；两者均为版本 1.0.0。

- 规范 ZIP：`releases/agent-plugin/fools-errand/1.0.0/fools-errand-1.0.0.zip`。
- 规范 SHA-256：`5228e50c52c92de8a1b578592834007651b73f919ed941ff56386a277954fe7e`。
- 原生 ZIP：`/Users/dashing/Desktop/huaweisg/local-tests/fools-errand/1.0.0/fools-errand-1.0.0-workswarm.zip`。
- 原生 SHA-256：`f62d3ba3d1c4714bfd91538605090e6d4abf1f2b2cb3be87bc851a6291e38b21`。

规范包解压到 `.research/fools-errand-1.0.0/extracted/`，五个运行文件逐文件 SHA-256 与原生包、源码载荷及 artifact.json 一致。原始 CC BY 4.0 许可哈希 `d557539df68e771cc1eedcc91d13f70fca930e508d11eedcafa4b15db49e3744` 不变。声明 Skill 路径存在；不含缓存、开发测试、任务记录、node_modules 或上游媒体。两个 ZIP 字节哈希不同，不把一次导入称作两种包装都直接安装通过。

## WorkSwarm GUI 实际用户测试

环境：用户实际使用的 macOS WorkSwarm 桌面应用及其已配置模型；具体模型名称、应用版本没有从用户证据中获得，不作猜测。测试日期 2026-10-27；截图所示首轮操作约 11:48–11:56，补测约 15:07–15:13。会话提供图片的时间与图片中的操作时间分别记录，不相互替代。

| 实际操作 | 本轮结果与证据范围 |
| --- | --- |
| 通过扩展入口使用当前插件、中文开局 | 通过：截图显示中文名、1.0.0、农场与误认勇者的开场；用户提供的首轮后续图显示初始数值 3 / 5 / 0。安装目录的五个运行文件与源码及两个 ZIP 的哈希一致。模型关于读取 Skill 的叙述不单独当作内部注册调用日志。 |
| 单回合明确询问巫师 | 补测通过：不带字母的明确指令得到询问回应，没有替玩家救火或安抚动物；公布三项任务，全部显示未完成，给出下一轮选项后等待。新局生成不同任务是预期行为，不拿不同局的任务相互比较为中途替换。 |
| 自由行动及农场安排 | 通过：用户不选字母、要求安抚动物并与邻居商量，回复承接人物和农场安排，没有自动完成卷轴任务。 |
| 查看状态、物品和任务 | 已实际执行：显示当前状态及变化说明，物品为空、三项任务仍未完成。首轮行动输入存在歧义，不以该轮体面变化证明精确因果正确；补测截图未覆盖数值栏，不追加数值一致性已验证的结论。 |
| 主动回家并结束 | 通过已展示范围：尊重提前结束，结局列出三项任务未完成、朋友和注脚，不再给游戏行动选项。截图未包含完整结局数值栏，不声称已逐项核对最终数值。 |
| 新会话请求恢复但不提供旧状态 | 通过：说明不能可靠恢复，不编造旧金币、物品或完成任务，不未经确认直接开新局。 |
| 暂不游玩，只解释文字冒险 | 通过：正常用中文解释，没有自动启动游戏或输出游戏状态和行动选项。 |

测试提示词见 MANUAL_TESTING.md。首轮 T2 将动态选项字母 A 与“询问巫师”文字绑定，但当时 A 实际代表救火；这是测试输入冲突，该轮不作为插件失败或状态因果通过的依据。使用明确自然语言重新验证了该步骤，无须改变已测试的运行包。

早期截图还出现过一次未开始任务的删除线/标签残留，以及另一会话的英文排查与乱码；本轮明确指令补测显示中文回复和正常未完成任务。现有证据没有定位上述现象的具体来源，不推断为已确认的包源码缺陷，也不声称已经永久修复或所有模型上均可稳定复现成功。PR 附件选用用户要求的成功操作原图，不伪造或重绘图片。

完整三任务通关、获得/交付/消耗物品、体面 0/负值/上限边界、长对话稳定性及全部模型组合未实际测试，保留为未测试范围，而非失败或通过。该包是模型指令驱动的文字游戏，不提供独立确定性游戏引擎或跨会话存档。

## 当前交付状态

用户确认仅覆盖本轮测试及当前未变更的包，不替代 Song Haoran 最终验收。根据实际截图及补测，没有确立阻止本轮 GitHub 交付的包级运行故障；已具备当前范围的源代码、许可、包哈希、实际测试记录、操作说明、用户确认和截图材料。接下来按 AGENTS.md 创建 PR、附真实原图并验证链接和 CI；不上传 Hub，不冒认项目负责人验收，不提前标记 Completed / Delivered。
