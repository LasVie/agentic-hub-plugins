# 延后渲染首屏外复杂内容

> 修改声明：2026-10-27，由 Gan Mingrui 维护的 JiuwenSwarm 适配版；依据 GoogleChrome Modern Web Guidance 0.0.196 同名指南翻译、节选及修正示例。这是中文精选改编，不是完整逐字译本。

来源：[defer-rendering-heavy-content](https://github.com/GoogleChrome/modern-web-guidance/blob/4f2b13e25c5815b3f080ca0d983e828d96561a0f/skills/modern-web-guidance/guides/performance/defer-rendering-heavy-content.md)。获取日期：2026-10-27。下文浏览器版本来自固定上游快照，不代表实时支持；上线前按项目目标浏览器核实并做特性检测。

`content-visibility: auto` 适合初始视口之外、相对独立且内部复杂的区块。不要对首屏关键内容使用它，否则额外的可见性判断可能反而拖慢首屏。

```css
.heavy-section-deferred {
  content-visibility: auto;
  contain-intrinsic-size: auto none auto 150px;
}
```

估计尺寸应根据实际布局调整。`auto` 允许浏览器记住渲染后的尺寸，初始占位值帮助减少滚动条跳动。不要用零高度占位替代合理估计。

`content-visibility: hidden` 会隐藏内容，也会影响辅助技术和页面内查找，不能拿它实现“隐藏但仍可搜索”的要求。`hidden="until-found"` 属于另一类能力，未纳入本版指南。

兼容与降级：上游记录 `content-visibility` 自 2025-09-15 达到 Baseline，列出 Chrome/Edge 108、Firefox 130、Safari 26。旧浏览器忽略 `auto` 只是失去性能优化；若业务使用 `hidden`，必须提供真正隐藏内容的默认样式，例如先 `display: none`，再通过 `@supports` 增强。

检查：键盘能否顺序访问首屏外内容、辅助技术能否读到需要的内容、滚动位置是否稳定。插件提供建议，不替代真实性能和无障碍测试。
