# 代码差异审阅模板

> 修改说明：2026-10-22，由 Anthropic Playground 原模板翻译并适配为简体中文；保留技术标识、来源和 Apache-2.0 许可。所有界面标签、提示词、帮助和复制状态默认中文；源材料按原值显示。来源见 ../THIRD_PARTY_NOTICES.md，完整许可见 ../licenses/claude-plugins-official/LICENSE。

当探索页用于审阅 git 提交、PR 或代码变更，并通过逐行评论提供反馈时，使用本模板。

## 布局

上方一侧显示真实提交哈希、提交信息、作者和日期，另一侧显示按文件及 hunk 分组的差异，带准确行号和 `+` / `-` 标记。底部提示词面板显示全部评论及“复制全部”按钮；固定面板不得遮挡内容，窄屏可改为正常文档流。

## 差异审阅控件

| 功能 | 控件 | 行为 |
| --- | --- | --- |
| 逐行评论 | 点击差异行或键盘激活 | 在该行下方打开输入框 |
| 评论标记 | 已评论行的徽标 | 显示该行有反馈 |
| 保存/取消 | 输入框旁按钮 | 保存或放弃当前编辑 |
| 复制提示词 | 提示词面板按钮 | 复制全部有效评论 |

## 差异数据

将真实差异解析为结构化数据再渲染。以下仅为结构示例，不可冒充真实提交：

```javascript
const diffData = [{
  file: "path/to/file.py",
  hunks: [{
    header: "@@ -41,13 +41,13 @@ function context",
    lines: [
      { type: "context", oldNum: 41, newNum: 41, content: "# 未改变的示例行" },
      { type: "deletion", oldNum: 42, newNum: null, content: "# 删除的示例行" },
      { type: "addition", oldNum: null, newNum: 42, content: "# 新增的示例行" },
    ]
  }]
}];
```

实际源代码、hunk header、文件路径和提交信息按原值展示，不翻译或改写。以 `textContent` 设置代码与评论，避免不可信文本进入可执行 HTML。

## 行样式

| 类型值 | 背景 | 文字颜色 | 前缀 |
| --- | --- | --- | --- |
| `context` | 透明 | 默认 | 空格 |
| `addition` | 浅色 `#dafbe1`；深色 `rgba(46,160,67,0.15)` | 浅色 `#1a7f37`；深色 `#7ee787` | `+` |
| `deletion` | 浅色 `#ffebe9`；深色 `rgba(248,81,73,0.15)` | 浅色 `#cf222e`；深色 `#f85149` | `-` |
| `hunk-header` | 浅色 `#ddf4ff` | 浅色 `#0969da` | `@@` |

## 评论系统

每行分配稳定且唯一的标识，以保存评论。更换筛选或重新渲染时保留评论；删除行使用旧行号，新增行使用新行号，明确区分位置。

```javascript
const comments = {}; // { lineId: commentText }
function selectLine(lineId, lineEl) {
  document.querySelectorAll('.diff-line.selected').forEach(el => el.classList.remove('selected'));
  document.querySelectorAll('.comment-box.active').forEach(el => el.classList.remove('active'));
  lineEl.classList.add('selected');
  document.getElementById(`comment-box-${lineId}`).classList.add('active');
}
function saveComment(lineId) {
  const textarea = document.getElementById(`textarea-${lineId}`);
  const comment = textarea.value.trim();
  if (comment) comments[lineId] = comment;
  else delete comments[lineId];
  renderDiff(); // 更新评论标记
  updatePromptOutput();
}
```

## 提示词格式

输出准确文件、行号、原代码和用户评论：

```javascript
function updatePromptOutput() {
  const commentKeys = Object.keys(comments);
  if (commentKeys.length === 0) {
    promptContent.textContent = '点击任一差异行添加评论；也可用键盘选择并激活该行。';
    return;
  }
  let output = '代码审阅意见：\n\n';
  commentKeys.forEach(lineId => {
    const lineEl = document.querySelector(`[data-line-id="${lineId}"]`);
    const file = lineEl.dataset.file;
    const lineNum = lineEl.dataset.lineNum;
    const content = lineEl.dataset.content;
    output += `📍 ${file}:${lineNum}\n`;
    output += `   代码：${content.trim()}\n`;
    output += `   评论：${comments[lineId]}\n\n`;
  });
  promptContent.textContent = output;
}
```

只输出用户真实保存的评论。若记录删除行，提示词中同时注明“旧行”，避免误认为当前文件位置。

## 行元素元数据

通过 DOM 属性赋值保存路径、行号和源文本；不将未经转义的源文本拼接成 HTML 属性：

```javascript
const line = document.createElement('div');
line.className = 'diff-line addition';
line.dataset.lineId = '0-1-5';
line.dataset.file = 'src/utils/handler.py';
line.dataset.lineNum = '45';
line.dataset.content = 'subagent_id = tracker.register()';
line.textContent = line.dataset.content;
line.tabIndex = 0;
```

## 读取真实差异

为指定提交创建页面时：
1. 在授权仓库运行 `git show <commit> --format="%H%n%s%n%an%n%ad" -p`。
2. 将实际输出解析成 `diffData`。
3. 把真实提交元数据放入页头。无法读取时说明缺失项，不虚构哈希、作者、日期或文件。

## 明暗主题

```css
/* 浅色主题 */
body { background: #f6f8fa; color: #1f2328; }
.file-card { background: #ffffff; border: 1px solid #d0d7de; }
.diff-line.addition { background: #dafbe1; }
.diff-line.deletion { background: #ffebe9; }
/* 深色主题：通过主题类限定，避免覆盖浅色规则 */
body.dark { background: #0d1117; color: #c9d1d9; }
body.dark .file-card { background: #161b22; border: 1px solid #30363d; }
body.dark .diff-line.addition { background: rgba(46, 160, 67, 0.15); }
body.dark .diff-line.deletion { background: rgba(248, 81, 73, 0.15); }
```

## 交互细节

- 悬停或聚焦行时显示“点击或按回车添加评论”。
- 保存评论的行显示 💬 标记，并允许重新编辑或删除。
- 保存、取消、复制等按钮有明确中文标签、关联输入框与可见焦点。
- 复制成功后提示“已复制”；失败时提示“复制失败，请手动选择并复制下方文本”，不显示虚假成功。

## 示例主题

- 单次 git 提交的逐行审阅。
- PR 的多提交、文件级与行级评论。
- 重构前后代码对比。
- 合并冲突的双版本标注。
- 带逐行发现的代码审计。

页面资源全部内联，不请求外部脚本、字体或服务。页面只生成复制回智能体会话的反馈，不自行发布 PR 评论或修改项目。
