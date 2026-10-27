# 来源、范围与许可审查

- 候选：CAND-CLD-335；任务：AH-20261027-anidoodle；负责人：Gan Mingrui。
- 名称映射：anidoodle → 手绘交互工坊 → anidoodle。
- 2026-10-27 用户明确选择并授权认领、开始开发；在线候选 Planned，任务已登记。
- 上游：https://github.com/alexgreensh/anidoodle/tree/f746cbd8a7032463bd0bc88ee8ff852599193b8c 。插件 manifest 与 engine package.json 均为 0.9.6。以提交锁定，不依赖移动的 main。

## 查重与设计

保留 Partial Overlap - Extend Existing Capability。相关资产：remotion-video-toolkit 97557b537a2c47748fcc1df8ea328c5d@1.0.0；分镜预演册与本地预演视频交付 d67e926bf3c8426eb9dbf19c0b102ddd@1.0.0。2026-10-27 启动时复核实时开发任务及最近台账，未发现新的 anidoodle 认领。该插件以配套交互素材入口补充现有视频工作流，不复制通用视频/分镜管线。没有声称现有资产内部绝无相似原语。

首版聚焦三个可改编的铅笔水彩交互场景；保留上游核心源码，以本地编译的 JS 避免普通生成依赖 Node/npm。中文工具生成独立 HTML，用户在浏览器互动和导出 PNG；源码工程用于进一步创作。未将固定模板标题定制冒充任意图像生成。JiuwenSwarm 对话嵌入预览未保证。

## 复用审查

已阅读根目录完整 LICENSE、NOTICE，核对选定九个 TypeScript 文件的导入、文件头和用途；所选闭包没有第三方图片、字体、采样音色或外部服务调用。选定路径与原始/目标 SHA-256 逐项记录在 provenance.json。主体根目录 Apache-2.0 许可覆盖这些绘图与交互实现，未发现所选文件另设许可或不兼容声明，允许在履行条件后改编分发，mode=ported。

| 材料 | 覆盖与处理 |
| --- | --- |
| 9 个绘图与交互源码 | Apache-2.0；完整原文、版权及 NOTICE 随内层 payload 分发 |
| 中文标签、移除未使用 Film 适配 | 各修改文件首行含修改者、日期和说明；保留原源码注释 |
| 编译 JS 与生成 HTML | 从上述源码构建，保留完整 LICENSE、NOTICE 和改编声明；无外部库运行时依赖 |
| esbuild 0.25.12 | 仅构建，MIT 全文另附；不分发编译器及二进制 |
| Playwright / 浏览器 | 仅本地测试；不分发，也不要求普通用户安装 Playwright |
| 音色/图片/字体 | 未复制、未下载可选音色，故不将根 Apache 授权扩大到这些第三方材料 |

署名均保留 Alex Greenshpun，不把原绘图引擎归为团队独立原创。许可/NOTICE 哈希见 provenance.json。新增自有适配不擅自对整个团队仓库作统一授权决定。

## 交付检查

最终 1.0.0 内层共 23 个文件，264884 字节。规范 marketplace ZIP 与本机原生导入 ZIP 解包内容逐字节相同；许可证据路径/哈希核对通过。九个移植源码文件均对应同一固定提交；生成 art.js 和独立 HTML 内含完整 Apache LICENSE、NOTICE 与改编声明，源码导出保留这些文件。依赖编译器未进入 ZIP，测试缓存和研究素材未进入 payload。

中文页面、真实宿主 loader/工具和解包测试通过；源码导出后重新编译 art.js 的字节与随包文件一致。浏览器测试使用的 HTML 与最终解包版生成 HTML 字节一致，证据见 TEST_REPORT.md 和 test-evidence.json。随后已通过实际 JiuwenSwarm 网页对话核验工具调用和附件交付，并收到、查看和原样归档用户提供的 12 张交互截图。未重演导入流程；Gan Mingrui 已于 2026-10-27 在当前对话明确确认 1.0.0 测试完成、无阻塞并进入提交，关联 ZIP 哈希见 TEST_REPORT.md。以上仅针对选定复用范围，不构成全部上游功能已迁移的声明。
