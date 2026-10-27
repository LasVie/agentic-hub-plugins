# 根据子元素状态设置父容器样式

> 修改声明：2026-10-27，由 Gan Mingrui 维护的 JiuwenSwarm 适配版；依据 GoogleChrome Modern Web Guidance 0.0.196 同名指南翻译、节选及修正示例。这是中文精选改编，不是完整逐字译本。

来源：[style-parent-with-has](https://github.com/GoogleChrome/modern-web-guidance/blob/4f2b13e25c5815b3f080ca0d983e828d96561a0f/skills/modern-web-guidance/guides/css/style-parent-with-has.md)。获取日期：2026-10-27。下文浏览器版本来自固定上游快照，不代表实时支持；上线前按项目目标浏览器核实并做特性检测。

使用 `.field-group:has(input:user-invalid)` 根据输入状态装饰祖先。范围限定到具体表单分组，避免用 `body:has(...)` 扫描大范围 DOM。`:has()` 与 `:user-invalid` 是两个不同能力，必须分别检测，不能拿后者的支持版本证明前者兼容。

```css
.field-group { border-inline-start: 4px solid #888; }
.field-group.has-error-fallback { border-inline-start-color: #b00020; }
@supports selector(:has(*)) {
  .field-group:has(input:user-invalid) { border-inline-start-color: #b00020; }
}
```

兼容与降级：本节上游只列出 `:user-invalid` 的版本，未完整列出 `:has()` 的版本；因此本包不自动推断 `:has()` 的最低版本。用 `CSS.supports('selector(:has(*))')` 和 `CSS.supports('selector(:user-invalid)')` 分开检测。需要降级时，在用户交互后用 `input.validity.valid` 和已触碰状态维护父容器类；不要在首次呈现时把所有必填项染红。

同步处理 `blur`、修正输入和 `reset`，重置时清理父级错误类及 `aria-invalid`。保留文字提示或图标，不只依赖颜色；CSS 状态不会自动同步 ARIA。实现前同时读取 `validate-input-after-interaction`。

检查：分别模拟不支持两个选择器的环境；验证首次显示、提交失败、修改正确以及重置四种状态。
