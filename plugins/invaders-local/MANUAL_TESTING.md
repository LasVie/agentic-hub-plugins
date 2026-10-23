# 星际防线 v1.0.2 人工测试

候选 `CAND-CLD-302`；任务 `AH-20261023-invaders-local`；负责人 Cai Zhenze。

## 当前包与哈希

- WorkSwarm 测试包：`dist/invaders-local/1.0.2/invaders-local-1.0.2-workswarm.zip`
- SHA-256：`21df39acd6244c2d9be87685d4c04fb08df1baad1defcab2ce425ebbcc199f67`
- 规范包：`releases/agent-plugin/invaders-local/1.0.2/invaders-local-1.0.2.zip`
- SHA-256：`70aebf34f8d40746a3a9977ad22b27be3665b5351bb2535b0852d3d748acfeef`

两个 ZIP 的15个载荷文件完全一致，仅市场包装不同。此轮不要上传 Agentic Hub。

## 无模型测试（推荐，不产生模型费用）

1. 打开 `http://127.0.0.1:6283`，进入 Extensions → My Extensions，点击“星际防线”卡片。插件已通过后端导入并安装；应看到中文说明及“创建星际防线网页”工具。不要点击 Publish。
2. 打开已由当前载荷生成的 `http://127.0.0.1:6284/game.html`。确认标题为“星际防线”，版本为1.0.2、种子12345。
3. 点击“开始游戏”，再点击棋盘。用左右方向键或 A/D 移动、空格射击。核对分数、生命、护盾损坏和敌人运动；尽量完成一波。
4. 按 P 暂停，确认“步数”停止变化；再按 P 继续。切到其他标签页/窗口，返回时应已暂停。Esc 也应暂停。
5. 暂停后点击“保存进度”，记下位置、分数、生命与步数，刷新同一页面。应恢复这些数值且保持暂停。
6. 点击“重新开始”，应从种子12345重新开局，得分0、波次1、生命3、步数0；保留最高分。无须为游戏配置账号或模型。
7. 可双击 `dist/invaders-local/1.0.2/manual-testing/星际防线.html` 直接离线打开。浏览器本地文件存储权限可能不同；如不能续玩，应出现中文提示而不是假称保存成功。

## 重新导入（只在需要时）

当前已安装，无需重复上传。若要验证完整文件选择流程，只卸载“星际防线”，保留其他插件。然后 Extensions → My Extensions → Create → Create from file → Click or drag a file here，选择上述 **WorkSwarm 测试 ZIP** 并 Confirm。文件对话框可按 Command+Shift+G，粘贴完整 ZIP 路径。安装后重新打开卡片。

界面文件选择器由你人工确认；本轮自动检查验证了真实后端导入/安装，未声称已经操作系统文件选择器验证。

## 从当前包重新生成，不调用模型

将 WorkSwarm ZIP 解压至新目录，进入含 manifest.json 的载荷目录，然后执行（输出路径必须不存在）：

```sh
python3 runtime/export_game.py /private/tmp/星际防线-人工测试.html --seed 12345
```

应返回 `ok=true`、`version=1.0.2` 和实际输出路径。相同种子网页 SHA-256 为 `213d6dcff4da4a5157fc88a218cedbdf083a2c5a0d4cab674853e3d9d5a0c183`。再次运行同一路径应以中文拒绝覆盖，旧文件不变。浏览器直接打开新生成的 HTML 即可。

如果你自行选择用 WorkSwarm 对话测试，请明确要求实际调用 `create_invaders_game` 并核对返回版本、网页路径与哈希；不要仅接受模型声称已经执行。对话会使用你当前模型设置，游戏本身无需该调用。本轮代理没有运行任何模型对话。

## 完成反馈

请提供清晰的原始截图：当前版本与游戏关键操作/结果，以及 WorkSwarm 插件或实际工具结果（如有）。明确确认测试的1.0.2和上述 ZIP 哈希已完成或指出问题。截图本身不能替代你的明确确认；自动测试也不等于你的人工测试。本轮停在此处，不提交或发布。
