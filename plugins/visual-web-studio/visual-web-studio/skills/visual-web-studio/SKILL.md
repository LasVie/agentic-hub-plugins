---
name: visual-web-studio
description: 使用可视化网页搭建台的真实原生工具和本机中文工作台，保存、恢复并导出实际成果。
---
# 可视化网页搭建台
默认使用简体中文。此插件包含真实运行代码，不可用生成的示例文字代替执行。
1. 使用用户授权的已存在专用目录；缺失时先确定目录，禁止使用敏感配置或其他人的工作目录。
2. 调用 `visual_web_studio_workbench`，action=start、workspace为绝对路径；用户明确要求打开即为本次启动授权，设置confirmed=true。返回ok=true后给出实际url。
3. 用 `visual_web_studio_operate`，传workspace、confirmed、operation、arguments，读取实际结果；失败时如实说明，不得写“已通过”。
4. 操作：load {}；save {project:GrapesJS工程JSON,html:"实际页面HTML",css:"实际CSS"}。通常先打开工作台让用户在可视化画布编辑，调用load可核对真实保存内容；不要伪造工程树。
5. 交互界面、保存数据与工具共享同一专用目录。重新对话时先status，再load；服务记录属于另一安装时不得接管，换用新目录。
6. 不修改宿主、SDK、其他插件或用户全局依赖。不自动上传云端，不自动发布站点，不调用外部模型。关闭仅调用本插件workbench的stop。
