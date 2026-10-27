# 家庭文档台账 1.0.0

维护用户明确确认的人员/文档元数据，在后续检查中持续保留修订和替换关系，按明确参考日核对到期、续办及日期精度。可从确认的文档 ID 计划创建新的材料副本、中文清单和 SHA-256 manifest。不会修改原始文档。

## 安装

需要 Python3.11+、macOS/Linux、兼容 WorkSwarm 原生 Plugin 宿主和其已有 openJiuwen SDK。核心无额外 pip/npm 依赖、联网或模型调用。宿主对话本身可能调用用户配置的模型。

在 WorkSwarm「扩展 / Extensions → 我的扩展」导入同版本 `family-document-registry-1.0.0-workswarm.zip`，启用后应显示「家庭文档台账」、版本1.0.0、1个技能和3个工具。市场包装ZIP与原生测试ZIP内层载荷相同。

## 工具与顺序

| 工具 | 用法 |
|---|---|
| `manage_family_registry` | `status`只读返回修订和完整记录；`inspect`检查`catalog_path`，返回完整元数据、文件状态及`preview_sha256`；用户确认后用相同摘要及`expected_revision`执行`init/update`，并传`confirmed=true`。 |
| `inspect_family_documents` | 提供`reference_date`（YYYY-MM-DD），可选`horizon_months`（默认6）、`person_id`或中文`kind`；只读核对持续台账和实际文件摘要。 |
| `prepare_family_document_pack` | `plan_path`、`output_dir`均为工作目录内完整绝对路径；默认`mode=preview`只读；用户确认完整计划及待确认项后用实际`expected_revision`、`expected_preview_sha256`和`confirmed=true`执行`mode=build`。 |

`workspace`必须为已存在的真实绝对目录；不接受符号链接或`.`/`..`。所有用户输入和输出须位于该目录，不能选择内部`.family-document-registry`。不擅自从文件内容、其他聊天或目录推断授权。

`init`使用`expected_revision=0`；更新先读当前修订。失败后停止说明，不自动换用新修订或摘要。登记更新保留所有旧人员/文档ID，不能删行；历史文档可显式设为`archived`。已有文档ID不能改换人员、类型、国家身份。新文档用新的ID，并由用户明确填`replaces`；不会自行归档旧件或判断替换件合法。

## 数据格式

完整示例在 `examples/`。人员为`{"id":"p_lin","name":"林晨（虚构）"}`。台账顶层固定为`schema_version=1`、`people`数组和`documents`数组。每份文档完整字段为：

```json
{"id":"passport_new","person_id":"p_lin","kind":"护照","country":"示例地区","path":"资料/林晨-新护照.txt","issued_on":"2026-10-01","expires_on":"2027-03-31","status":"active","replaces":null}
```

`path`为工作目录内相对路径或`null`（未关联附件）；文件缺失可以登记，但不伪称存在。`issued_on/expires_on`接受完整日期、仅月份或`null`。`null`表示未知，不代表永久有效；月份精度始终需要人工核对，不能猜月初/月底。非法日期、重复JSON键、未知字段、重复ID、跨人/跨类型/跨国家替换和替换环均拒绝。状态为`active`（在用）、`renewing`（续办中）或`archived`（历史归档）。

按用户给出的参考日计算：完整到期日早于参考日为`expired`；等于为`expires_today`，按日期包含当天；提醒边界包含当天。`unknown/month_precision`表示未知/仅月份。`beyond_horizon`仅表示晚于提醒边界，不证明法律效力。报告同时返回登记状态、明确`replaced_by`及文件`present/missing/unattached/changed`状态。

材料计划顶层固定为`schema_version=1`、`reference_date`和`requirements`。每项固定`id/person_id/label/document_id`，可选用户明确指定的`min_validity_months`（参考日之后至少有效的月数）和`max_age_months`（签发距参考日的最长月数）。缺失项用`document_id=null`。参见完整/待确认两个计划。精确月份计算只在目标月末需要时截断，如2026-10-31减1月为2026-09-30。

副本按计划顺序和ID命名，保留常见扩展名；不识别、转换、合并或执行内容。`checklist.md`为中文；`manifest.json`记录每份源路径、SHA-256、字节数、实际预览摘要、修订及待确认项。`complete=true`仅表示满足本次显式声明的机械条件；不表示机构受理、法律资格或文档真实性。经用户明确确认可以生成带待确认项的副本，但仍返回`complete=false`。

## 状态、错误与限制

所有业务结果含`version=1.0.0`和`ok`；`ok=true`仅表示工具操作成功。`writes_performed=false`为只读，不等于有效期或材料已通过。

- 常见错误：`confirmation_required`（缺少明确确认）、`preview_changed`（预览已变）、`revision_conflict`（旧修订）、`source_changed/source_missing`（文件变化/缺失）、`output_exists`（旧输出不能覆盖）、`invalid_date/duplicate_json_key/invalid_schema`（输入结构）、`unsafe_path/unsafe_file/filesystem_error`（路径/链接/权限）、`integrity_mismatch/invalid_registry`（台账异常）。
- 写入有权限限制的本地`.family-document-registry`，文件0600/目录0700，保存最多64次修订；头文件原子替换，历史不自动清理。并发冲突返回`registry_busy/revision_conflict`。同一操作系统用户的恶意篡改不在防御保证内；SHA-256是字节一致性，不认证来源。
- 最多32人、128份文档、32项材料；JSON512KiB，单文件8MiB、总64MiB，路径深度12、相对路径512字符。仅普通文件，不接受软/硬链接、设备或FIFO。源文件应保持稳定；不提供文件系统原子快照。
- 输出目录排他新建，不覆盖既有空目录。复制时目录可能暂未完成；`manifest.json`最后写入。`partial_output`表示本次新目录未完成，保留供人工检查；不自动删除现场、原件或旧材料包。断电/进程强制终止也可能留下未完成输出或未提交历史。
- 姓名、路径、日期等元数据明文存储；无加密、自动脱敏、OCR、正文提取、自动文件整理、归档/删除、提醒后台、网络服务或法律规则。文件只按字节读取核对摘要。未知/月份精度的日期不能替代精确日；本版没有“永久有效”推断。

## 无模型命令行

在内层目录运行`python3 -B runtime/registry.py --help`。子命令`manage/report/pack`与原生工具对应，`--input-json`提供JSON参数文本。退出码0为操作成功，2为拒绝或失败。帮助、说明、错误和清单默认简体中文；保留技术字段与原许可文本。

来源、原作者、固定版本和修改见`THIRD_PARTY_NOTICES.md`；完整上游MIT在`licenses/document-vault/LICENSE`。
