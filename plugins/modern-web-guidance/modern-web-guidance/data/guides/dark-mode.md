# 跟随系统的深浅主题

> 修改声明：2026-10-27，由 Gan Mingrui 维护的 JiuwenSwarm 适配版；依据 GoogleChrome Modern Web Guidance 0.0.196 同名指南翻译、节选及修正示例。这是中文精选改编，不是完整逐字译本。

来源：[dark-mode](https://github.com/GoogleChrome/modern-web-guidance/blob/4f2b13e25c5815b3f080ca0d983e828d96561a0f/skills/modern-web-guidance/guides/visual-design/dark-mode.md)。获取日期：2026-10-27。下文浏览器版本来自固定上游快照，不代表实时支持；上线前按项目目标浏览器核实并做特性检测。

先在文档 head 声明支持的配色，再把 `color-scheme` 作用于 `:root` 或 `html`，使浏览器表单控件、滚动条和页面背景跟随主题。只设在 body 不能保证全视口界面同步。

```html
<meta name="color-scheme" content="light dark">
```

```css
:root { color-scheme: light dark; --page-bg: #fff; --page-fg: #222; }
@media (prefers-color-scheme: dark) {
  :root { --page-bg: #181818; --page-fg: #eee; }
}
@supports (color: light-dark(white, black)) {
  :root { --page-bg: light-dark(#fff, #181818); --page-fg: light-dark(#222, #eee); }
}
body { background: var(--page-bg); color: var(--page-fg); }
```

兼容与降级：上游记录 `color-scheme` 自 2022-02-03 达到 Baseline，列出 Chrome/Edge 98、Firefox 96、Safari 13；`light-dark()` 颜色值自 2024-05-13 达到 Baseline，列出 Chrome/Edge 123、Firefox 120、Safari 17.5。两者分别检测；媒体查询配合普通变量提供颜色降级。本节不把颜色值支持推断成图片值支持。

只有用户需要时才添加手动主题开关。手动覆盖必须同步根元素配色及降级变量；如果 JS 读取 `matchMedia`，还要处理其 `change` 事件。子树配色覆盖不一定自动重新计算已经继承的颜色变量，应重新应用相关属性。

上游提示 Safari 的 iframe 配色传播存在差异；需要准确同步时，在受控父子页面之间传递显式主题并验证消息来源。主题和滚动条配色均需检查对比度，不能只相信浏览器自动处理。不要为美化原生控件轻易重新实现控件。

检查：首次加载闪白、系统主题切换、原生输入控件、手动覆盖以及旧环境降级。本节是核心配色精选，未迁移上游全部图片、滚动条及 iframe 示例。
