# 单页视图切换的渐进过渡

> 修改声明：2026-10-27，由 Gan Mingrui 维护的 JiuwenSwarm 适配版；依据 GoogleChrome Modern Web Guidance 0.0.196 同名指南翻译、节选及修正示例。这是中文精选改编，不是完整逐字译本。

来源：[same-document-transitions](https://github.com/GoogleChrome/modern-web-guidance/blob/4f2b13e25c5815b3f080ca0d983e828d96561a0f/skills/modern-web-guidance/guides/ui-behaviors/same-document-transitions.md)。获取日期：2026-10-27。下文浏览器版本来自固定上游快照，不代表实时支持；上线前按项目目标浏览器核实并做特性检测。

用 `document.startViewTransition()` 包裹 DOM 更新，使用唯一的 `view-transition-name` 关联前后视图中的共享元素。同一快照内不能有两个元素使用相同名称。只为主要内容建立共享动画，结束后清理临时名称。

```js
async function navigate(updateDOM, focusNewHeading) {
  const reduceMotion = matchMedia('(prefers-reduced-motion: reduce)').matches;
  if (!document.startViewTransition || reduceMotion) {
    await updateDOM();
    focusNewHeading();
    return;
  }
  const transition = document.startViewTransition(updateDOM);
  try {
    await transition.updateCallbackDone;
    focusNewHeading();
    await transition.finished;
  } catch (error) {
    // 动画失败不等于 DOM 更新失败；不要重复执行有副作用的更新。
    // 调用者应按实际更新结果报告错误。
    throw error;
  }
}
```

兼容与降级：上游记录同文档 View Transitions 自 2025-10-14 达到 Baseline，列出 Chrome/Edge 111、Firefox 144、Safari 18。没有该 API 时直接更新 DOM，不能让导航依赖动画。减少动态效果时也走直接更新路径。

新视图标题可用 `tabindex="-1"` 接收程序焦点。框架适配时要等实际 DOM 更新完成；不要把状态 setter 的调用当成 DOM 已提交。文字过渡可用 `width: fit-content` 减少拉伸。跨文档过渡不在本节范围内。

检查：正常动画、重复名称、API 缺失、减少动态效果和键盘焦点。视觉过渡成功不代表路由或数据加载已成功。
