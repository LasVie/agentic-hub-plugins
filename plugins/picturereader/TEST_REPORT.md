# 像素证据读图器 1.0.1：当前版本测试记录

日期：2026-11-04（Asia/Singapore）。负责人仍为 Siu Lok Yin；原 Task / Candidate ID 保持不变。

本次变更：用户可见说明、Skill、工具诊断和报告中文化；机器标识、参数结构与原生实现边界保持不变。下面旧版本记录完整保留，仅作历史，不能确认本次中文包。

## 2026-11-04 当前精确包：真实 WorkSwarm GUI 与中文提示测试

用户明确委托 Agent 使用本地已打开的 WorkSwarm 测试导入与 prompt，成功后留存原图并提交 PR；后续又直接授权本任务合并及推送。根 Agent 按该授权实际操作 GUI，并目视核对当前原图。本次为 **AI 受委托测试**，`human_performed_testing=false`；没有宣称用户本人亲测，也没有把旧版确认或新造的“用户口头通过”当作本轮证据。PR、Hub 与最终验收仍按真实后续动作分别记录。

- 时间：2026-11-04 14:47–14:48（Asia/Singapore）；真实会话 `web_1a1a55030d9_5f82abe2c5d5`，模型 `gpt-6.1-sol`。
- 本轮实际宿主：**WorkSwarm 桌面 0.2.8、内嵌 Python 3.12.13、Pillow 12.2.0**。当前运行 gateway 的 App 可执行文件及其加载的 Python/Pillow 库已独立只读核对。这与下方开发验证的隔离 0.2.9b1 / Python 3.11.17 / Pillow 12.3.0 是不同环境。
- 导入：根 Agent 通过 WorkSwarm 原生界面导入精确 native ZIP，实际 toast“插件导入成功”，详情显示像素证据读图器 1.0.1。独立核对实际安装 README、manifest、Skill、工具源码四文件 SHA 与冻结 payload 全部相等。
- 真实工具：整图 `image_scan` 返回 120×80、20×7 网格；`image_sample` 四象限红/绿/蓝/白精确采样；`image_palette(count=5)`；`image_crop` 以 `overwrite=false` 成功导出区域 `(60,40,60,40)`；对 60×40 裁剪图重新扫描；最后越界采样 `(999,1)` 实际返回预期 `ok=false / INVALID_IMAGE` 及中文错误“图像处理失败：坐标 (999,1) 超出图像边界 120x80”。四个工具均由真实原生调用执行，未用终端脚本替代。
- 计数边界：界面显示 13 条调用记录，实际为 1 次 `tool_search`、6 次 `tool_call` 包装、6 次原生调用；不是 13 项独立功能测试。七张 JPEG 为同一流程的不同视窗，另有一张原生导出长 PNG，也不是八项独立测试。
- 文件独立核对：`gui-crop.png` 确为 60×40、116 字节，SHA-256 `4dbc5e9138bd18a9995f307765986c1641d41098371da27311e448f6df57048b`；全部 RGB 像素等于输入图对应区域。当前 fixture SHA-256 `552f1ad1a45a1fc54c5aa1265d12383d199e5387f42e17b68d87e8b68a9428b6`，与上午功能测试保留的原 fixture 当前字节相等、mtime 均为 11:58。没有找到独立保存的 pre-GUI 哈希快照，因此不补造严格的前后哈希对；独立开发测试另有操作前后源文件哈希不变断言。
- 时间显示边界：live GUI 观察为 53.69 秒，原生导出摘要显示 54.20 秒，保留为两项真实显示观察，不合并成虚构精确耗时。

原图原字节保存在 `test-evidence/20261104-zh-1.0.1/`，逐文件大小/哈希及委托、版本、调用和限制在 `GUI_TEST_RECORD_1.0.1.json` 与同目录 `evidence.json`。原生长图 `jiuwenswarm-share-20261104-144945.png` 为 2250×9261、1212052 字节，SHA-256 `9bdc07cd95cbf054f5076c6ddfe591f02b3e9812f155da88e521c8a297d7952e`；从 Downloads 原字节复制，未经重压缩、缩放或裁切，已实际查看。长图是渲染对话摘要，不包含展开的原生工具 trace，也不能单独证明版本；配套原图/AX与安装字节核对共同关联当前精确包。

本轮只更新包外记录与证据，四个运行文件和两个冻结 ZIP 的字节不变。没有在此更新中 push、创建 PR、合并或提交 Hub；原图永久 PR 附件链接仍待实际交付时验证，不能填造。

