# 避免中文输入法回车误提交

> 修改声明：2026-10-27，由 Gan Mingrui 维护的 JiuwenSwarm 适配版；依据 GoogleChrome Modern Web Guidance 0.0.196 同名指南翻译、节选及修正示例。这是中文精选改编，不是完整逐字译本。

来源：[ime-safe-enter-submit](https://github.com/GoogleChrome/modern-web-guidance/blob/4f2b13e25c5815b3f080ca0d983e828d96561a0f/skills/modern-web-guidance/guides/forms/ime-safe-enter-submit.md)。获取日期：2026-10-27。下文浏览器版本来自固定上游快照，不代表实时支持；上线前按项目目标浏览器核实并做特性检测。

中文、日文和韩文输入法会用 Enter 确认候选词。自定义键盘提交逻辑必须区分确认候选与提交消息；这也适用于搜索框、命令面板和重命名输入框。

```html
<form id="chat-form">
  <label for="chat-input">消息</label>
  <textarea id="chat-input" placeholder="输入消息，Shift+Enter 换行"></textarea>
  <button type="submit">发送</button>
</form>
<script>
const textarea = document.getElementById('chat-input');
const form = document.getElementById('chat-form');
textarea.addEventListener('keydown', (event) => {
  if (event.key !== 'Enter' || event.shiftKey) return;
  // 先让输入法完成候选确认；不要阻止它的默认行为。
  if (event.isComposing || event.keyCode === 229) return;
  event.preventDefault();
  form.requestSubmit();
});
</script>
```

本版调整了上游示例的检查顺序：先排除组合输入，再对实际提交阻止默认行为。单行输入框不需要 `Shift+Enter` 换行分支。保留真实发送按钮、标签和原生表单路径；没有自定义 Enter 处理器的普通表单不必额外拦截。

兼容与降级：上游指出部分 Safari 的事件顺序可能导致确认候选时 `isComposing` 已恢复为 false，故示例保留仅在 Enter 分支使用的 `keyCode === 229` 兼容判断。`keyCode` 已废弃，但这里是有意的兼容补充。不能据此笼统断言所有 Safari 都不支持 `isComposing`。禁用废弃 API 的项目可基于 `compositionend` 的 `event.timeStamp` 窗口处理，但可能吞掉快速提交，必须在目标环境实测。

检查：真实中文输入法选词不发送；结束组合后 Enter 只发送一次；Shift+Enter 换行；按钮仍能发送。合成键盘事件通过不等于真实 IME 已通过验收。
