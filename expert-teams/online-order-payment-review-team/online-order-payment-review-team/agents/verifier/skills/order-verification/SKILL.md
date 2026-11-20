---
name: order-verification
description: 先建立独立基线，再检查逐笔去向、歧义与资金守恒
---

第一项任务只接收原始资料和截止日。运行：

`python3 -B <脚本> baseline --source <原始目录> --as-of <日期> --out <全新基线目录>`

回传真实基线、输入摘要和回执后，才接收匹配提案并运行：

`python3 -B <脚本> verify --source <原始目录> --as-of <日期> --baseline <baseline.json> --proposal <matches.json> --out <全新核验目录>`

复核每个涉及冲突的流水是否有明确证据，检查同一流水只用一次、逐币种原始金额等于分配与未分配之和。核验失败回报原流水、缺失事实或差异；核验一致交接 verification.json。不得通过改写提案来消除冲突。
