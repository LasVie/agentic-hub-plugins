# 手绘交互工坊 1.0.0 测试记录

任务 AH-20261027-anidoodle；候选 CAND-CLD-335；负责人 Gan Mingrui；日期 2026-10-27。

## 已执行

- Windows；Node 24.22.0；esbuild 0.25.12；实际 JiuwenSwarm .venv / openJiuwen SDK；本机 Edge headless。
- 源码版 9 项 Python 测试通过：中文输出及许可保留、HTML 注入转义、不覆盖已有作品、路径与保留名拒绝、非法输入、长度与场景校验、源码导出、范围声明，以及真实宿主 manifest 加载和工具执行。
- 真实 SDK 在 loader 解析一个 Skill 和一个 Tool 后执行 6 次操作：list、3 场景 create、source、stream。没有模拟 SDK。
- 三个场景的浏览器检查通过：实际挂载、同一渲染器下重放画面一致、鼠标与键盘按钮、表单错误/遮眼/偷看/成功状态、滚动事件、PNG 下载、390px 和 1280px 无横向溢出、减少动态效果下静止。运行中无页面异常、无外部请求。
- 人工式视觉检查已查看实际生成的三张页面截图，中文和角色正常显示。截图由开发自测产生，不替代用户验收截图。
- 上游 emit-interactive 的静态自包含检查通过，但其 Windows 浏览器检测不足；本插件普通生成使用预编译 JS，不依赖该检测器，也无需运行 npm。

命令：宿主 Python `-m unittest discover -s plugins/anidoodle/tests -v`；Node `plugins/anidoodle/tests/browser.mjs <作品目录> <证据目录>`。开发测试依赖通过 ANIDOODLE_PLAYWRIGHT_URL 指定，浏览器可通过 ANIDOODLE_BROWSER 指定。

## 解包与交付

`tests/release_audit.py` 已实际执行：最终解包版 9 项测试通过，含 6 次真实 SDK 操作。23 个 payload 文件与源码及原生导入 ZIP 逐字节相同，重复打包结果一致，测试未改变 payload。导出的源码工程重新编译后 art.js 字节一致。浏览器已测试 HTML 与最终解包版生成 HTML 字节一致，无需用旧截图替代不同版本。

| 文件 | SHA-256 |
| --- | --- |
| marketplace ZIP | `3c65b279a759f26bdd7266a03d0e32380d141475f2acb8192e1a704899e7a172` |
| 本机原生导入 ZIP | `bf300d24813c64fb920af004afd9443ccdea711b2bc44125f9697a5031d556cf` |

本机测试包：工作区 `plugin-builds/anidoodle/1.0.0/anidoodle-1.0.0-native.zip`。规范包：仓库 `releases/agent-plugin/anidoodle/1.0.0/anidoodle-1.0.0.zip`。原生包 manifest 位于 ZIP 根；规范包带 Hub marketplace 外层。两者只有容器布局不同。自测截图与 PNG 位于工作区 `plugin-builds/anidoodle/1.0.0/self-test-evidence/`；用户演示作品位于同级 `previews/`。

首版范围为三个可改编的铅笔水彩交互场景和选定绘图源码；不宣称完整 32 画风、配乐、MP4 或任意提示词生成新角色。PNG 是当前画布；源码改编需要本地 Node/npm 编译。未验证跨浏览器逐像素一致性、真实手机或长时负载。

## 2026-10-27 网页端补测

用户反馈“我测的差不多”并要求补测，尚未明确确认当前版本测试完成。通过 Computer Use 操作用户现有 Chrome 中的 JiuwenSwarm（localhost:5173，会话 web_1a17c4aea8a_0d1926480db7），输入补测请求并展开原始工具调用记录核验：

- `anidoodle_art` 共 7 次实际调用：list 返回三个中文场景；mascot、form、scroll 分别生成 browser-test-*.html；重复 mascot 文件名返回拒绝覆盖；`../escape` 在文件名校验阶段被拒绝；source 成功导出 browser-test-source-source。
- 发送文件工具返回成功发送三个文件，聊天界面实际出现三个 HTML 附件卡片。未把“工具返回成功”单独当作附件可见的证明。
- 两张原始 Chrome 截图保存于工作区 `plugin-builds/anidoodle/1.0.0/browser-evidence/01-no-overwrite.jpg`、`02-three-attachments.jpg`，分别展示拒绝覆盖的参数/返回和三个交付卡片。这是代理补测截图，不冒充用户提供的交互截图。
- 浏览器控制工具禁止访问 `file://`，本轮未重测下载 HTML 内的指针、表单、滚动及 PNG 按钮，也未通过其他方式绕过该限制。上文已有的 headless 交互结果属于上一轮自测。用户另行生成的水墨山水是源码改编作品，不是首版新增内置场景。
- 本轮确认已安装工具可供模型实际调用；没有重演 ZIP 导入流程，也没有独立核对已安装目录与 ZIP 的逐文件哈希。源码 payload、版本及两个交付 ZIP 均未改变。

## 2026-10-27 用户原始截图归档

用户在当前对话指定 `C:\Users\Gary\Pictures\Screenshots`，已逐张查看并归档本次 16:16–16:18 的 12 张 PNG：表单 3 张（初始、密码掩码/遮眼、显示演示密码/偷看），滚动绘画 5 张（入口、结构、线稿、水彩、完整插画），角色互动 4 张（初始、视线变化、抬手、欢呼）。页面标题与网页端补测生成的三个验收页面一致；部分头部直接显示版本 1.0.0。

原图已复制到工作区 `plugin-builds/anidoodle/1.0.0/user-test-evidence/2026-10-27/`，按 `01-form`、`02-scroll`、`03-mascot` 分类。README.md 提供逐图说明和 PR 建议；inventory.json 记录来源文件名、尺寸、字节数、SHA-256 与 ZIP 关联信息。12 张共 12,267,077 字节，复制后逐字节核验一致；未裁剪、压缩或改图，原始目录保留。三张右下角含系统截图通知，已标注，主要交互状态仍可辨认。

这批用户截图补充了实际可见交互状态；不能单独证明 PNG 下载成功、表单成功提交、键盘操作及连续鼠标跟随全过程，也不替代精确 ZIP 身份核验或明确测试完成确认。未见真实账户凭据或其他明显敏感内容，明文 1234 位于明确标注的演示密码框。

用户原始截图已收到并完成本地整理。

## 用户测试完成确认

2026-10-27，Gan Mingrui 在当前对话回复“确认”，明确回答了“手绘交互工坊 1.0.0 已测试完成、没有阻塞问题，可以进入提交阶段吗？”；记录时间为 16:29:48（UTC+8，记录时间而非精确消息时间）。确认覆盖上列原生及规范 ZIP 哈希，未改动 payload。确认追加到 RPT-20261027-anidoodle-ready-100，进入 Submitting；Project Lead 验收仍单独待处理。提交前再次运行源码版 9 项测试通过（11.304 秒），并核对 23 个 payload 文件、两个 ZIP 与 12 张原始截图。
