---
name: screenshot-review
description: 用已安装本机脚本为 PNG 建议脱敏框、按用户确认输出候选、独立复核后交付。
---

# 截图脱敏本机工作流

需要已安装 Swift 工具的 macOS 与本地浏览器。只处理当前授权目录的 1 至 12 张静态正常方向 PNG。原图、候选像素、OCR 原文字不读取到模型。不要上传原图与确认文件，也不要记录敏感文件名。

从本 Skill 根目录定位 `scripts/review.swift` 与 `confirm.html`。在用户授权的本轮新目录编译 Swift 源文件，指定模块缓存目录，并确认返回成功：

```sh
/usr/bin/swiftc -O -module-cache-path "$work/modules" "$skill/scripts/review.swift" -o "$work/screenshot-review"
```

由真实成员执行并保存回执。命令参数须按本机路径正确引用，阶段文件用新的路径。

| 阶段 | 命令参数（前面加本轮可执行文件） | 责任 |
|---|---|---|
| 扫描 | `scan 原图目录 扫描.json email,phone,url,account` | 脱敏员；类别可任选，`manual` 跳过自动建议 |
| 确认 | 浏览器打开安装包 `confirm.html`，选择扫描与原图 | 使用者检查每张图并保存确认 JSON |
| 候选 | `render 原图目录 扫描.json 确认.json 新候选目录` | 脱敏员按已确认框生成 PNG |
| 复核 | `verify 原图目录 扫描.json 确认.json 候选目录 新复核.json` | 复核员从原图与候选独立检查 |
| 交付 | `deliver 原图目录 扫描.json 确认.json 候选目录 复核.json 新交付目录` | 主理人核对真实回执后交付 |

工具输出只有阶段计数或中文错误，不能把原图、识别文字和手工文件内容作为模型输入。标记保留区可以防止遮盖影响必要上下文；暂缓图不进入 share/。最终由使用者核对所有可见内容后发送。