## 独立开发功能与 SDK 验证（非本轮 GUI 环境）

环境：macOS 26.6 arm64，WorkSwarm 0.2.9b1 原有宿主环境，Python 3.11.17、Pillow 12.3.0；未安装或修改 Python 环境，未调用外部模型、网络图像服务或业务数据。

`tests/test_picture_reader.py` 实际调用四个 OpenJiuwen `Tool` 类，退出码 0，12 项通过：PNG/JPEG/WebP 扫描、红色区域主色、结构指标范围、四象限精确采样、色板比例、PNG 裁剪、操作前后源文件哈希一致、已有输出保护、越界拒绝和中文缺参诊断。原始输出见 `FUNCTIONAL_TEST_1.0.1.log`。源文件哈希现在在操作前记录，避免旧测试的同一时刻自比较。

真实 SDK `load_plugin_package` 与 `validate_plugin_paths` 已接受中文 manifest，解析到四个工具和一个 Skill。原生 ZIP 根部为 `manifest.json`；规范包为 `<slug>/plugin.yaml` 加同名内层载荷。两包与源码的全部四个运行文件逐字节一致。

- 当前原生包 SHA-256：`dce99062ee78e84454345be5ae0bd705660593bdb9836a6e96d2d17945db0066`
- 当前规范包 SHA-256：`94e4e4f161a2792097f6c2592990a47709e664ae4c765298d7fdcd534071a386`

上午开发阶段的 GUI 待完成状态已由下述本轮实际结果更新。历史 1.0.0 的用户确认与原图只覆盖旧包；本次没有补造新的用户口头通过声明。


## 2026-11-04 仓库验证范围

使用现有 Python 的 `-S` 隔离视图，仅只读加载仓库固定依赖 PyYAML 6.0.3，全仓单元测试 603 项通过、122 项因可选依赖跳过；没有安装或修改环境。两款当前包另用完整真实 WorkSwarm SDK 验证并实际实例化所有声明工具。

额外在完整 SDK 环境发现运行 608 项、61 项跳过时，有两个无关资产的 `assertWarns` 触发 SDK 的延迟模块属性错误：`offline-backup-recovery` 与 `offline-ebook-reader` 测试访问 `openjiuwen.core.foundation.store.__warningregistry__` 后抛出 `ModuleNotFoundError`。无需插件代码的 SDK-only 复现也触发同一错误。这次完整 SDK 全仓运行未通过，原始失败日志保留，不冒称全绿；CI 依赖隔离视图与两款当前包 SDK/功能测试结果分别记录。

`asset_release.py check-repo` 通过：63 项源码资产、75 个版本 ZIP。没有修改这两款之外的插件代码。

## 历史记录（原文保留）

# Functional Test — picturereader 1.0.0

Test date: 2026-10-23 (Asia/Singapore). Task `AH-20261023-picturereader`; candidate `CAND-DSH-177`.

Environment: macOS arm64, Python 3.11.15, OpenJiuwen host venv, Pillow 12.1.1. No network calls, API keys, external models, or business data.

Command:

```bash
~/agent-core/.venv/bin/python plugins/picturereader/tests/test_picture_reader.py
```

Result: **PASS**, exit 0. The test generates a deterministic 120×80 four-quadrant fixture and invokes all four real OpenJiuwen tool classes.

| Check | Result |
| --- | --- |
| PNG, JPEG, and WebP scan | PASS |
| Region scan and red-dominant measured palette | PASS |
| Structure measurements bounded to 0..1 | PASS |
| Exact red/green/blue/white coordinate samples | PASS |
| Palette shares sum to approximately 1 | PASS |
| PNG crop dimensions and bytes | PASS |
| Source bytes unchanged | PASS |
| Existing-output protection | PASS |
| Out-of-bounds coordinate rejection | PASS |

Repository format, deterministic packaging, extracted-ZIP loader, and repository-wide structural checks are recorded after the release package is generated. This development test is not a user WorkSwarm screenshot, Hub submission, or Project Lead acceptance.

## User WorkSwarm test

The user confirmed the exact manifest-at-root ZIP SHA-256 `4118f7c64584247ca3b3087b53beb3dd74171f9dae2f52bf24c412a92fb268fa` on 2026-10-23 and supplied the original 2250×24045 screenshot at `test-evidence/jiuwenswarm-share-20261023-130342.png` (SHA-256 `809f95f22d77295af1445651c17fe810c8f724cc6936a555aa2a6ad4cb5d8631`). See `USER_TEST_CONFIRMATION.md`. This evidence is outside the runtime ZIP.
