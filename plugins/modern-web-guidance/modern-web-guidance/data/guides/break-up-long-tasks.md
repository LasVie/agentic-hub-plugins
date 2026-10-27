# 拆分阻塞主线程的长任务

> 修改声明：2026-10-27，由 Gan Mingrui 维护的 JiuwenSwarm 适配版；依据 GoogleChrome Modern Web Guidance 0.0.196 同名指南翻译、节选及修正示例。这是中文精选改编，不是完整逐字译本。

来源：[break-up-long-tasks](https://github.com/GoogleChrome/modern-web-guidance/blob/4f2b13e25c5815b3f080ca0d983e828d96561a0f/skills/modern-web-guidance/guides/performance/break-up-long-tasks.md)。获取日期：2026-10-27。下文浏览器版本来自固定上游快照，不代表实时支持；上线前按项目目标浏览器核实并做特性检测。

长循环会阻塞输入与渲染。按时间预算分批处理，并把控制权交还浏览器。`await Promise.resolve()` 只排入微任务，不等同于让出主线程进行下一次渲染。

```js
async function processLargeArray(items, processItem) {
  let deadline = performance.now() + 50;
  for (const item of items) {
    processItem(item);
    if (performance.now() >= deadline) {
      if (globalThis.scheduler && typeof globalThis.scheduler.yield === 'function') {
        await globalThis.scheduler.yield();
      } else {
        await new Promise(resolve => setTimeout(resolve, 0));
      }
      deadline = performance.now() + 50;
    }
  }
}
```

兼容与降级：上游将 Scheduler API 标为有限支持，列出 Chrome/Edge 129、Firefox 142，Safari 未支持。因此保留 `setTimeout` 降级。这里的 50ms 是示例预算；单个 `processItem` 如果已耗时很长，外围分批不能解决，需要拆分内部工作或另行考虑 Worker。

检查：真实交互是否可以响应、结果顺序与数量是否不变、异常是否向调用方传播。若工作会被取消，还需由业务代码增加取消检查。本插件不自动运行项目中的计算。
