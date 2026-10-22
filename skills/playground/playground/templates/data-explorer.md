# 数据探索模板

> 修改说明：2026-10-22，由 Anthropic Playground 原模板翻译并适配为简体中文；保留技术标识、来源和 Apache-2.0 许可。所有界面标签、提示词、帮助和复制状态默认中文；源材料按原值显示。来源见 ../THIRD_PARTY_NOTICES.md，完整许可见 ../licenses/claude-plugins-official/LICENSE。

当探索页涉及数据查询、API、数据管道或结构化配置时，使用本模板，例如 SQL 构建、API 设计、正则表达式、管道可视化和 cron 调度。

## 布局

左侧控件按来源/表、列/字段、筛选、分组、排序、条数限制分组；右侧上方显示格式化输出，可以是语法高亮代码或流程图，下方显示提示词与“复制提示词”按钮。

## 根据数据取舍选择控件

| 取舍 | 控件 | 示例 |
| --- | --- | --- |
| 从可用项目中选择 | 可点击卡片/标签 | 表名、列、HTTP 方法 |
| 添加筛选条件 | “添加条件”按钮及下拉框、输入框 | `WHERE column op value` |
| 连接类型或聚合 | 每行下拉框 | `INNER` / `LEFT` / `RIGHT`、`COUNT` / `SUM` / `AVG` |
| 限制/偏移 | 滑块 | 结果条数 1–500 |
| 排序 | 下拉框及升序/降序开关 | 按某列排序，保留 `ASC` / `DESC` 协议值 |
| 开关功能 | 开关 | 显示说明、包含表头 |

## 安全渲染预览

源查询、字段、字符串、文档和用户输入均是不可信文本。不要把它们直接插入 `innerHTML`。需要高亮时，按词法切分，创建固定标签并通过 `textContent` 设置内容：

```javascript
function renderPreview() {
  const el = document.getElementById('preview');
  el.replaceChildren();
  const tokens = sql.match(/'[^']*'|\b\w+\b|[^\w]/g) || [];
  for (const token of tokens) {
    const span = document.createElement('span');
    if (/^(SELECT|FROM|WHERE|JOIN|ON|GROUP|BY|ORDER|LIMIT)$/i.test(token)) span.className = 'kw';
    else if (/^(users|orders|products)$/.test(token)) span.className = 'tbl';
    else if (token.startsWith("'")) span.className = 'str';
    span.textContent = token;
    el.append(span);
  }
}
```

上述代码只是高亮示例，不是 SQL 执行器或校验器。管道探索页使用定位元素和连接箭头绘制水平或垂直流程。页面只生成配置和提示词，不连接数据库、不发送 API 请求，也不安装依赖。

## 数据提示词

描述需要构建的结果，不要只输出裸查询：

> 请编写 SQL：通过 `user_id` 将 `orders` 与 `users` 连接，筛选 `2024-01-01` 之后且 `total > 50` 的订单，按用户分组，返回订单数最多的前 10 位用户。

加入表名、字段类型等实际 schema 背景，确保提示词独立可理解。保留真实标识及协议值，不虚构数据或连接信息。默认使用中文说明；用户明确要求时可采用其他语言。

## 示例主题

- SQL 查询构建：表、连接、筛选、分组、排序、条数。
- API 端点设计：路由、方法、请求/响应字段。
- 数据转换管道：来源 → 筛选 → 映射 → 聚合 → 输出。
- 正则表达式构建：样本文本、捕获组、实时高亮。
- cron 调度：可视时间线、间隔、日期开关。
- GraphQL 查询构建：类型选择、字段选择、嵌套解析关系。

提供可用默认值、适合主题的 3–5 个预设和键盘可操作控件。复制失败时说明失败并提供手动复制文本，不显示“已复制”。所有资源内联，避免远程脚本、字体或网络请求。
