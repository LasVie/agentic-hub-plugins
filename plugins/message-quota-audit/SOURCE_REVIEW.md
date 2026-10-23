# 来源与查重审查

2026-10-23；成员Cai Zhenze；CAND-DSH-070；AH-20261023-message-quota-audit；repo:agent-plugin:message-quota-audit。
名称：deepsleepAquarium/dsh-whale-post#gate → 消息配额与用量审计 → message-quota-audit；版本1.0.1。

## 授权与实际材料

mode=ported，permission_status=verified。已阅读实际根/包MIT全文、代码/文档及完整递归包树。固定来源：https://github.com/deepsleepAquarium/dsh-whale-post/tree/d78a82699722f0da6ae3d2b4cbdbaa411f2f67af/packages/gate ，包0.6.1；该源码提交不同于历史npm gitHead，不声称二者归档相同。完整包树为README中英文、index.js、package.json、selftest.mjs、cordis.patch.yml、LICENSE；没有媒体、嵌套许可证或NOTICE。实现只导入Node内置fs/path/crypto，原Node>=20、无外部运行依赖。

- 根及包MIT：Copyright (c) 2026 The Tank；blob e1f13ed44dc24d9163850b294ce30d73de6743c0；SHA-256 8d5ee4ed2408d928530d0515bfa8f8d1976f468f355a19aaa7f71921c4dce08d。完整版权、许可条件、免责声明原字节保存于内层licenses/whale-post-gate/LICENSE。
- 实际改编：index.js中的回执正则、在线/离线单位计量、每日桶配额、同对窗口/回复深度与查账语义进入runtime/quota.py；README接口需求进入内层README.md。原JS头逐字保存于licenses/whale-post-gate/UPSTREAM_HEADER.txt，Python头保留来源、版权及修改提示。
- 修改：Python3.11/SQLite替代Node文件增量；事务内复核+写账、ID幂等/冲突拒绝、严格有界输入/私有目录、显式时区日界、损坏状态失败、中文工具/CLI/技能/说明。新增代码的统一许可由负责人决定，不擅自重许可。
- 无媒体/图标/字体/数据/二进制复制，无外部服务账号。SDK、Python、SQLite、系统时区仅依赖宿主，未重新打包。MIT不要求Apache修改声明；没有NOTICE，不伪造。
- 原实现已经接触且允许复用，诚实记录ported，不声称native或来源隔离。audit-upstream仅自动输出MIT-like/unknown，不能代替上述人工范围审查。

## 范围及差异

复用Phase1有效复核并在kickoff读取最新候选/任务/PR，未发现新冲突。625项账本中，上下文洞察72c01bbdeaee47c4ad9eeaa9d7ae630e/d0facc36f10c4f82b9592633a2dc0b11@1.0.3分析token/context；Discord桥接卫士04d23729393a4070a80dd38bc6ce1cab@1.0.0传输和访问控制；agent-team-orchestration b68e551f74ec46818b51492be6efb83c@e7bda4f是角色交接；PR41的代理信件完整性校验1.0.1是结构、摘要、HMAC和发件人许可。它们不维护本工具的消息配额/用量/对账。同仓来源本身不构成重复或新功能证明。

不移植费用、force、手机上限、群折算、generic bucketRules、注册钩子、总线或发送。原目录quiet-hours描述与固定源码不符，候选Notes已明确更正。此插件只处理用户声明，不证明真实投递、身份、授权或真实账单；不是安全或硬支出保证。用户/系统时间和同账户本地状态是信任前提。

## 分发复核

内层THIRD_PARTY_NOTICES.md列明逐路径覆盖及修改；完整MIT及原始头随包。源码、市场ZIP、原生ZIP及解包许可/路径/哈希检查结果见TEST_REPORT.md和package-verification.json。原生测试ZIP从已打包市场内层产生，不另改载荷。没有未解决的已知复制许可条件；最终包仍须实际检查。此记录不代表Hub审批或其他权利的自动豁免。用户手测、原始截图及负责人验收待后续阶段。

2026-10-23 Phase3复核：当前1.0.1的完整MIT/原始源文件头/第三方说明、源码与ZIP9文件哈希再次核对通过；用户完成确认及4幅原图已收到，见USER_TEST_CONFIRMATION.md与evidence/originals.json。原生/市场包未变；不把用户确认当作负责人验收。
