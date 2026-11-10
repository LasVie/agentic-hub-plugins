---
name: grant-proposal
description: 按资助方指南撰写基金申请书：拆解评审要点、调研文献与研究空白、设计技术路线与预算、模拟评审打分，并用 proposal_checker 校验要点覆盖、预算、篇幅与评分，最后交付申请书草稿与自评表。
---

# 基金申请书规范

## 1. 需求清单

资助方与项目类型、指南或评审细则原文、截止日期、预算上限与币种、篇幅限制、研究主题、已有成果与团队、保存路径。缺失项写入“假设与待补”。

## 2. 默认章节结构（资助方有模板时以模板为准）

| id | 章节 | 主要回应的要点 |
|---|---|---|
| S1 | 摘要 | 全部 |
| S2 | 立项依据（研究意义、国内外现状、研究空白） | 科学意义、创新性 |
| S3 | 研究目标与研究内容 | 创新性、可行性 |
| S4 | 研究方案与技术路线 | 可行性 |
| S5 | 特色与创新之处 | 创新性 |
| S6 | 年度计划与预期成果 | 可行性 |
| S7 | 研究基础与工作条件 | 研究基础 |
| S8 | 风险与应对 | 可行性 |
| S9 | 预算说明 | 经费合理性 |
| S10 | 参考文献 | — |

## 3. proposal_checker 输入格式

```json
{
  "action": "review",
  "criteria": [{"id": "C1", "text": "指南原文", "weight": 3, "mandatory": true}],
  "sections": [{"id": "S2", "title": "立项依据", "text": "章节正文全文",
                "evidence": [{"criterion_id": "C1", "quote": "逐字摘自正文的一句话"}]}],
  "budget": {"currency": "CNY", "total_cap": 300000, "stated_total": 298000,
             "category_caps": [{"category": "设备费", "max_ratio": 0.3}],
             "lines": [{"item": "GPU 服务器", "category": "设备费", "quantity": 1,
                        "unit_cost": 80000, "years": 1, "justification": "模型训练"}]},
  "limits": [{"section_id": "S1", "max_units": 400, "unit": "mixed"}, {"max_units": 30000}],
  "scores": [{"criterion_id": "C1", "score": 4, "max_score": 5, "rationale": "指向具体段落的理由"}],
  "weak_threshold": 0.6
}
```

- 单项检查：`criteria_map`、`budget`、`limits`、`score`，只需传对应字段。
- `review` 四项输入都要提供；缺任一项会列入 `skipped`，`ready_to_submit` 为 false。
- 引文必须逐字出现在该章节正文中（空白差异会被忽略），否则列入 `quotes_not_found`。
- `limits` 不写 `section_id` 表示全文限制；`mixed` 计数：每个汉字计 1，英文与数字按词计 1。资助方系统的计数方式可能不同，留出 5% 余量。

## 4. 写作要点

- 每个章节第一段就回答它对应的评审要点，不要把关键论点藏在后面。
- 创新点写成“相对于已有工作 X，本项目首次 / 首个……”，并有文献支撑。
- 研究目标、研究内容、技术路线、年度计划、预期成果五处要一一对应，编号一致。
- 预算每一行都能回答“这笔钱做哪项研究内容”。
- 前期基础只写用户提供的真实成果；缺少时如实写入待补清单。

## 5. 交付

`proposal.md`（正文）与 `self-review.md`（评分表、要点覆盖表、预算校验、篇幅统计、假设与待补清单）。
