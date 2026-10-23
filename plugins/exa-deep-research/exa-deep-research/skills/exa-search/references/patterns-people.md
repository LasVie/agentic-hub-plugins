<!-- Adapted for native openJiuwen tools from Exa 3.4.2; see THIRD_PARTY_NOTICES.md. -->
# 查询模式：人物

`category:people` 可能偏向 LinkedIn 资料。发现查询需包含明确公司、职位、时间或地区，避免把“研究员 创始人 CEO 初创公司”等模糊组合当作有效筛选。

```json
{"query":"category:people OpenAI 工程师","numResults":10}
```
```json
{"query":"category:people Cursor 副总裁 总监","numResults":10}
```
```json
{"query":"category:people 旧金山 B2B SaaS 初创公司 增长负责人","numResults":12}
```
```json
{"query":"category:people Jane Smith Anthropic 机器学习","numResults":5}
```

需要公司覆盖时，分别检索工程、产品设计、销售市场等部门及资历，每个查询先请求 10 条；只有宿主支持且已授权时才并行执行。

补充公司官方团队页、个人主页和入职公告等非 LinkedIn 来源；“近期”必须先转换为日期范围。优先按规范化 LinkedIn URL 去重，没有时按姓名加当前公司去重。核实资料时效，不把同名人物合并。
