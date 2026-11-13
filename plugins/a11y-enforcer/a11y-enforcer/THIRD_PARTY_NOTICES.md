# 第三方声明

## A11y Enforcer: WCAG Accessibility Checker

- 上游：https://github.com/petrovicistefan/claude-code-plugins ，目录 `a11y-enforcer`，固定提交 `0b19c0dd919c2b5e0b992fb1610ef2ca427a357f`（2026-10-07；上游 `plugin.json` 版本 1.0.0）。
- 版权声明：Copyright (c) 2026 Stefan Petrovici。
- 许可：MIT。完整许可文本（含免责声明）随包提供：`licenses/a11y-enforcer/LICENSE`，与上游固定提交的 `a11y-enforcer/LICENSE` 逐字节一致（SHA-256 `5f434c88921e448707dc3b7983a41364721fdbec7468735c26dba2200f183d04`，Git blob `b723472340e31da4d4c4452bb6e21a893e04f480`，LF 换行，1073 字节）。上游没有 NOTICE 文件。
- 实际复用范围：
  - `skills/a11y-enforcer/scripts/a11y_scan.py`（Git blob `798293a064dc58015fb86bcc4d5e22808a49559a`，10571 字节，SHA-256 `610e7ac63235bd1577d1f62d7812bea77e25872530fba9ad543cda97e5b4f87f`）与 `skills/a11y-enforcer/scripts/contrast.py`（Git blob `d71961c8cd2d8f0f184ddfd1f8e351b68a0c6530`，2669 字节，SHA-256 `4e8a80bef217860874b87ed696b776c82166eea8537bd9fe2e89a280e52b98f0`）：合并移植为本包 `tools/a11y_enforcer.py` 中“移植自上游”的一段，扫描规则和对比度算法保持上游原样，按下面的修改摘要改动。上游两个文件都没有单独的版权头；本包文件头部的说明里写明了来源和许可。
  - `skills/a11y-enforcer/SKILL.md`（Git blob `e742f7dfb50f4eab9ca1e8e968dbad8e6586af9e`）：译为简体中文并改写为 `skills/web-accessibility-check/SKILL.md`。
  - `README.md`（Git blob `7c294748da687d7d5d9d9b54c4c1cb47a191515c`）和 `SKILL.md` 里的规则清单被参考，用来编写 `skills/web-accessibility-check/references/rules.md`；本包 README 独立编写。
- 修改摘要：
  1. 把 20 条规则的说明、对比度结论和颜色解析错误全部改为简体中文；规则名、WCAG 编号和“错误/警告”两个级别保持上游写法。
  2. 增加中文识别：链接文字里的“点击这里、点这里、这里、了解更多、查看更多、更多、详情、点击查看、链接”也按“链接文字没有说明去向”提示。
  3. 有界匹配和时间上限：上游对整个文件做一次性正则匹配，遇到大量未闭合的标签时耗时随文件长度二次方增长（实测 2 万字符的畸形输入就要数秒）。本包把标签匹配限定在 8000 字符的窗口、`<label>` 匹配限定在 2000 字符、查找结束标签最多向后看 20000 字符，每个文件 10 秒、一次调用 60 秒的时间预算，超时的文件丢弃结果并说明；单个文件超过 1 MiB 不扫描；一次调用最多 3000 个文件、总计 200 MiB。正常大小的文件结果与上游一致。
  4. 文件夹遍历：扩展名不区分大小写，跳过符号链接；显式指定的文件只接受上游支持的扩展名。
  5. 对比度：`rgb()`/`rgba()` 的数值超出范围（通道大于 255、透明度不在 0 到 1 之间）时拒绝，而不是默默算出一个结果；函数 `parse` 改名为 `parse_color`。
  6. 去掉命令行入口（`argparse`、`main`、`sys.exit`）和 `--json` 写文件的选项，把两个脚本合成一个模块，改成可直接调用的 `scan_file()`、`ratio()`；增加两个原生工具类（`a11y_scan`、`a11y_contrast`）、输入校验、错误处理和报告格式。
  7. 技能说明由“在 Claude 里用 `python3 ${CLAUDE_SKILL_DIR}/scripts/...` 运行脚本”改为调用两个原生工具，并增补中文页面的检查项；只在用户要求修复时才改代码。
- 未复用：上游 `.claude-plugin/icon.png`、`.claude-plugin/plugin.json` 的清单、`commands/` 下的两个斜杠命令、`README.md` 末尾的作者介绍和联系方式、`PRIVACY.md`。
- 授权范围说明：MIT 许可覆盖上游的代码和文字；不授予上游图标、名称或商标的任何权利，也不表示上游作者认可本插件。

## 本插件独立编写的部分

- `tools/a11y_enforcer.py` 文件头部的有界匹配与时间上限函数，以及文件末尾的两个原生工具及其输入校验、错误处理和报告格式。
- `skills/web-accessibility-check/` 中为中文页面增补的内容，`references/rules.md` 和 README。
- 本插件不联网、不写任何文件、不保存任何内容，也不附带图片、字体、数据集或二进制文件。

## 效果声明

本插件只做静态扫描和对比度计算，没有发现问题不等于符合 WCAG，也不能替代用键盘、读屏软件和浏览器工具所做的无障碍检查或审计。
