# 点击遮罩关闭模态弹窗

> 修改声明：2026-10-27，由 Gan Mingrui 维护的 JiuwenSwarm 适配版；依据 GoogleChrome Modern Web Guidance 0.0.196 同名指南翻译、节选及修正示例。这是中文精选改编，不是完整逐字译本。

来源：[light-dismiss-a-dialog](https://github.com/GoogleChrome/modern-web-guidance/blob/4f2b13e25c5815b3f080ca0d983e828d96561a0f/skills/modern-web-guidance/guides/ui-behaviors/light-dismiss-a-dialog.md)。获取日期：2026-10-27。下文浏览器版本来自固定上游快照，不代表实时支持；上线前按项目目标浏览器核实并做特性检测。

用原生 `<dialog>` 和 `showModal()` 提供模态行为、顶层显示及焦点约束。`closedby="any"` 允许点击外部和关闭请求；`closerequest` 仅允许关闭请求及程序关闭；`none` 仅允许程序关闭。非模态 `show()` 没有同样的遮罩行为。

```html
<dialog id="myDialog" closedby="any" aria-labelledby="dialogTitle">
  <form method="dialog">
    <h2 id="dialogTitle">反馈</h2>
    <p>可以点击遮罩、按 Esc 或使用关闭按钮。</p>
    <button type="submit">关闭</button>
  </form>
</dialog>
<button id="openDialog">打开反馈</button>
<script>
const dialog = document.getElementById('myDialog');
document.getElementById('openDialog').addEventListener('click', () => dialog.showModal());
if (!('closedBy' in HTMLDialogElement.prototype)) {
  dialog.addEventListener('click', (event) => {
    if (event.target !== dialog) return;
    const rect = dialog.getBoundingClientRect();
    const inside = rect.top <= event.clientY && event.clientY <= rect.bottom &&
      rect.left <= event.clientX && event.clientX <= rect.right;
    if (!inside) dialog.close();
  });
}
</script>
```

兼容与降级：`closedby` 在上游快照中仍为有限支持，列出 Chrome/Edge 134、Firefox 141，Safari 未支持。上面的特性检测与边界判断用于降级；点击弹窗内部空白不应被误判为遮罩。`<dialog>` 本身的支持需独立确认，完全不支持时采用普通页面表单等可用入口。

检查：遮罩、内部文字、内部空白、关闭按钮、Esc 和关闭后焦点恢复。业务逻辑根据需求监听 `cancel` 或 `close`，不要把所有关闭都当成点击事件。
