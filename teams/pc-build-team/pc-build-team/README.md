# 装机专家团 0.2.1

按预算和用途配一台电脑：Leader 问清需求，配件选型师选出主方案、省钱版和性能版，兼容与电源工程师逐条校验，装机指导写出步骤，最后导出一份中英双语 PDF。

## 使用方法

1. 在“专家”页的专家团中上传本 ZIP 导入。
2. 新建会话，切换到**集群模式**，在输入框旁选择“装机专家团”（专家团只能在首次创建 Team 时选择）。
3. 说明预算、用途和 PDF 保存路径，例如：“预算 6000 元人民币，2K 游戏，PDF 保存到 /mnt/c/Users/你的用户名/Downloads/my-pc.pdf”。

## 成员与工具

- `leader`（装机总顾问）：需求确认、分派、验收、导出。
- `parts_researcher`（配件选型师）：三套方案的型号、规格、价格、链接与核价日期。
- `compat_engineer`（兼容与电源工程师）：用 `build_checker` 校验并推动修正。
- `assembly_guide`（装机指导）：装机步骤、BIOS、首次开机检查、风险点。

所有成员都带有 `build_checker` 工具和 `PcBuildRail` 提示词规则。

### build_checker

- `validate`：检查插槽、内存类型与数量、主板版型、显卡长度、散热器高度与插槽、冷排位、M.2 数量、电源功率与接口、电源版型、核显、价格时效（7 天）、币种和预算。传入 `user_budget` 时，所有方案都按用户预算检查，方案自填的 budget 会被替换；`export` 必须带 `user_budget`。结果分为通过、注意、失败、未知。
- `export`：所有方案没有失败时，把团队写的中英双语 Markdown 报告（`markdown_path`）转成 A4 PDF。正文里单独一行的占位符（如 `{{parts:main}}`、`{{power_chart}}`、`{{board_map}}`）会换成由校验数据生成的表格和图；没放的必备项附在文末。Markdown 里的 HTML 不会执行。`output_path` 必须是绝对 .pdf 路径，不覆盖已有文件。

## 运行环境

- WorkSwarm 原生 Python 工具 SDK；依赖 `pydantic` 和 `markdown-it-py`（宿主均已有）。
- PDF 渲染优先使用 Chrome / Chromium / Edge 无头模式（可用环境变量 `PC_BUILD_CHROME` 指定路径），否则回退到 LibreOffice（`soffice`），版式效果较差。
- 需要中文字体（如 Noto Sans CJK SC 或微软雅黑）。
- 联网搜索与网页抓取使用宿主提供的工具；`build_checker` 本身不联网。

## 限制

- 兼容性检查基于成员提交的规格，不能替代厂商兼容列表；功耗为按额定值估算。
- 价格是核价日期的快照，不保证库存或最低价。
- 主板示意图按版型绘制标准布局，非实物比例；机箱侧视图按实测尺寸绘制。
- 不包含商品图片（版权原因），配件以链接给出。
- 不代用户下单或付款。
