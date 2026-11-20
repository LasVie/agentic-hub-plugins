---
name: order-matching
description: 基于登记核对明确引用及双向唯一的无引用候选
---

接收梳理员实际 register.json，运行：

`python3 -B <脚本> match --register <register.json> --out <全新匹配目录>`

明确订单引用可合计多笔扣款，退款只关联相符的退款单号。无订单号扣款要求商户及币种完全相同、金额等于实付应扣、七天内、双向唯一且无明确扣款引用占用。不得把同额多候选硬配；报告原流水、订单引用和金额。将 matches.json 与真实回执交给主理人。
