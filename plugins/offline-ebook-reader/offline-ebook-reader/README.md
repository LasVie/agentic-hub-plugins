# 离线书架阅读器 1.0.0

把用户明确选择的本地TXT或未加密流式文本EPUB复制到私有书架，在独立浏览器中连续阅读、按章跳转、调整排版并保存阅读位置。原文件不修改，没有在线书源、联网搜索、朗读、翻译或自动创作。

## 安装与开始

在WorkSwarm「扩展 / Extensions」导入同版本 `offline-ebook-reader-1.0.0-workswarm.zip` 并安装、启用。确认名称「离线书架阅读器」、版本1.0.0、1个技能及3个工具。仓库规范市场包装ZIP含外层 `plugin.yaml`，此旧宿主使用载荷完全相同的原生测试ZIP。

需要macOS/Linux、Python3.11+、宿主原生Tool/ToolCard SDK和现代桌面浏览器；不额外安装npm/Python依赖或下载模型。Windows未支持。准备一个已存在的专用工作目录，文件路径均使用真实绝对路径，不经过链接。

1. 明确授权保存书籍副本，然后调用 `manage_ebook_library`：`action="import"`、`workspace="/用户/专用书架"`、`path="/用户/书籍/示例.txt"`、`confirmed=true`。TXT默认UTF-8；旧中文编码须显式 `encoding="gb18030"`，带BOM的UTF-16用 `encoding="utf-16"`。不会猜测编码。
2. 用实际返回的 `book_id` 调用同一工具的 `action="toc"`，查看真实章节顺序与导入说明。`action="list"`读取书架、设置和revision；相同原始字节重复导入返回 `reused=true`，不清除已有进度。
3. 明确授权启动本机阅读器，调用 `local_ebook_reader`：`action="start"`、相同 `workspace`、`confirmed=true`。在同一台电脑的独立浏览器标签页打开实际返回的完整URL，点击书架中的书名阅读。不要编造URL或把工具启动成功当作人工阅读已通过。
4. 点击目录跳章、向下滚动。滚动后尝试自动保存；离开前点击「保存阅读位置」，以成功提示为准。刷新页面或重启服务后能从同一书架恢复已保存章节和章内比例；排版变化可能导致像素位置略有差异。
5. 调整字号、行距、栏宽、纸张色，点击「保存阅读设置」。多个窗口或工具并发保存时，旧revision被拒绝；刷新后重试，不覆盖新记录。

查询服务用 `local_ebook_reader` 的 `action="status"`；关闭用 `action="stop", confirmed=true`。服务只监听127.0.0.1，30分钟无请求或4小时后关闭；重启保留书架和进度。不会依据保存的PID杀进程，也不会停止其他插件服务。

## 工具与数据

- `manage_ebook_library`：import/list/toc/progress/preferences。保存进度需 `book_id`、从0开始的 `chapter_index`、`offset_ratio`（0～1）、刚取得的 `expected_revision` 及 `confirmed=true`。保存设置需完整preferences对象和同样的revision/授权。
- `read_ebook_chapter`：按 `book_id`、`chapter_index`只读真实文本；默认最多20000字符，范围按 `start_char`、`max_chars`控制。`truncated=true`时用实际 `next_char`续读，不把片段当作完整章节。它不生成摘要或改写正文。
- `local_ebook_reader`：start/status/stop。返回的URL含本机访问凭据，不要公开分享；对外提交截图时隐藏地址栏。

数据保存在 `workspace/.offline-ebook-reader/`：原始书籍副本、解析文本、书架、阅读位置、排版设置与服务状态。目录权限700，文件600；不加密，不是操作系统沙箱，不能防御同用户恶意进程。没有上传、同步、自动删除或原文件覆盖功能。原文SHA-256用于一致性检查，不证明版权、来源真实性或完整作者身份。

## 支持范围与限制

- 输入最多8MiB，正文最多200万字符、500章，最多40本及128MiB副本；EPUB最多400项、累计解压24MiB、单项4MiB、XML深度50/10万节点。
- TXT按常见中文「第X章/卷/回」及Chapter数字标题切章；不识别的标题保留正文，完全没有标题时是一章。正文不依赖模型处理。
- EPUB2/3：只支持UTF-8 XML/XHTML、单包文档、未加密流式文本，按spine主序列读章；可采用nav/NCX标签作为章名。本版目录是章节级，不保留每个章内锚点或完整原目录树。
- EPUB为纯文本投影：段落及常见结构换行，图片仅保留替代文字；CSS、字体、复杂图形/数学、多媒体与脚本不渲染，导入说明持续可见。不保证原书版式、交互链接、脚注往返或图文完整保真。
- 拒绝DRM/加密/字体混淆、固定版式、图像占位符之外无正文的章节、DTD/实体声明、危险路径、重复项、特殊文件、缺失引用及损坏/超限归档。合法但超出本版范围的EPUB也可能被拒绝；请用原书核对，不把警告当成完整兼容证明。
- 常见错误：`confirmation_required`需明确授权；`revision_conflict`需刷新状态；`invalid_encoding`需正确编码；`encrypted_epub`/`fixed_layout`为不支持；`unsafe_archive`/`unsafe_xml`为拒绝；`integrity_mismatch`为副本损坏；`busy`稍后重试。状态损坏不自动重置。

命令行可用 `python3 -B runtime/ebook.py --help`。实际功能、宿主及浏览器测试范围见开发目录TEST_REPORT.md，打包校验不代替人工测试。

## 来源与许可

基于xrn1997/dsh-novel0.8.1固定提交f9a19f5fbd2d76ef5e970c2333a67f9dcb66b31c的本地导入、书架和阅读位置流程适配；Copyright 2026 xrn1997，Apache-2.0。完整许可在 `licenses/dsh-novel/LICENSE`，实际复用/修改说明在 `THIRD_PARTY_NOTICES.md`。不包含上游书源引擎、截图、图标、字体或书籍，不表示上游官方背书。
