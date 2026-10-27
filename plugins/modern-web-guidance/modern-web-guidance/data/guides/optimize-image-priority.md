# 优先加载首屏关键图片

> 修改声明：2026-10-27，由 Gan Mingrui 维护的 JiuwenSwarm 适配版；依据 GoogleChrome Modern Web Guidance 0.0.196 同名指南翻译、节选及修正示例。这是中文精选改编，不是完整逐字译本。

来源：[optimize-image-priority](https://github.com/GoogleChrome/modern-web-guidance/blob/4f2b13e25c5815b3f080ca0d983e828d96561a0f/skills/modern-web-guidance/guides/performance/optimize-image-priority.md)。获取日期：2026-10-27。下文浏览器版本来自固定上游快照，不代表实时支持；上线前按项目目标浏览器核实并做特性检测。

先确认页面实际的 LCP 候选图片，再为最多一到两张关键图片设置 `fetchpriority="high"`。不要给所有图片提权，也不要将 LCP 图片设为 `loading="lazy"`。

```html
<!-- 首屏关键图：尺寸用于预留空间。路径需替换为项目的实际资源。 -->
<img src="/images/hero.jpg" alt="活动主题" width="800" height="400" fetchpriority="high">
<!-- 普通首屏外图片：接近视口时按正常优先级加载。 -->
<img src="/images/details.jpg" alt="活动详情" width="800" height="600" loading="lazy">
<!-- 起初隐藏的轮播图片，可使用较低优先级。 -->
<img src="/images/slide-2.jpg" alt="第二张轮播图" width="800" height="400"
     loading="lazy" fetchpriority="low">
```

普通首屏外懒加载图片不必再加 `low`，它接近视口时应及时加载。默认优先级省略属性即可。不要使用旧 `importance` 属性或 `loading="auto"`。

兼容与降级：上游记录 Fetch priority 自 2024-10-29 达到 Baseline，列出 Chrome/Edge 103、Firefox 132、Safari 17.2。不支持时属性会被忽略，浏览器使用默认调度，因此无需为这个提示属性加载 polyfill。

检查：在实际页面和网络条件下测量 LCP、资源瀑布及布局偏移；不能仅凭添加属性宣称性能已经提升。
