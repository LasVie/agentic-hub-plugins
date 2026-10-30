# 离线光学实验室 v1.0.0：人工测试

任务 `AH-20261030-offline-optics-lab`；候选 `CAND-EXT-003`；负责人 Cai Zhenze。
本指南保留原测试步骤。Cai Zhenze 已于2026-10-30在当前对话中明确确认本版本人工测试通过；详见 TEST_REPORT.md。仅授权GitHub交付，不创建Release或执行Hub操作。

## 安装与入口

测试站点：http://127.0.0.1:6393/ 。这是已有隔离实例，后端端口29310。
在「扩展 → 我的扩展」中确认「离线光学实验室」1.0.0已安装/启用。若需要重新导入，选择「创建 → 上传文件创建」，使用：

`/Users/IDLE_And_R/Downloads/Huawei/agentic-hub-plugins/dist/offline-optics-lab/1.0.0/offline-optics-lab-1.0.0-workswarm.zip`

原生测试ZIP SHA-256：`5634e3e37c9a53920e59567cd81bce9df42677e18944ba0b2f539b9602785511`

对应 Agentic Hub 标准外包装为：

`/Users/IDLE_And_R/Downloads/Huawei/agentic-hub-plugins/releases/agent-plugin/offline-optics-lab/1.0.0/offline-optics-lab-1.0.0.zip`

标准ZIP SHA-256：`a45ab514eb845631a3cc6855532888368ab134b81af60fee4e66bdecc8fb1a6f`

两个ZIP外层不同，内层载荷相同。精确SHA-256见同目录 `package-verification.json`；请保留测试版本与摘要。不要用标准外包装代替原生测试ZIP；不要上传到Hub。

## 可复制到 WorkSwarm 的测试请求

```text
请只使用「离线光学实验室」的真实工具测试 v1.0.0。不要编写替代工具、生成猜测光路或修改宿主、模型、其他插件。

1. 实际调用 simulate_optical_scene，scene参数为：
{"schema_version":1,"title":"人工测试：平行光束聚焦","objects":[{"id":"光束","type":"Beam","p1":{"x":100,"y":230},"p2":{"x":100,"y":420},"brightness":1,"rayCount":9},{"id":"透镜","type":"IdealLens","p1":{"x":400,"y":150},"p2":{"x":400,"y":500},"focalLength":150},{"id":"焦平面","type":"Detector","p1":{"x":550,"y":100},"p2":{"x":550,"y":550},"bins":20,"twoSided":true}]}

展示实际 ok、version、emitted_rays、segment_count、探测器power/hits和截断标志。预期9条发射光线、27段、power约1、hits=9，但以实际返回为准；工具只预览前12段，不要把预览截断等同引擎截断。

2. 我明确授权使用以下专用目录启动仅本机可访问的光学实验室：
/Users/IDLE_And_R/Downloads/Huawei/agentic-hub-plugins/dist/offline-optics-lab/1.0.0/manual-workspace
实际调用 local_optics_lab，action=start，workspace=上述完整路径，confirmed=true。
再对同一目录调用action=status。展示真实版本、running、两次session_id是否相同和完整URL。保留已有场景，不自动覆盖或删除。

3. 保持服务运行，指导我在独立Chrome标签页打开实际URL，人工测试以下操作。不要把计算成功、服务启动或AI操作描述成人工测试通过。工具不可用、版本不符或失败时如实停止，不制造替代结果。
```

## 浏览器人工验收

1. **聚焦与编辑**：选「平行光束聚焦」，点击「追迹光路」。观察光线汇聚和探测器分布。选择透镜，把焦距150改为300：旧结果必须立即清除；重新追迹后焦点与分箱分布应改变。再拖动端点或用坐标输入修改几何，检查图形与数值一致。
2. **折射/全内反射/组合**：切换折射示例，修改折射率并追迹；观察反射和透射两条分支。选择全内反射示例，观察只有反射光。组合示例应显示小功率分支截断及lost_power提示，不能声称完全收敛。
3. **保存/恢复**：为场景取中文名，点击「保存场景」。若已有记录，先导出保留并确认是否替换。刷新后应恢复元件和参数，结果需重新计算。
4. **导出/导入**：导出场景JSON和本次探测器CSV；检查中文、数值和分箱。导入刚导出的JSON，再追迹应得到相同结果。任意上游JSON不在兼容范围。
5. **失败边界**：将光源两个端点改为相同位置，追迹应明确报错、清除旧结果并禁止CSV导出；恢复参数后可继续。不要将错误解释成零光强。

请使用真实页面和真实工具返回截图，包含插件名/版本、修改后的光路、探测器读数或保存结果。截图请隐藏地址栏：完整本机URL包含访问凭据。完成后明确告知本版本测试通过或列出失败；在确认前不进行GitHub交付。

服务空闲约30分钟自动关闭。需要时可由真实工具重新启动。无需改变任何模型配置，测试过程中涉及的模型使用由用户自行控制；本次自动验证没有发起模型调用。

## 适用边界

这是可编辑的有界二维几何光学数值实验，不是完整上游网站。支持理想直镜/薄透镜、均匀玻璃、光源和透明探测器；不支持衍射、干涉、三维、曲面、重叠玻璃或工程认证。功率带方向符号且为相对单位。需要已有Python3.11+、Node18+及桌面浏览器；插件不会安装依赖或修改宿主。

## 自动验证的未覆盖项

浏览器文件选择器自动化超时，因此未宣称JSON重新导入界面已通过；导出的真实JSON已由同一引擎校验并重新追迹通过。请人工重点检查第4项的导入，以及直接鼠标拖动。未运行用户/模型会话；工具注册与调用是在独立真实SDK中验证，和实际运行宿主的安装/连接检查分开记录。
