# 测试报告 — 网页无障碍检查 1.0.0

Owner: Nguyen Trung Dung. Tested 2026-11-13, Asia/Singapore.
Task AH-20261113-a11y-enforcer; Candidate CAND-CLD-251.
Package under test: native ZIP `test-packages/a11y-enforcer-1.0.0-native.zip`（见文末的最终哈希记录）。

## 环境

- Windows 11 家庭中文版 10.0.26100；Python 3.11.9（虚拟环境 `D:/jiuwen_repos/outputs/pitwall-build/venv`）；openjiuwen 0.1.20.post1；pydantic 2.14.3。
- 没有调用任何模型（`model_calls: 0`）。没有在 WorkSwarm 前端里对话测试（`frontend_conversation: not performed`），那一步留给用户手工测试。

## 1. 自动测试（`tests/test_a11y_enforcer.py`）

命令（在仓库外的目录运行，避免 SDK 把 `logs/` 写进仓库）：
`python -B -X utf8 -m unittest discover -s <仓库>/plugins/a11y-enforcer/tests`
结果：**53 个测试，52 个通过，1 个跳过**（约 20 秒）。跳过的是“用真实符号链接测试遍历”——Windows 上没有权限创建符号链接；同一逻辑由 `test_symlink_logic_with_patched_islink` 用替换 `os.path.islink` 的方式覆盖，没有在真实符号链接上测过。测试对象是插件载荷里的真实文件 `a11y-enforcer/tools/a11y_enforcer.py`。覆盖：

| 类别 | 内容 |
| --- | --- |
| 20 条规则 | 每条规则的触发和不触发：html-lang、img-alt（含 `alt=""`、role=presentation、aria-hidden、展开属性、`Image`/`NextImage`）、input-image-alt、form-label（label for、包住的 label、aria-label、aria-labelledby、title、隐藏/提交/按钮类型、select、textarea）、button-name、link-name、link-purpose（英文和 9 个中文词）、anchor-is-button、click-no-role/focus/key（HTML、Vue、Angular、Svelte、JSX）、media-autoplay、video-captions、iframe-title、heading-order、viewport-zoom、tabindex-positive、accesskey、role-no-focus、focus-outline |
| 中文与编码 | 20 条规则的说明全是中文，规则名与 WCAG 编号是上游写法；中文内容页面零误报；UTF-8 BOM；GBK 编码的文件仍能扫描；`\n`、`\r\n`、`\r` 和混合换行的行号正确 |
| 框架文件 | `.jsx`、`.tsx`、`.vue`、`.svelte`、`.astro` |
| 与上游一致 | `iter_tags` 与上游 `TAG_RE.finditer` 在 5 组样本和全部示例文件上结果逐个标签一致；`collect_label_for` 与上游 `re.findall` 结果一致 |
| 对比度 | 黑白 21:1；同色 1:1；#777777 对白 4.48（AA 正文不达标、大字达标）；#767676 对白 4.54；#6b7280 对白 4.83；7:1 边界；显示 4.50 但精确值 4.4994 的情况按未达标并给出说明；颜色格式 `#rgb`、`#rgba`、`#rrggbb`、`#rrggbbaa`、`rgb()`（逗号和空格分隔）、`rgba()`（小数和百分比）、颜色名；透明度混合和背景透明度说明；10 种非法颜色（含 `hsl()`、通道大于 255、透明度大于 1）都报 `INVALID_COLOR` 且信息是中文；部分非法时保留合法结果 |
| 输入校验 | 18 种非法 `scan` 参数、12 种非法 `contrast` 参数都返回 `INVALID_ARGUMENTS`；多余字段（包括试图写文件的 `json`）被拒且没有创建文件；找不到路径、不支持的文件类型、空文件夹、混合路径；`max_issues` 与 `errors_only`；报告和提示是中文 |
| 文件夹遍历 | 跳过 node_modules、dist、build 和隐藏目录；扩展名不区分大小写；`.js`、`.css` 不扫；符号链接逻辑；扫描前后文件哈希和修改时间不变（只读） |
| 上限 | 超过 1 MiB 的文件被跳过并说明（恰好 1 MiB 的被扫描）；文件数量上限给出“扫描没有跑完”；6 万次 `<div a=b ` 的畸形文件在 1 秒预算下被丢弃并说明、同一调用里的正常文件仍被扫描；5000 行的正常大页面几秒内扫完；未闭合的 `<button>`、`<a>` 大量重复也能在时限内返回 |
| 包内容 | manifest、asset.json、技能 frontmatter、规则文档里的 20 条规则与代码里的 20 条逐条一致、LICENSE 与 provenance 哈希一致且是上游原始字节、THIRD_PARTY_NOTICES 含必要内容、载荷里没有网络/子进程/动态执行/写文件的代码（只有一个只读 `open`）、没有缓存或日志文件 |
| 工具类 | 工具卡片（id、中文描述、必填项）、`invoke`、`stream`、20 个并发调用互不串扰、内部错误不暴露堆栈 |

