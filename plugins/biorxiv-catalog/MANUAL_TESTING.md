# 预印本目录助手 1.0.0 — WorkSwarm 中文测试

导入 `test-packages/biorxiv-catalog-1.0.0-native.zip`，开启“预印本目录助手”，新建对话。一次发送一条提示；展开真实工具名、参数和结果，并保留原始 PNG/JPEG 截图。工具卡必须以 `biorxiv_` 开头。未执行工具的文字回答不算通过。

## 1. 分类与工具可见性

```text
调用 biorxiv_get_categories，参数 {}。
必须实际使用插件工具，用中文列出服务返回的学科，保留英文 API 分类值。
工具不可用时如实说明，不用网页搜索或已有知识替代，也不要自动重试。
```

预期：`ok:true`，实际分类中有 `bioinformatics`，并展示来源、服务版本和获取时间。不是检测 Claude/前端页面上的分类。

## 2. 中文参数与目录查询

```text
调用 biorxiv_search_preprints，直接传入：
{"date_from":"2024-01-01","date_to":"2024-01-07","category":"生物信息学","server":"生物预印本","limit":2}

用中文整理实际返回的两条题名、作者、DOI、日期和版本。保留 source、server_version、retrieved_at_utc。
如果 total 与实际条数不一致，原样说明矛盾；不要据 total=0 说没有结果。不得自行补论文或重试。
```

预期：中文别名映射为 bioinformatics/biorxiv，返回不超过两条符合日期的真实记录。当前已验证第一条 DOI 为 `10.1101/2023.12.30.573742`；如果服务变更，按实际结果报告。已观察到源 `total:0` 与两条结果并存，警告必须保留。

## 3. 用实际 DOI 读取元数据

```text
使用上一步第一篇实际返回的 DOI 调用 biorxiv_get_preprint，server 设置为 biorxiv。
用中文解释实际题名、作者、版本、日期、摘要要点、license 和发表关联。
未提供的字段写“未提供”，保留来源，不把预印本说成已证明的结论；不要另找或猜一个 DOI。
```

预期：实际 DOI 与上一轮一致，保留 version/license；期刊等未知字段不能编造。

## 4. 发表关联

```text
调用 biorxiv_search_published_preprints，参数：
{"date_from":"2024-01-01","date_to":"2024-01-07","include_details":false,"limit":2}

用中文列出真实预印本 DOI、发表 DOI、发表日期和期刊。区分预印本日期与发表日期；空值写“未提供”，不能自动补作者或期刊名。
```

预期：成功响应中保留实际 DOI 对与发表日期；服务的 journal/author 字段可能为 null，不得猜测。

## 5. 资助机构

```text
调用 biorxiv_search_by_funder，原样传入：
{"funder_ror_id":"00k4n6c32","date_from":"2025-04-10","date_to":"2025-07-10","limit":1}

用中文说明实际返回的题名、DOI、日期和资助查询条件。该 ROR 取自官方 API 示例；返回中没有机构全名、基金编号或资助金额时，不得补写。不要自动换 ID 或重试。
```

预期：实际执行请求；当前已返回一条符合日期的记录。未知的资助明细仍保持未知，不能据目录过滤断言完整资助历史。

## 6. 内容与使用统计

```text
先调用 biorxiv_get_content_statistics，参数 {"interval":"月度"}。
再调用 biorxiv_get_usage_statistics，参数 {"interval":"monthly"}。

用中文概述实际返回字段，区分新投稿与修订、全文浏览与 PDF 下载。
只列前两条示例并标明来源期间。缺少月份、年份或摘要浏览数时如实写未提供，不要按数组位置补日期，不把缺失当零，也不推断独立读者或论文质量。
```

预期：两个工具均实际调用；保留原始统计和警告。年度响应已观察到期间空值，月度也应按实际字段核对；字段缺失的正确披露属于此测试要求。

## 7. medRxiv 平台

```text
调用 biorxiv_search_preprints，参数：
{"date_from":"2024-01-01","date_to":"2024-01-07","server":"medrxiv","limit":1}

用中文列出实际题名、DOI、日期和版本，标明来源为 medRxiv。不要添加未经工具支持的分类；不要用 bioRxiv 的结果冒充。
```

预期：medRxiv 查询本身成功并返回实际记录，或如实说明源没有结果/失败。空结果不等于访问失败。

## 8. 预期参数拒绝（这个错误才算通过）

```text
仅测试参数拒绝。调用 biorxiv_search_preprints，一次且原样传入：
{"date_from":"2024-01-08","date_to":"2024-01-01","limit":2}

展示实际错误代码和中文提示。不得交换日期、改参数、更换工具或重试。
```

预期：`ok:false`，`error.code=INVALID_ARGUMENTS`，中文提示“开始日期不能晚于结束日期”。此输入应在联网前拒绝；前端即使显示工具错误，也不代表该拒绝测试失败。

## 完成后

请确认测试的是当前 1.0.0 ZIP，并发送能看清工具名、参数及实际结果的原始截图。明确说明测试完成及任何失败/未测项。源服务和数据可变化；不能把超时、HTTP401/403/429或 CONNECTION_FAILED 当作零结果或测试通过。用户测试确认前保持本地 Build，不推送或创建交付 PR。
