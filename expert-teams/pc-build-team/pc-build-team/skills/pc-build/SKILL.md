---
name: pc-build
description: 按预算和用途规划一台电脑：问清需求、分配预算、选主方案和两个备选方案、用 build_checker 校验兼容性与电源余量、写装机指南，最后导出一份中英双语 PDF。
---

# 装机规范

1. **需求**：预算与币种、地区或商店、用途、尺寸与噪音、已有配件、外观、PDF 保存路径。
2. **预算分配**：游戏约 35%–45% 给显卡；剪辑与 AI 侧重处理器、内存和显存；办公优先核显、安静和小体积。
3. **选型**：主方案 main，以及省钱版 budget 和性能版 performance。每个配件写型号、单价、币种、商店、链接、核价日期和规格字段；查不到的规格留空。
4. **校验**：`build_checker` 的 `validate`，始终带上 `user_budget`（用户给出的预算），工具会用它检查每套方案，忽略方案里自填的 budget。fail 必须修正；unknown 需要补查规格；warn 要评估。价格超过 7 天视为过期，需要重新核价。
5. **装机指南**：步骤、BIOS 设置、首次开机检查、风险点、内存插槽和系统盘 M.2 插槽（用主板说明书上的名称，与 dimm_slot_names、m2_slot_names 一致，PDF 主板示意图据此高亮）。
6. **报告**：Leader 写一份中英双语 Markdown（`report.md`）。每段先中文、后英文（或按 language_order），含义一致；正文写结论、理由、备选方案说明、装机步骤、BIOS 设置、首次开机检查、风险点和资料来源链接。表格和图用单独一行的占位符插入，不要手写：

   ```
   # 标题 · Title
   {{kpis}}
   ## 一、方案摘要 · 1. Summary
   （双语正文）
   {{budget_chart}}
   ## 二、配件清单 · 2. Parts list
   {{parts:main}}
   ## 三、兼容性报告 · 3. Compatibility report
   {{compat}}
   {{power_chart}}
   {{clearance_chart}}
   {{case_fit}}
   ## 四、备选方案 · 4. Alternatives
   {{variants_chart}}
   （省钱版说明）
   {{parts:budget}}
   （性能版说明）
   {{parts:performance}}
   ## 五、装机指南 · 5. Assembly guide
   {{board_map}}
   1. 步骤…… / Step……
   ## 六、资料来源 · 6. Sources
   - 标题 — https://……
   ```

   Markdown 里的 HTML 不会生效；不要贴图片。每个步骤一两句，避免冗长。
7. **导出**：`build_checker` 的 `export`，传入三套 builds、`user_budget`、`markdown_path`、`ram_slots_to_use`、`m2_boot_slot`、language_order 和绝对 .pdf 路径。

builds 里的方案名称和备注用 `{"zh": "...", "en": "..."}`；报告正文用双语 Markdown。型号、规格、链接和数字不翻译。
