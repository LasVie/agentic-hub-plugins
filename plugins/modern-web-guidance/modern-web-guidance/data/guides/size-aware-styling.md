# 容器宽度驱动的组件布局

> 修改声明：2026-10-27，由 Gan Mingrui 维护的 JiuwenSwarm 适配版；依据 GoogleChrome Modern Web Guidance 0.0.196 同名指南翻译、节选及修正示例。这是中文精选改编，不是完整逐字译本。

来源：[size-aware-styling](https://github.com/GoogleChrome/modern-web-guidance/blob/4f2b13e25c5815b3f080ca0d983e828d96561a0f/skills/modern-web-guidance/guides/css/size-aware-styling.md)。获取日期：2026-10-27。下文浏览器版本来自固定上游快照，不代表实时支持；上线前按项目目标浏览器核实并做特性检测。

组件应根据所在容器的空间调整布局，而非只看整个视口。先在外层设置 `container-type: inline-size`，再让内层组件响应 `@container`；被查询的容器不能靠自己的尺寸查询来改变自身。

```css
.card-container { container-type: inline-size; }
.card { display: flex; flex-direction: column; gap: 1rem; }
@container (min-width: 400px) {
  .card { flex-direction: row; align-items: center; }
}
```

容器查询的尺寸隔离会影响固有尺寸计算。不要为了宽度查询盲目使用 `container-type: size`，后者还要求明确处理高度。

兼容与降级：上游记录尺寸容器查询自 2023-02-14 达到 Baseline，最低版本为 Chrome/Edge 105、Firefox 110、Safari 16。旧浏览器保留默认纵向布局即可；必要时可用视口媒体查询近似，但不能声称它等价于容器查询。

检查：把同一张卡片分别放进窄侧栏和宽内容区；确认窄容器不溢出，旧环境仍可阅读和操作。
