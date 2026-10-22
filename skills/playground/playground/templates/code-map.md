# 代码结构图模板

> 修改说明：2026-10-22，由 Anthropic Playground 原模板翻译并适配为简体中文；保留技术标识、来源和 Apache-2.0 许可。所有界面标签、提示词、帮助和复制状态默认中文；源材料按原值显示。来源见 ../THIRD_PARTY_NOTICES.md，完整许可见 ../licenses/claude-plugins-official/LICENSE。

当探索页用于可视化代码库架构、组件关系、数据流、分层或系统架构，并允许通过评论提供反馈时，使用本模板。

## 布局

左侧包含视图预设、层级开关、带颜色的关系类型筛选，以及评论列表和删除按钮。右侧上方使用 SVG 画布显示节点与连线，附缩放控件，左下角放图例；下方显示提示词及“复制提示词”按钮。窄屏下按内容顺序堆叠。

用户点击组件添加评论，评论进入生成的提示词。层级及关系筛选帮助聚焦系统局部，不应删除已保存评论。

## 代码图控件

| 取舍 | 控件 | 示例 |
| --- | --- | --- |
| 系统视图 | 预设按钮 | 完整系统、对话流程、数据流、智能体系统 |
| 可见层级 | 复选框 | 客户端、服务端、SDK、数据、外部依赖 |
| 关系类型 | 带颜色提示的复选框 | 数据流（蓝）、工具调用（绿）、事件（红） |
| 组件反馈 | 点击评论对话框 | 显示反馈输入框 |
| 缩放 | 放大/缩小/重置按钮 | 缩放 SVG 以查看细节 |

## 画布渲染

使用 `<svg>` 动态创建节点与路径：

- 节点：圆角矩形、中文标题及作为副标题的真实文件路径。
- 关系：带箭头的贝塞尔曲线，按类型设置样式。
- 分层：按纵向分带排列，例如 `y: 30–80` 为客户端，`y: 130–180` 为服务端。
- 点击评论：点击节点 → 打开对话框 → 保存 → 显示节点标记。
- 筛选：按层级显示节点，按关系类型显示连线；仅渲染两端均可见的连线。

```javascript
const nodes = [
  { id: 'api-client', label: 'API 客户端', subtitle: 'src/api/client.ts',
    x: 100, y: 50, w: 140, h: 45, layer: 'client', color: '#dbeafe' },
];
const connections = [
  { from: 'api-client', to: 'server', type: 'data-flow', label: 'HTTP' },
  { from: 'server', to: 'db', type: 'data-flow' },
];
function renderDiagram() {
  const visibleNodes = nodes.filter(n => state.layers[n.layer]);
  const visibleIds = new Set(visibleNodes.map(n => n.id));
  // 先画可见节点之间的连线，再画节点
  connections.filter(c => visibleIds.has(c.from) && visibleIds.has(c.to)).forEach(drawConnection);
  visibleNodes.forEach(drawNode);
}
```

通过 `createElementNS` 创建 SVG 元素；标题、路径与评论用 `textContent` 设置，不将不可信文本直接拼接到 `innerHTML`。

## 关系类型与样式

定义 3–5 种容易区分的关系；技术类型值保持不变，可见标签使用中文：

| 类型值 | 中文标签/颜色 | 样式 | 用途 |
| --- | --- | --- | --- |
| `data-flow` | 数据流，蓝 `#3b82f6` | 实线 | 请求/响应、数据传递 |
| `tool-call` | 工具调用，绿 `#10b981` | 虚线 `6,3` | 函数或 API 调用 |
| `event` | 事件，红 `#ef4444` | 短虚线 `4,4` | 异步事件、发布/订阅 |
| `skill-invoke` | Skill 调用，橙 `#f97316` | 长虚线 `8,4` | 插件/Skill 激活 |
| `dependency` | 依赖，灰 `#6b7280` | 点线 | `import` / `require` 关系 |

使用 SVG marker 画箭头：

```html
<marker id="arrowhead-blue" markerWidth="8" markerHeight="6" refX="7" refY="3" orient="auto">
  <polygon points="0 0, 8 3, 0 6" fill="#3b82f6"/>
</marker>
```

## 评论系统

1. 点击节点，打开包含组件名、路径和输入框的对话框。
2. 保存评论，将其加入列表，并用有颜色的边框标记节点。
3. 侧栏列出组件名、评论预览及删除按钮。
4. 删除评论时同步更新节点标记和提示词。

记录完整组件背景：

```javascript
state.comments.push({
  id: Date.now(),
  target: node.id,
  targetLabel: node.label,
  targetFile: node.subtitle,
  text: userInput
});
```

对话框需要关联标签、可见焦点、键盘关闭、关闭后返回触发节点；节点提供键盘入口。评论不得因切换视图或筛选而丢失。

## 代码图提示词

将真实系统背景与用户评论组合：

```text
这是[项目名称]的架构，本次聚焦[可见层级]。

对具体组件的反馈：

**API 客户端**（src/api/client.ts）：
我想在这里加入带指数退避的重试逻辑。

**数据库管理器**（src/db/manager.ts）：
能否加入连接池？当前实现每次请求都创建连接。

**认证中间件**（src/middleware/auth.ts）：
这里应校验 JWT 并提取用户上下文。
```

只包含用户实际添加的评论；未显示完整系统时说明可见层级。示例不是对真实项目的事实判断。页面仅生成让用户复制回会话的指令，不自行修改文件或发送消息。

## 预填真实资料

先阅读具体代码库，再填入 15–25 个附真实路径的关键组件，以及依据真实导入/调用确定的 20–40 条关系。按界面、API、业务逻辑、数据、外部依赖分组，以水平带和一致间距排列。提供“完整系统”“仅前端”“仅后端”“数据流”等 3–5 个适用预设；资料不足时明确说明。

## 分层配色（浅色节点）

| 层级 | 填充色 | 内容 |
| --- | --- | --- |
| 客户端/界面 | `#dbeafe` | React 组件、hooks、页面 |
| 服务端/API | `#fef3c7` | Express 路由、中间件、处理器 |
| SDK/核心 | `#f3e8ff` | 核心库、SDK 封装 |
| 智能体/逻辑 | `#dcfce7` | 业务逻辑、智能体、处理器 |
| 数据 | `#fce7f3` | 数据库、缓存、存储 |
| 外部 | `#fbcfe8` | 第三方服务、API |

## 示例主题

- 代码库架构探索：模块、导入、数据流。
- 微服务：服务、队列、数据库、API 网关。
- React 组件树：组件、hooks、context、state。
- API 架构：路由、中间件、控制器、模型。
- 智能体系统：提示词、工具、Skill、子智能体。
- 数据管道：来源、转换、去向、调度。
- 插件/扩展架构：核心、插件、hooks、事件。

默认使用中文标签与提示词，资源全部内联。复制成功才显示“已复制”；失败时说明失败并提供可选择的文本手动复制。
