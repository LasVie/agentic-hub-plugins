# Word 引用脚注转换 1.0.0：功能与交付前验证

- 日期：2026-10-27；负责人：Cai Zhenze。
- Candidate：CAND-CLD-322；Task：AH-20261027-word-citation-notes。
- 仅本聊天工作树，分支 feat/word-citation-notes，起点 c85e1e8a056dcd9af8039b1192204fe9a97b7b18。没有修改Main工作目录。
- Python3.12.14、lxml6.1.3（libxml2 2.14.6）、openjiuwen0.1.19；python-docx1.2.0只用于开发检查，非运行时重存依赖。

## 已执行的功能测试

`python -B -m unittest discover -s tests -p test_word_citation_notes.py -v`：24/24通过。真实lxml和openJiuwen环境；SDK封装在独立子进程实际invoke/stream，未调用模型、网络服务或收费API。

| 测试组 | 实际结果 |
|---|---|
| 中文、emoji、Unicode码点、重复年份/相同引文、相邻精确范围 | 位置准确；quote不符明确拒绝；不按年份猜测 |
| 跨不同样式run的replace/append、简单超链接 | 未选文字/运行属性和超链接关系保留 |
| 原生脚注、原生尾注 | 正文引用、注释部件、关系、内容类型、分隔符及按正文位置编号通过独立OOXML断言 |
| 原件、参考文献、未变ZIP成员 | 源DOCX字节不变；参考文献保留；未变成员原字节保留 |
| inspect/preview | 不写文件；完整段落/动作；摘要绑定源、完整计划及新输出 |
| 确认、源/计划/输出变化、旧摘要 | 明确拒绝；不产生转换输出 |
| 已有输出、输入别名、预览后竞争创建 | 拒绝覆盖，竞争创建的文件保持原样 |
| 重复JSON键/ID、未知键、类型、重叠、越界 | 明确拒绝，不静默丢字段 |
| 表格、域、修订、已有注释、外部模板 | 不支持的结构明确拒绝 |
| 路径逃逸、软/硬链接、ZIP重复/穿越/加密/链接/膨胀、XML实体/DTD | 明确拒绝，无解析外联 |
| CLI、工具说明、默认响应 | UTF-8简体中文；技术标识/原始许可保留 |
| 人工测试输入生成器 | 固定摘要、只生成7个公开虚构输入，拒绝覆盖已修改文件；不执行转换 |

`python tools/asset_release.py check plugins/word-citation-notes`和`pack`通过。市场外壳ZIP、原生ZIP解压后以及实际安装路径分别运行同一套24项测试，均24/24通过；8个载荷文件逐项摘要相同、原始MIT全文摘要一致、无缓存。独立审查未发现阻塞问题。

仓库回归在已有Node22.23.3及仅PyYAML开发依赖环境中执行：509项，419通过、90项可选环境跳过；本插件完整SDK/lxml测试另行实际通过。`check-repo`：41个源码资产、50个ZIP通过。首次受限环境未配置Node且禁止本地监听，导致其他插件15个环境错误和阅读器启动失败；在已有Node及本地回环可用条件下重跑通过，未修改其他插件。

## 冻结包装与宿主

- 市场ZIP：`releases/agent-plugin/word-citation-notes/1.0.0/word-citation-notes-1.0.0.zip`；SHA-256：`03da5e1d00c4873ebaff0e4547470f37ce5c86ba63d9d4f7173a1f73dd63a658`。
- WorkSwarm原生ZIP：`plugins/word-citation-notes/test-packages/word-citation-notes-1.0.0-workswarm.zip`；SHA-256：`335a003d520315f8688f548ff284af9154829a3a32fc1cf885ee419870303b57`。
- 两包8个载荷文件与源码和实际安装文件相同，详见package-verification.json；没有把测试、任务记录或临时渲染文件放进载荷。
- 复用本聊天专用WorkSwarm：前端6392 HTTP200；后端29290及前端代理6392的WebSocket ping/pong、配置读取和扩展目录RPC成功；新ID事前未占用，import_local和install成功，显示connected。
- 浏览器真实核对「我的扩展」及详情：中文名、1个技能、3个中文工具说明均正确。宿主版本来自安装manifest1.0.0，页面未显示独立版本字段，不据此编造UI版本标识。其他2个插件目录记录及配置SHA-256前后相同；无端口复用冲突、服务重启或模型请求。host-verification.json记录实际结果。
- 对话测试仍由用户自行选择/配置宿主模型；现有disabled-local-test保留，AI未读取/输出密钥或擅自改模型。工具本身离线，SDK直接调用通过不等同于模型对话测试。

## 真实文档渲染

在独立临时测试目录实际调用本版核心生成footnote.docx和endnote.docx；未使用人工测试workspace的输出路径。LibreOfficeDev26.8.0.0.alpha0（2c87e51eeaa2b413ff4ae097b2705eea1995d8e5）分别读取两份DOCX并导出PDF；Poppler渲染页面，逐图核对：页下注在页底，文末注在正文后；正文1/2与注释1/2对应，中文、emoji、页码、保留的乙文献引文和参考文献可见，未发生剪裁或重叠。

首次默认Fontconfig没有读取系统中文字体，渲染缺字；仅为此临时渲染进程提供指向macOS已有字体的Fontconfig配置和临时缓存后重新渲染通过。未改插件、宿主、Main或系统字体，未复制/分发字体。PDF文本提取交叉核对中文和两项注释。这是开发渲染证据，不是用户人工测试截图，也不证明所有Word版本的分页一致。

## 人工测试边界

本次公开原件摘要：`380dcd1233e8eade020a8e6b2ef06d2ab34ba076860ac11637dbc07fb70758e3`。人工workspace仅含输入，尚无脚注/尾注转换输出。请按MANUAL_TESTING.md先检查/预览，核对具体计划并明确确认后再转换，最后用真实Word/兼容查看器检查两份结果并提供原始截图。

用户尚未确认本包测试完成；没有用户截图；没有push、交付PR、merge、Release或Hub提交。已知范围限制：仅支持明确支持的顶层正文文字段落；不处理表格、字段、修订、书签、已有注释、页眉页脚或自定义注编号；不验证来源真实性或法律格式。
