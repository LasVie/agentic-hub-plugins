<!-- Adapted for native openJiuwen tools from Exa 3.4.2; see THIRD_PARTY_NOTICES.md. -->
# 查询模式：公司

使用 `category:company` 辅助发现公司资料，并核实融资、人数和业务描述。

```json
{"query":"category:company 旧金山 AI 基础设施 初创公司","numResults":10}
```
```json
{"query":"category:company B 轮 金融科技 支付","numResults":10}
```
```json
{"query":"category:company 与 Stripe 类似的公司","numResults":8}
```

竞品研究覆盖不同角度：与目标相似的公司、该类别软件工具、近期产品发布及融资公告。宽范围查询可用 15 条结果，随后核验具体产品与条件。

融资与投资方查询可组合“[公司] 融资轮次 金额 投资人”和“category:company [公司]”，各先请求 5 条。保留公告日期、币种、来源与不确定性，避免将公司概要当作最新融资事实。
