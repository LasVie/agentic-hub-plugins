# 前端包体积透视台 1.0.4

上游：Rollup Plugin Visualizer → 前端包体积透视台 → `bundle-insight`。

## 安装与打开
在WorkSwarm「扩展」导入本插件原生伴随ZIP并安装；Hub格式ZIP位于仓库releases目录。两种包装的内层运行文件完全一致。
在新任务中选择本插件，指定一个已存在的专用工作目录，要求“打开前端包体积透视台”。原生工具返回本机链接；在浏览器操作中文工作台。

需要宿主SDK与Node.js22+。macOS优先使用PATH中的Node，或WorkSwarm应用自带Node；可用JIUWEN_NODE_BINARY指定已有可执行文件。不自动安装或修改系统依赖。

## 真实操作
build-demo {name:"baseline",large:false}；import {name:"build1",data:真实raw-data JSON}；load {name:"build1"}；compare {before:"baseline",after:"build1"}。示例构建不代表用户项目已测试。

## 保存与边界
数据仅保存到用户选择目录下的`.bundle-insight`。使用界面的保存/导出操作获取真实文件；不要把聊天中的说明当作执行证据。关闭后数据保留，可由同一安装重新打开。保存记录不兼容另一安装目录时应使用新工作目录。

本轮验证以实际TEST_REPORT为准。首版支持范围见中文界面；不承诺未测试的平台、格式或扩展。此插件不执行Agentic Hub发布。

## 许可
完整第三方许可、固定来源、组件范围见`THIRD_PARTY_NOTICES.md`和`licenses/`；原作者声明保留原文。

## 接入已有 Vite / Rollup 项目
在你自己的项目分支中安装统计插件，保留已有配置，并将以下统计插件加到 plugins 数组末尾。工作台不会替你执行项目配置。

```sh
npm install --save-dev rollup-plugin-visualizer@7.1.1
```

```js
import { visualizer } from 'rollup-plugin-visualizer';
// 在已有 Vite / Rollup 的 plugins 数组末尾添加：
visualizer({ filename: 'bundle-stats.json', template: 'raw-data', gzipSize: true, brotliSize: true })
```

使用项目原有构建命令生成 bundle-stats.json，再在本工作台选择该文件，填写快照名并点击“导入构建统计”。构建前后分别导入不同快照名，比较同一统计口径的变化。支持 Visualizer 7.1.1 生成的含 tree、nodeParts、nodeMetas 的 raw-data，最多10 MiB、5000个模块。统计可包含项目模块路径，导入前按团队要求处理敏感路径。
