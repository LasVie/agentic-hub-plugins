# 动画展开到内容自然高度

> 修改声明：2026-10-27，由 Gan Mingrui 维护的 JiuwenSwarm 适配版；依据 GoogleChrome Modern Web Guidance 0.0.196 同名指南翻译、节选及修正示例。这是中文精选改编，不是完整逐字译本。

来源：[animate-to-intrinsic-sizes](https://github.com/GoogleChrome/modern-web-guidance/blob/4f2b13e25c5815b3f080ca0d983e828d96561a0f/skills/modern-web-guidance/guides/css/animate-to-intrinsic-sizes.md)。获取日期：2026-10-27。下文浏览器版本来自固定上游快照，不代表实时支持；上线前按项目目标浏览器核实并做特性检测。

`interpolate-size: allow-keywords` 可让固定长度与固有尺寸关键字之间发生插值。必须显式启用；不能直接在 `min-content` 与 `max-content` 等两个关键字之间插值。

```css
.expandable {
  interpolate-size: allow-keywords;
  block-size: 0;
  overflow: hidden;
  transition: block-size .3s ease;
}
.expandable.is-expanded { block-size: auto; }
@media (prefers-reduced-motion: reduce) {
  .expandable { transition: none; }
}
```

兼容与降级：上游将 `interpolate-size` 和 `calc-size()` 标为有限支持，列出 Chrome/Edge 129，Firefox/Safari 未支持。没有动画的即时展开是合法降级。使用 `calc-size()` 时先写普通 `auto` 等值，因为旧浏览器会忽略整个未知声明。

交互必须同步按钮的 `aria-expanded`。尺寸为零不会自动移除可聚焦子元素；收起时管理焦点、`inert` 或 `hidden`，展开前恢复。不要只等 `transitionend` 才更新隐藏状态：减少动态效果、零时长或被取消的动画可能不发出事件。这是本适配版对原示例的补充修正。

检查：长短内容切换、键盘焦点、快速连续点击，以及减少动态效果开启时的展开和收起。
