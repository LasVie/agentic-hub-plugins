# 小屏可读的语义化数据表格

> 修改声明：2026-10-27，由 Gan Mingrui 维护的 JiuwenSwarm 适配版；依据 GoogleChrome Modern Web Guidance 0.0.196 同名指南翻译、节选及修正示例。这是中文精选改编，不是完整逐字译本。

来源：[responsive-table](https://github.com/GoogleChrome/modern-web-guidance/blob/4f2b13e25c5815b3f080ca0d983e828d96561a0f/skills/modern-web-guidance/guides/ui-atoms/responsive-table.md)。获取日期：2026-10-27。下文浏览器版本来自固定上游快照，不代表实时支持；上线前按项目目标浏览器核实并做特性检测。

保留 `<table>`、`<thead>`、`<tbody>`、`<th>` 等语义和数据关系。用有名称、键盘可聚焦的滚动区域承载宽表格；固定表头和行标题帮助用户持续识别上下文。

```html
<div tabindex="0" role="region" aria-labelledby="table-caption" class="table-wrapper">
  <table>
    <caption id="table-caption">团队成员</caption>
    <thead><tr><th scope="col">姓名</th><th scope="col">职责</th></tr></thead>
    <tbody><tr><th scope="row">小明</th><td>前端开发</td></tr></tbody>
  </table>
</div>
```

```css
.table-wrapper { overflow: auto; max-inline-size: 100%; max-block-size: min(500px, 80vh); }
table { border-collapse: separate; border-spacing: 0; }
thead { position: sticky; inset-block-start: 0; z-index: 1; background: Canvas; }
tbody th { position: sticky; inset-inline-start: 0; background: Canvas; }
```

兼容与降级：本节上游未提供完整版本表，本包不虚构最低浏览器版本。默认保留可滚动的语义表格。可再用容器查询做窄屏卡片布局，但不能只靠隐藏 `<thead>` 和 CSS 伪元素标签就认定无障碍正确；改变表格 display 后应实测目标读屏软件中的表头关系。对复杂表格，保留横向滚动通常更可控。

检查：键盘可进入并滚动区域、焦点可见、行列标题与内容对应、深浅主题下固定区域不透明。容器查询用法参阅 `size-aware-styling`。
