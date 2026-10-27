# 离线书架阅读器 v1.0.0 人工测试

候选 CAND-DSH-329；任务 AH-20261027-offline-ebook-reader；负责人 Cai Zhenze。当前仍处于本地测试阶段，尚未声明人工测试通过。

## 安装包与环境

- WorkSwarm：<http://127.0.0.1:6393/>。已安装“离线书架阅读器”，可在“扩展 → 我的扩展”查看一个技能和三个工具。
- 测试 ZIP：`/Users/IDLE_And_R/Downloads/Huawei/agentic-hub-plugins/plugins/offline-ebook-reader/test-packages/offline-ebook-reader-1.0.0-workswarm.zip`
- 测试 ZIP SHA-256：`0da0b30a9961bc6ea1fd66b18b8085f1f10446eb14526ca013e6edfaa9669222`
- 规范 Agentic Hub ZIP：`/Users/IDLE_And_R/Downloads/Huawei/agentic-hub-plugins/releases/agent-plugin/offline-ebook-reader/1.0.0/offline-ebook-reader-1.0.0.zip`
- 规范 ZIP SHA-256：`f6b38c5e1f05055c041971609a6669f5aefcb45d37563722d55e7e12c55b6cf4`

两个 ZIP 的十个内部运行文件完全一致；规范 ZIP 多一层市场包装。WorkSwarm 本地“上传文件创建”使用测试 ZIP。若在另一个实例安装，进入“扩展 → 我的扩展 → 创建 → 上传文件创建”，选择测试 ZIP 并确认；不要选择“发布”。当前实例已安装，无需反复安装或卸载。

新的隔离 WorkSwarm 未复制旧模型密钥，`disabled-local-test` 指向本机关闭端口，因此不会自动发出有效模型请求。可以直接在独立桌面 Chrome 中测试下面的阅读器，无需模型。若要额外测试 WorkSwarm 聊天，请先自行在这个隔离实例配置模型；本次未代替你运行模型或付费调用。

## 无模型直接测试

合成书籍目录：`/Users/IDLE_And_R/Downloads/Huawei/agentic-hub-plugins/dist/offline-ebook-reader/1.0.0/manual-test/`

专用工作目录：`/Users/IDLE_And_R/Downloads/Huawei/agentic-hub-plugins/dist/offline-ebook-reader/1.0.0/manual-test/书架工作目录`

已用已安装的真实工具导入“中文三章示例.txt”和“中文顺序示例.epub”，并启动本机阅读器。当前完整地址见本地文件：`dist/offline-ebook-reader/1.0.0/MANUAL_SESSION.md`。请在运行服务的这台电脑上用独立 Chrome 标签页打开实际地址。地址含临时本机访问凭据，请勿公开分享。

1. 打开 TXT，检查三章中文、标点和表情可读；点击目录在章节间跳转，连续向下滚动，确认仍是原文而不是生成的摘要。
2. 滚到第二章中部，点击“保存阅读位置”，等待成功提示。刷新页面，核对恢复到第二章及接近的章内位置。修改字号、行距、栏宽和纸张主题，点击“保存阅读设置”；刷新，检查设置及位置保留。
3. 打开 EPUB，检查“第一章 出发 → 第二章 归来”顺序正确；查看“导入说明与格式边界”，应明确提示图片替代文字和样式/脚本等省略。不得执行书内脚本、加载示例远程图片，或声称完整复刻出版排版。
4. 关闭并重启阅读器后，用新返回的地址打开，核对书架、位置及设置仍在。仅刷新网页与重启服务是不同检查，分别记录。
5. 可选：把自己有权使用的小型 TXT/未加密流式文本 EPUB 导入本专用工作目录，核对目录、真实正文与重开恢复。原文件不应修改。

阅读器空闲30分钟或运行4小时后会关闭。需要重新启动时，可在仓库根目录运行以下命令（只启动本专用工作目录的阅读器，输出真实 URL）：

```sh
python3 plugins/offline-ebook-reader/offline-ebook-reader/runtime/ebook.py reader --input-json '{"workspace":"/Users/IDLE_And_R/Downloads/Huawei/agentic-hub-plugins/dist/offline-ebook-reader/1.0.0/manual-test/书架工作目录","action":"start","confirmed":true}'
```

查询时将 `action` 改为 `status`；明确要关闭时改为 `stop` 并保留 `confirmed:true`。不删除书架状态，不操作别的服务。

## WorkSwarm 真实工具测试提示词（自行配置模型后可选）

```text
请仅使用“离线书架阅读器”的真实工具，测试 v1.0.0。不要编写替代阅读器，不生成书籍正文，不联网。

我明确授权把以下合成测试文件复制导入这个专用工作目录，并启动该目录的仅本机阅读服务：
workspace=/Users/IDLE_And_R/Downloads/Huawei/agentic-hub-plugins/dist/offline-ebook-reader/1.0.0/manual-test/书架工作目录
测试文件目录=/Users/IDLE_And_R/Downloads/Huawei/agentic-hub-plugins/dist/offline-ebook-reader/1.0.0/manual-test/

1. 实际调用 manage_ebook_library，action=import，confirmed=true，依次导入“中文三章示例.txt”和“中文顺序示例.epub”。这两个文件可能已经导入，重复导入应保留阅读位置，不要删除状态。
2. 使用实际返回的 book_id 调用 action=toc，并用 read_ebook_chapter 读取各书的一小段原文。展示真实版本、章节数量、顺序、原文、字符范围及导入警告。
3. 尝试导入“固定版式拒绝.epub”和“损坏示例.epub”，应如实返回不支持/无效文件，不能修复或替换它们。
4. 导入“旧编码示例.txt”：默认 UTF-8 应报告编码失败；明确使用 encoding=gb18030 后应成功，不得猜编码。
5. 实际调用 local_ebook_reader，action=start，confirmed=true；再用 action=status 查询。展示真实 ok、version、running、session_id 和完整 URL；同一存活会话应复用。不要伪造地址。

用中文汇总实际结果，提醒我独立操作浏览器并检查保存/恢复。工具不可用或失败时如实报告。不要把导入或启动成功称为人工阅读测试通过。不要发布或提交任何内容，不改其他插件和模型设置。
```

## 范围与测试回报

仅 macOS/Linux、Python3.11+、桌面浏览器。支持有界 TXT 和未加密流式文本 EPUB；不支持 DRM、固定版式、图片书或完整排版、在线书源、朗读、翻译、编辑/删除。最多8MiB输入、200万字符、500章、40本。保存的是章节和近似比例，不是固定页码。书架副本与状态仅存本机，未加密。

完成后请明确说明 **CAND-DSH-329 — 离线书架阅读器 v1.0.0** 的人工测试是否通过，并提供原始截图：WorkSwarm 真实工具返回（若测试聊天）、当前版本的阅读界面、章节中部保存及重开恢复、设置保存。截图与明确确认是不同材料。任何问题请保留实际错误，不删除或覆盖证据；修包后将提供新版本重新确认。

状态更新：2026-10-27，Cai Zhenze 已明确确认本版人工测试通过并提供四张原始截图，见 USER_TEST_CONFIRMATION.md。此文保留为复现指南；截图中的临时阅读会话已关闭。重新运行测试会生成新的实际地址。
