# 家庭文档台账 1.0.0：功能测试记录

Task ID：AH-20261026-family-document-registry；Candidate ID：CAND-CLD-247；负责人：Cai Zhenze；日期：2026-10-26。

## 环境与实际源测试

macOS arm64；Python3.12.14；已有独立 WorkSwarm 环境 `/private/tmp/state-machine-audit-workswarm-20261026/venv`。核心仅用标准库，openJiuwen原生工具使用该环境已安装SDK。未改变系统依赖、其他插件或Main目录/服务；无模型请求。

实际执行：

```text
PYTHONDONTWRITEBYTECODE=1 <existing-venv>/bin/python -B -m unittest discover -s tests -p test_family_document_registry.py -v
<existing-venv>/bin/python -B tools/asset_release.py check plugins/family-document-registry
```

源功能测试46项通过，含真实SDK端到端invoke/stream；格式check通过。SDK导入出现其现有依赖的弃用警告，不属于此插件的业务失败。所有实例使用自动生成的公开虚构附件和独立临时目录，不预先初始化用户手测目录。

## 已验证行为

- 完整元数据/实际文件摘要预览、明确确认、revision=0初始化、完整status回读、独立进程重读持久记录。
- 真实月末、闰年、到期恰等于参考日/提醒边界、自定5个月有效期和1个月新近程度的包含边界。
- 未知及月份精度日期、续办中、已归档和显式替换关系分别报告；不自动推断替换有效性。
- 严格JSON/日期/ID/引用、替换环、未知字段、重复键、限额及布尔整数拒绝；保留历史ID和旧修订，合法并发仅一个更新成功。
- 工作目录外路径、点路径、软/硬链接、超大文件拒绝；缺失附件如实登记，内容变化显示changed且拒绝自动采纳；台账摘要/权限异常拒绝。
- 材料只读预览、确认/摘要/修订绑定、精确副本和中文清单；待确认材料返回complete=false；计划/源文件/输出变化拒绝；旧目录与重复输出拒绝。
- 模拟最终manifest写入失败，实际partial_output并保留现场和原件；HTML标签作为数据转义；核心操作在禁止socket创建时完成，无网络尝试。
- 真实SDK实例化3工具，执行登记、只读报告、更新、冲突、材料预览/生成/拒绝和stream一致性；未调用模型。

## 包与宿主检查

市场包装与原生ZIP均提取并核对18个载荷文件，逐文件SHA-256与源目录完全一致；安装后仍一致，无pyc或缓存。两包均保留原始MIT字节（SHA-256 `f0a46556162fa59b55fc18b145c3e58e499018693fa76b9bd4a0a9c66c1a4e88`）、第三方声明和来源修改头；版本1.0.0、中文名「家庭文档台账」、1个技能和3个工具一致。中文README、Skill、工具描述、错误、CLI帮助与材料checklist.md均作UTF-8/实际功能检查；技术字段/ID及原始许可保持原值。

源、市场提取、原生提取、实际安装目录分别执行本插件46项测试，全部通过；每轮真实SDK验证16次invoke/stream调用，覆盖3个工具，无模型调用。输入目录均独立，手测目录仍没有台账或材料输出。

复用本聊天已有独立实例 `/private/tmp/state-machine-audit-workswarm-20261026`：前端 http://127.0.0.1:6392/ 返回200/HTML；6392代理和29290后端WebSocket均ping/pong成功，config.get与插件目录接口正常。Extensions实际import_local及install成功；中文名、说明、1技能、3工具由CUA界面核对。原状态机插件条目和宿主config.yaml哈希均保持不变，不占用新端口，不重启服务，不操作Main。宿主保留disabled-local-test占位模型；聊天手测前需用户在此实例自行选择/配置模型。

实际身份：市场ZIP SHA-256 `7434f44e68a3a42850c423019c7449f467c4d89d22896f2dea30087cc174dc56`，67920字节；原生ZIP SHA-256 `9316d2dd294f4ea488b65a7a466884d46c99f74dd198bfbc6d9ed29815bb3b37`，65589字节。详情见package-verification.json和host-verification.json。以上均为助手自测，不是用户手工完成确认或其原始截图。

## 仓库回归与环境说明

按requirements-dev.txt的最小PyYAML6.0.3依赖配置，使用现有Node22.23.3和本地回环权限，完整测试运行447项，381项通过、66项明确跳过；check-repo通过38个源资产/47个ZIP，未改变其他资产。真实SDK验证另在上述宿主环境独立执行。

最初广域SDK环境运行：默认Node不可用和沙箱禁本地监听造成旧插件环境错误；改用现有Node/回环权限后，457项运行仅剩一个已有测试的SDK兼容问题：offline-backup-recovery的unittest.assertWarns遍历模块时触发openJiuwen懒加载 `store.__warningregistry__` 的ModuleNotFoundError。未修改该插件、SDK或测试；改用仓库声明的最小测试依赖环境后通过，本插件真实SDK测试在子进程隔离运行且通过。完整混合SDK环境的这个旧问题未被伪称修复，不属于新包功能失败。

实际命令与原始自测记录在本任务忽略目录 `dist/family-document-registry/1.0.0/development-evidence/`；不将调试日志/真实用户资料打入ZIP。打包测试不能替代功能测试，助手自测不能替代用户测试确认。

## 限制与未验证事项

仅macOS/Linux；Windows未支持。无OCR、正文语义提取、加密、自动脱敏、自动整理/删除、提醒后台、云同步或法律规则。未知/月份精度不能证明有效。只核对字节一致性，不认证来源或抵御同一系统用户恶意篡改；没有文件系统原子快照。输出目录创建后可能短暂不完整，失败/断电现场保留。用户人工测试、真实私人资料、生产数据、大规模运行和机构受理/法律资格均未验证；需停止等待用户对确切包的人工测试及原始截图。
