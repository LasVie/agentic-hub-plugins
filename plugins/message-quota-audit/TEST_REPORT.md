# 功能测试记录

2026-10-23；Cai Zhenze；CAND-DSH-070；AH-20261023-message-quota-audit。

环境：macOS arm64，Python3.12.14，SQLite标准库；使用现有独立venv，不安装新增依赖。来源：gate0.6.1/d78a82699722f0da6ae3d2b4cbdbaa411f2f67af，ported/MIT。源代码已实际运行，未调用模型或上游服务。

已执行：`python -m unittest discover -s tests -p test_message_quota_audit.py -v`，31项全部通过。覆盖：中文/英文回执、深度/配对窗口、在线收件人和离线每次数量、恰好限额/下一单位拒绝、预览不占额、独立发件人/桶、同ID幂等/内容冲突、显式登记确认、策略修订号/重复初始化保留、已有记录后锁定时区、日界/DST、外部时间/回退、逐记录对账、最近日范围、线程竞争、独立进程竞争（8进程竞争3额度）、同ID并发、SQLite写锁超时、坏/空/缺表/损坏记录、权限/符号链接、路径穿越、坏JSON/类型/时区和实际CLI中文输出。正文未在账本或结果中出现；只读操作前后数据库字节一致。

`python tools/asset_release.py check plugins/message-quota-audit`通过。`audit-upstream`仅提供自动MIT-like证据；许可结论及逐路径范围另见SOURCE_REVIEW.md。测试运行生成的本插件__pycache__已清理；后续验证禁写字节码。

## 打包与解包

`python tools/asset_release.py pack plugins/message-quota-audit`成功，生成市场ZIP及artifact.json；确定性原生包由build_local_test_package.py从市场内层导出。市场SHA-256：0eb6d3f295db16ceb21717927cefeb21c081b3d2fd1408d9af68d9c61da5a4df；原生SHA-256：61dff8962b7f481f9ae89eb6fdad0ef77f67e78d987f52c0652bdcdb3c31a9a6。

解包目录dist/message-quota-audit/1.0.1/extracted。以MESSAGE_QUOTA_TEST_PAYLOAD指向解包载荷再次运行上述31项测试，全部通过。市场/原生/源码9个文件逐哈希相同；MIT许可SHA与原始全文相同；原始源文件头逐字保留；无缓存、运行状态、测试文件或额外目录入包。README、SKILL、工具描述、CLI帮助/错误均为UTF-8简体中文，兼容标识/协议值及原法律文本保留。实际中文输入/错误/结果测试通过。package-verification.json保存逐文件哈希。

## 实际宿主资格检查

新任务专用WorkSwarm源代码固定3ef1de9bf0b4813e2a0e8674dedc499c78e53df2，数据/配置/缓存/任务目录独立在/private/tmp/message-quota-audit-workswarm-20261023。源码使用只读git archive，LFS过滤只对归档调用关闭；venv/前端依赖只读复用。未复制其他实例凭据或修改Main。前端6386、web29250、agent28250、gateway30250均在启动前验证空闲，保留已有进程。

2026-10-23T08:38:24Z真实检查：前端HTTP200/HTML；直连后端及前端代理WebSocket ping/pong、config.get、plugin_packages.list成功。真实plugin_packages.import_local读取确切原生ZIP，install成功；保留原插件ID。实际installed目录在本任务数据根内，9文件与源码/两个ZIP完全相同。

通过宿主find_plugin_manifest→load_plugin_package→resolve_plugin_parts解析1技能/4真实Tool类；真实invoke/stream共17次通过，包括配置、预览、登记、重复/冲突、恰好配额/超额、离线、回执/链深、旧修订号、汇总/两类对账、重新加载读取持久状态。全程网络审计钩子禁连，0网络尝试、0模型调用；没有构造模型Agent或发送测试消息。实际返回见host-verification.json。

实际浏览器检查：http://127.0.0.1:6386 → 扩展 → 我的扩展 → 详情，中文名、描述、技能说明及四工具标签无乱码/截断。AI检查图保存在/private/tmp/message-quota-audit-workswarm-20261023/runtime/extensions-details.png，不是用户测试证据。

较早资格检查也在上一独立周期的任务自有6385实例通过，随后为手测提供上述全新实例；早期证据单独保存在runtime/previous-instance-checks，未用旧环境冒充新环境。一次健康检查初因并行RPC复用request_id失败；改用唯一UUID后成功，没有改宿主或载荷。直接源码SDK测试产生的四份日志已移至本任务tmp诊断目录，未入交付。默认沙箱禁止localhost/进程枚举的检查用授权escalated执行成功，不当作插件故障。

## 限制与下一步

原生操作系统文件选择器及真实模型对话没有由AI自动执行；已验证的是实际导入/安装RPC、宿主解析及工具调用。新实例模型故意disabled-local-test，用户对话手测需本地自行配置模型；无模型CLI也可测试。Linux宿主未执行，Windows不支持。SQLite/本地系统时间/同账户恶意修改不构成独立安全边界；记录只是用户声明。

AI功能、包及宿主检查通过，用户完成确认/原始截图仍待收集，不宣称用户测试通过。此阶段不push、开PR、合并、发布Release或操作Hub；候选保持Planned，待手测包最终readback后任务Ready for Testing。

最终复核发现替换表结构可能导致未结构化异常，已增加表列名验证与第31项回归测试；最终1.0.1的31项源码测试、31项解包测试和17次真实安装工具调用均重新通过。未向用户交付1.0.0；其预检ZIP/旧证据归档于/private/tmp/message-quota-audit-preflight-1.0.0，不纳入交付。当前只保留1.0.1原生/市场包。全仓check-repo为30源码资产、38发行ZIP，通过（结构检查不等于用户确认）。

2026-10-23 Phase3：用户在当前独立会话明确确认1.0.1手测完成且通过，提供4幅原始全分辨率PNG。ZIP/载荷未改变；只读核对用户账本revision1、3记录/4单位与截图一致。具体确认、版本/哈希及原图说明见USER_TEST_CONFIRMATION.md；既往“待手测”段落为当时Build历史，不代表当前仍缺确认。最终负责人验收未收到。

Phase3整仓回归：使用已有Node22.23.3显式加入PATH/DSH_NODE_BINARY后，249项Python测试通过（1项环境条件跳过）；最初未加入Node的环境检查失败和60跳过日志单独保存在/private/tmp，未当成载荷故障或掩盖。check-repo30源码/38发行ZIP通过。所有手测载荷和两个ZIP保持原SHA；只更新外层确认/来源/测试记录及原图。
