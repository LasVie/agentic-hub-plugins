<!-- Adapted for native openJiuwen tools from Exa 3.4.2; see THIRD_PARTY_NOTICES.md. -->
# 使用 Exa 搜索

普通检索使用 `exa_search`（`query`、`numResults`）和 `exa_fetch`（已知 URL 的正文）。确需域名、日期等条件时，使用 `exa_search_advanced` 并在 `arguments` 中传入符合当前远端模式的字段。

## 语义查询

Exa 按语义相似性发现页面，不能把相似度当作用户条件已经满足的证明。自然语言查询描述希望找到的页面，不依赖布尔运算符或引号强制精确匹配。

| 目标 | 简短但不足的查询 | 更具体的查询 |
| --- | --- | --- |
| 某主题的实践文章 | “主题 X” | “实践者撰写的主题 X 详细经验文章，包含具体实现与结果” |
| 提供某类产品的公司 | “Y 公司” | “category:company 为企业开发 Y 产品的初创公司” |
| 公司中的特定职位 | “公司员工” | “category:people Acme 公司的资深工程师” |

使用通顺的自然语言描述。精确实体先用 `numResults=5`；窄类别与约束用 10；宽范围探索用 15。最多为 25；扩大覆盖时执行多角度的 10–15 条查询，不请求 50 条。

可使用上游参考中的类别提示 `category:company`、`category:publication`、`category:news`、`category:personal site`、`category:people`。提示不等于已核验的硬筛选；真正的结构化筛选应根据高级工具返回的模式设置，再核验结果。

```json
{"query":"category:publication 长上下文稀疏注意力机制","numResults":10}
```

## 多角度与时间

多个查询应覆盖不同立场、实践场景或证据类型，不只替换近义词。词序也可能影响结果，可尝试 2–3 种表述；并行执行须符合宿主真实能力和授权。

遇到“上周”“最近”“本月”，先按当前用户时区计算日期边界，再写入查询或合适的结构化日期筛选；不要照搬例子年份或凭感觉估算时间。

避免只有 1–2 个词的模糊查询。不要把 AND/NOT 当作必然生效的运算符，也不要把引号当作精确匹配保证。

## 无结果与领域模式

没有结果或只有无关结果时，先写得更具体，再更换角度。多个角度仍无结果时，如实说明公开资料覆盖有限，不编造来源。

按任务阅读同目录参考，通常选择 1–2 份：

| 文件 | 领域 |
| --- | --- |
| `patterns-people.md` | 职位、公司、地点等人物查询 |
| `patterns-companies.md` | 公司类别、阶段、竞品、融资 |
| `patterns-papers.md` | 学术论文与综述 |
| `patterns-relationships.md` | 客户、协作等关系线索 |
| `patterns-code.md` | 代码、API、文档与错误 |
| `patterns-news.md` | 新闻、近期事件与反应 |

## 阅读与核验

先检查标题和摘要，移除无关结果；对有价值且摘要不足的来源调用 `exa_fetch`。抓取失败时，可使用其他已授权、真实可用的读取工具并说明工具来源；仍失败就保留其余证据并披露缺口。

```json
{"urls":["https://example.com/official-document"],"maxCharacters":10000}
```

默认以中文解释检索结果；保留来源语言、URL 和引用准确性。