## 2. 仓库格式检查

- `python tools/asset_release.py check plugins/a11y-enforcer`：`format_ok: true`。
- `python tools/asset_release.py preflight plugins/a11y-enforcer/a11y-enforcer` 和对原生 ZIP 的 `preflight`：扫描 0 个 JavaScript 文件，0 个已知动态执行特征。

## 3. 原生 ZIP 与宿主检查（真实 DeepAgent / Runner / SkillUseRail，没有模型）

- 构建：`python tests/make_native_zip.py`，确定性 ZIP，7 个条目，54559 字节。
- 解压到干净目录后，逐文件、逐 SHA-256 与源载荷和 `native-artifact.json` 比对：一致；条目没有绝对路径、`..`、缓存或日志。
- 对解压后的载荷运行 `tests/host_checks.py`（`--fixtures tests/fixtures/manual`）：
  - 两个工具 `a11y_scan`、`a11y_contrast` 以直接可见（`direct`）的方式加载，描述含中文；技能目录被加载。
  - 经 Runner 注册的工具调用：缺 `paths` 被拒；多余字段 `json` 被拒且没有写文件；不存在的文件返回 `ALL_PATHS_FAILED` 且原因是“找不到这个文件或文件夹”；无法识别的颜色返回 `INVALID_COLOR`。
  - 经 Runner 对中文示例文件的真实调用：
    - `登录页.html`：8 个错误、2 个警告（html-lang、viewport-zoom、heading-order、img-alt、form-label、button-name、link-purpose、click-no-role/focus/key）。
    - `商品卡片.jsx`：6 个错误、0 个警告。
    - `订单表单.vue`：7 个错误、3 个警告。
    - `正确示例.html`：0 个问题（对照）。
    - 文件夹（4 个文件）：21 个错误、5 个警告；`errors_only` 时 0 个警告、21 个错误。
    - 对比度：黑白 21.0；#777777 对白 4.48（AA 正文不达标），#767676 对白 4.54（达标）。
  - 卸载后工具和技能都消失；载荷与示例文件的哈希在检查前后不变。
- 结果记录：`host-report.json`（`model_calls: 0`，`payload_unchanged: true`，`fixtures_unchanged: true`）。

## 4. 对畸形输入的实测（支撑有界匹配的修改）

在上游正则上用一次性探测脚本实测（没有运行上游脚本）：2 万字符的畸形输入耗时 2 到 8 秒，10 万字符的同类输入 5 分钟内未跑完。移植后的工具对 100 万字节的同类文件（`<div a=b ` 重复、`<a b={` 重复、`<label ` 重复、`<img ` 重复、`<button ` 重复）在当时 60 秒的单文件预算下全部在预算处被丢弃并说明，没有拖死；之后把单文件预算改为 10 秒（总预算仍 60 秒），并用测试覆盖了超时路径。没有再用 100 万字节的畸形文件完整重跑一遍 10 秒预算的耗时。

## 5. 没有测、或测得不够的部分

- 没有在 WorkSwarm 前端里用真实模型对话：模型是否会在合适的时候调用工具、是否按技能分级汇报、会不会把“没有发现问题”说成“符合 WCAG”、改代码时是否尊重“只在用户要求时才改”，要靠用户手工测试（`MANUAL_TESTING.md`）。
- 示例文件是手写的小文件；没有在真实的大型前端项目（几千个文件、`.vue`/`.astro` 的复杂模板、Tailwind、JSX 里嵌套很深的属性）上测过误报和漏报率。
- 没有在浏览器里验证示例页面的实际无障碍表现，也没有用读屏软件试过；扫描结果只是标记层面的静态判断。
- 对比度只验证了与 WCAG 公式一致的几个已知值（21:1、#767676 为 4.54:1、#777777 为 4.48:1），没有与浏览器或其他工具逐项交叉比对。
- 没有运行上游仓库里的脚本（来源未审查的下载代码，见 SOURCE_REVIEW.md）。因此“与上游行为一致”靠“规则代码约 83.8% 的行保持原样”、逐标签的正则等价测试和上面的回归测试来支撑。

