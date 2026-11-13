# a11y_scan 规则一览

规则名和 WCAG 成功标准编号沿用上游写法；“级别”是扫描结果里的“错误”或“警告”。

| 规则名 | 级别 | WCAG | 在查什么 | 常见改法 |
| --- | --- | --- | --- | --- |
| html-lang | 错误 | 3.1.1 | `.html` 文件里的 `<html>` 没有 `lang` | 写 `lang="zh-CN"`（或页面实际语言） |
| img-alt | 错误 | 1.1.1 | `<img>`（以及 `Image`、`NextImage`）没有 `alt` | 写出图片在上下文里的含义；纯装饰图写 `alt=""` |
| input-image-alt | 错误 | 1.1.1 | `<input type="image">` 没有 `alt` | 加 `alt`，说明按钮的作用 |
| form-label | 错误 | 1.3.1 / 4.1.2 | 输入框、下拉框、文本域没有 `label`、`aria-label`、`aria-labelledby` 或 `title`，也没有被 `<label>` 包住 | 用 `<label for>` 关联，或把控件放进 `<label>`；占位符不能当标签 |
| button-name | 错误 | 4.1.2 | `<button>` 没有文字，也没有 `aria-label` 等名称 | 加可见文字；只有图标时加 `aria-label` |
| link-name | 错误 | 2.4.4 / 4.1.2 | `<a>` 里没有文字，也没有名称 | 加链接文字；只有图标时加 `aria-label` |
| link-purpose | 警告 | 2.4.4 | 链接文字只有“click here”“more”“点击这里”“更多”“详情”之类 | 改成说明去向或作用的文字 |
| anchor-is-button | 错误 | 4.1.2 | 没有 `href` 的 `<a>` 带点击事件，被当按钮用 | 改用 `<button>` |
| click-no-role | 错误 | 4.1.2 | `div`、`span`、`li`、`td`、`p`、`section` 带点击事件却没有 `role` | 改用 `<button>`，或补 `role` 和 `tabindex` |
| click-no-focus | 错误 | 2.1.1 | 同上，没有 `tabindex`，键盘到不了 | 改用原生控件，或加 `tabindex="0"` |
| click-no-key | 错误 | 2.1.1 | 同上，没有键盘事件处理 | 处理 Enter 和空格；最好改用 `<button>` |
| media-autoplay | 错误 | 1.4.2 | `<video>`、`<audio>` 自动播放且没有 `muted` | 去掉自动播放，或静音并提供暂停控件 |
| video-captions | 警告 | 1.2.2 | `<video>` 里没有 `<track>` | 提供字幕轨 |
| iframe-title | 错误 | 4.1.2 | `<iframe>` 没有 `title` | 写出这个框架的内容 |
| heading-order | 警告 | 1.3.1 | 标题层级跳级（例如 h1 直接到 h3） | 按层级顺序写，样式交给 CSS |
| viewport-zoom | 错误 | 1.4.4 | viewport 里 `user-scalable=no` 或 `maximum-scale=1` | 去掉这些限制 |
| tabindex-positive | 错误 | 2.4.3 | `tabindex` 大于 0 | 改成 0 或 -1，让 DOM 顺序决定焦点顺序 |
| accesskey | 警告 | 2.1.4 | 用了 `accesskey` | 去掉，或确认不和读屏软件快捷键冲突 |
| role-no-focus | 错误 | 2.1.1 | `role` 是 button、link、checkbox、tab、menuitem、switch 的非原生元素没有 `tabindex` | 改用原生元素，或加 `tabindex` |
| focus-outline | 警告 | 2.4.7 | 行内样式去掉了焦点轮廓；`.vue`、`.svelte`、`.astro`、`.html` 里有 `outline: none` 而且全文没有 `:focus` 样式 | 保留轮廓，或提供清楚的 `:focus-visible` 样式 |

## 识别的边界

- 扫描按标签文本做匹配，不解析成 DOM，也不展开组件：自定义组件（大写开头的标签，`Image`、`NextImage` 除外）里的问题看不到；带 `{...props}` 展开的标签会跳过需要属性的检查。
- 一个标签（含属性）超过 8000 个字符，或者过深的花括号嵌套，可能识别不到。
- 文件超过 1 MB、扫描一个文件超过 10 秒、一次调用超过 60 秒，对应的文件或剩余部分会被跳过，并在结果里说明。
- 文件按 UTF-8 读取，其他编码的文件里的中文会变成乱码，但标签结构仍能识别。
- 没有发现问题不等于符合 WCAG。目标尺寸、焦点管理、动态更新、动效这些需要读代码或在浏览器里验证。
