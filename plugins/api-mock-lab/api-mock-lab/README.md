# 接口模拟与联调台 1.0.3

上游：Mockoon → 接口模拟与联调台 → `api-mock-lab`。

## 安装与打开
在WorkSwarm「扩展」导入本插件原生伴随ZIP并安装；Hub格式ZIP位于仓库releases目录。两种包装的内层运行文件完全一致。
在新任务中选择本插件，指定一个已存在的专用工作目录，要求“打开接口模拟与联调台”。原生工具返回本机链接；在浏览器操作中文工作台。

需要宿主SDK与Node.js22+。macOS优先使用PATH中的Node，或WorkSwarm应用自带Node；可用JIUWEN_NODE_BINARY指定已有可执行文件。不自动安装或修改系统依赖。

## 真实操作
demo {}；save {spec:{name,routes:[{method:"get",path:"/api/products",status:200,body:{...}}]}}；start {scenario:"normal"|"slow"|"error"}；probe {method:"GET",path:"/api/products"}；stop {}；import-openapi {source:"规范文本"}。响应模板/文件/代理/回调禁用。

## 保存与边界
数据仅保存到用户选择目录下的`.api-mock-lab`。使用界面的保存/导出操作获取真实文件；不要把聊天中的说明当作执行证据。关闭后数据保留，可由同一安装重新打开。保存记录不兼容另一安装目录时应使用新工作目录。

本轮验证以实际TEST_REPORT为准。首版支持范围见中文界面；不承诺未测试的平台、格式或扩展。此插件不执行Agentic Hub发布。

## 许可
完整第三方许可、固定来源、组件范围见`THIRD_PARTY_NOTICES.md`和`licenses/`；原作者声明保留原文。
