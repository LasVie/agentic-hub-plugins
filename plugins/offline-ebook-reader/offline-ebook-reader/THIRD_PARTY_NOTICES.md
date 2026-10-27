# 第三方来源与修改说明

- 来源：[xrn1997/dsh-novel](https://github.com/xrn1997/dsh-novel)，版本0.8.1，固定提交 `f9a19f5fbd2d76ef5e970c2333a67f9dcb66b31c`。
- 原声明：`Copyright 2026 xrn1997`；Apache License, Version 2.0。完整未改动原文见 `licenses/dsh-novel/LICENSE`。固定来源树没有NOTICE文件，未编造上游NOTICE。
- 实际适配：`src/services/localbooks.ts`的显式本地书副本、标题行切章流程，`src/services/shelf.ts`的书架与章/比例进度模型，`src/client/progress.ts`以同一章节高度保存/恢复比例的计算；参考 `src/services/epub/` 的spine顺序、格式边界与拒绝行为。
- 改动日期2026-10-27，Cai Zhenze：`runtime/ebook.py`改为Python标准库、受限TXT/EPUB纯文本、严格输入/归档/XML上限、完整性及私有事务状态、工具和回环服务；`assets/app.js`改为无依赖中文浏览器界面与revision冲突检测。两处含显著修改声明；README和Skill为本次中文适配说明。
- 未搬入：DSH/Cordis/React宿主、九项npm运行依赖及其实现、在线legado书源/兼容快照、网络抓取/登录、截图、图标、字体、书籍和媒体。这里不授予第三方书籍/书源/商标权利，不表示官方背书。
- 工具包装、UI HTML/CSS和测试由本次适配编写；本文件不替仓库自有材料选择统一许可证。发行前逐文件复核和来源记录在外层SOURCE_REVIEW.md/provenance.json。