## 6. 运行中的警告（非阻塞）

- SDK 在隔离宿主检查里报：`Failed to load description from …/SKILL.md: 'NoneType' object has no attribute 'fs'`（本团队已交付的其他插件在同一检查里有同样的警告）；技能目录仍然被加载并在卸载时移除。技能能否在 WorkSwarm 里被模型发现，要靠用户手工测试确认。
- SDK 报 `No module named 'redis'`（在线训练 rail 不可用），与本插件无关。

## 7. 最终哈希记录（2026-11-13）

| 产物 | 文件 | 大小 | SHA-256 |
| --- | --- | --- | --- |
| 原生测试包（交给用户测试） | `test-packages/a11y-enforcer-1.0.0-native.zip` | 54559 字节 | 5faef2928eed506c873812bd19a00fbb888c0c9891a55196d94081c0af0f7897 |

| 规范包装包（准备交付） | `releases/agent-plugin/a11y-enforcer/1.0.0/a11y-enforcer-1.0.0.zip` | 56023 字节 | 5fba65bdb086dbb0a9999bf179f0fdce1de83894a77bffbba26b8477c14e720a |

两个包的 7 个内层载荷文件逐文件、逐 SHA-256 一致（包装只多出外层 `plugin.yaml`）；`tools/a11y_enforcer.py` 的 SHA-256 记录在 `test-packages/native-artifact.json` 和 `releases/.../artifact.json`。上述自动测试和宿主检查都是针对这套字节。用户测试之后如果载荷、名称或本地化有任何改动，需要重新构建、重新测试并重新确认。

## 8. 用户手工测试（WorkSwarm，2026-11-13）

测试人：Nguyen Trung Dung，在 WorkSwarm 里安装 `a11y-enforcer-1.0.0-native.zip`（SHA-256 5faef2928eed506c873812bd19a00fbb888c0c9891a55196d94081c0af0f7897），把 `D:\jiuwen_reposgentic-hub-plugins\ForTestings`（`tests/fixtures/manual/` 的副本）当作测试目录，用真实模型对话，约 15:21 到 15:36（Asia/Singapore）。收到 3 张界面截图和 3 张完整对话导出，看到的内容：

- 工具与技能：`a11y_scan`（参数 `paths`、`max_issues`，结果 DONE）和 `a11y_contrast`（用户自选的三组颜色，结果 3.21、3.43、3.66，与独立重算的 3.2127、3.4289、3.6645 一致）被真实调用；模型通过 `skill_tool` 加载了 `web-accessibility-check`。
- 测试 1（登录页，3 次对话）：10 条问题，8 个错误、2 个警告，与预期一致。
- 测试 3（`商品卡片.jsx`）：6 个错误、0 个警告，与预期一致。
- 测试 5（整个目录）：警告 5 处，与预期一致。
- 测试 10（不在目录里的文件）：模型说明目录里只有这 4 个文件、找不到该文件，没有编造结果。
- 测试 11（只看错误）：只报告错误，把两个警告列为按请求排除，与预期一致。
- 测试 12（改正）：模型先询问，用户确认后才改文件；改动尽量小；用 `a11y_scan` 重扫得到 0 个错误、0 个警告；说明静态扫描不等于 WCAG 合规，并列出需要人工确认的部分。这次修改只发生在用户自己的测试副本 `ForTestings\登录页.html`，仓库里的示例文件没有变。
- 诚实度：文件里没有颜色时，模型说明 `a11y_contrast` 没有可算的输入，没有编造比值。
- 没有看到的测试：2、4、6、7、8、9（用户用自己选的颜色代替了 6 到 8 的示例）。
- 非阻塞观察：第一次对话里模型对中文提问用英文回答；另外两次对话用中文回答，其中一次先加载了技能。工具返回里已有“请用简体中文向用户汇报”的提示，但模型没有遵守，属于模型的语言选择；用户认为这不构成阻塞。

用户随后通过明确的问答确认：测试通过，没有阻塞问题；中文显示名保持“网页无障碍检查”。原始截图已收到，将附在交付 PR 的证据评论里。
