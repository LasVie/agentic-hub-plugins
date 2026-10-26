# 域名续费比价 1.0.0 — WorkSwarm 用户测试

负责人 Nguyen Trung Dung；任务 AH-20261026-domain-renewal-research。
原生 ZIP：test-packages/domain-renewal-research-1.0.0-native.zip。
原生 SHA-256：`af6ef3967d0dcb88739abf6bf0df5e88e4eb39f98477b536386d0e93159b0d26`。
外层 SHA-256：`532fefbc5aa7a94fa08ad76270ad9d491e8f4ffe7fac12713a3e4b1c6945a82c`。

本机可直接导入的绝对路径：
`D:\jiuwen_repos\agentic-hub-plugins-domain-renewal-research\plugins\domain-renewal-research\test-packages\domain-renewal-research-1.0.0-native.zip`。

导入 native ZIP，启用 **域名续费比价**，新建会话。
参数直接给工具，不套 arguments。此次基本测试不需要账户、密钥、Radar 或额外模型账户。

## 1. 原生工具与中文入口

提示：

> 显示当前可用的 domain_ 工具。然后调用 domain_get_registrars，用中文说明覆盖来源及其健康状态。
> 必须实际调用插件工具，不能用通用网页搜索替代；工具不可用时如实说明。

预期：插件名称中文；工具清单有 12 个 domain_ 工具；出现实际工具调用和注册商来源/状态。
不能只根据模型自述的工具名单判定通过。请展开至少一个原始工具结果截图。

## 2. 续费预算比较

提示：

> 调用 domain_search_prices，参数为 {"q":".com,.org,.dev","sort":"renewal","maxRenewalCents":1500,"limit":3}。
> 用中文列出实际报价的后缀、注册商、首年注册费、年度续费、获取时间和比较链接。
> 保留部分覆盖、样本和税费限定；不要检查任何具体名称，不得用记忆补全。

预期：实际调用，最多三条已返回报价，年度续费按美元分换算，注册费分列；日期/链接真实。
服务返回缺口或错误时原样说明，不保证三个后缀总有合格报价。

## 3. 估算

提示：

> 从刚才返回的实际注册商中选择一个，为它覆盖的后缀调用 domain_estimate_cost，years=3。
> 解释这是新注册的估算，保留分项和来源；未知总价不能写成零。

预期：工具实际返回、中文说明、分项和日期；不声称这是已有域名账单或未来价格保证。

## 4. 缓存可注册性与未知值

提示：

> 调用 domain_check_availability_batch，原样使用 {"name":"example","tlds":"com,org","cachedOnly":true}。
> 用中文区分有证据的状态和未知；不要触发真实检查、自动刷新或重试。

预期：工具实际调用；缓存缺失明确为未知，不得据此声称可注册或已被注册。

## 5. 中文输入与拒绝额外私密参数

提示：

> 仅做本地参数拒绝测试：调用 domain_check_availability，参数 {"name":"中文测试","tld":"com"}。
> 显示中文错误代码/提示，不改成拼音、不要重新调用或发送其他名称。

预期：INVALID_ARGUMENTS 和中文提示，联网前拒绝此输入，无伪造可注册性。

## 6. 可选命名表单

提示：

> 调用 domain_open_name_finder，用中文给出命名表单入口和当前宿主支持情况，不执行名称检查。

预期：说明和公开网页链接。没有内嵌 App 时使用链接是已声明行为，不能声称已经打开或渲染表单。

## 完成后提供

请明确确认 **域名续费比价 1.0.0**、原生 ZIP SHA-256 的测试完成情况，说明任何失败步骤。
提供原始 PNG/JPEG：启用面板、展开的实际工具结果、续费比较、缓存未知/中文错误等关键流程。
截图中的价格本身会变化，重点是实际调用、来源日期和限定被保留。
不需要进行 Hub 提交或提供 Hub 截图。当前测试包与代码留在本地，待本版本确认及原始证据齐备后再进入提交阶段。
