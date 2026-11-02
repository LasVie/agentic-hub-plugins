# 第三方许可与来源

本插件的数值引擎为 Astronomy Engine 2.1.19，由 Don Cross 开发。
固定来源：https://github.com/cosinekitty/astronomy/tree/865d3da7d8112bbc7911238052c6af4aaf877181

`runtime/astronomy.py` 原样复制自 `source/python/astronomy/astronomy.py`，未修改；保留原始完整 MIT 文件头（Copyright (c) 2019–2025 Don Cross）。
根目录完整 MIT 文本见 [LICENSE](licenses/astronomy-engine/LICENSE)，Python 子目录的原始文本（2019–2022）见 [PYTHON_LICENSE](licenses/astronomy-engine/PYTHON_LICENSE)。原年份和免责声明均保留。

中文界面、参数校验、工具适配、限时进程和会话管理由本项目另行编写。会话边界沿用本仓维护的离线服务机制，不改动其他插件。没有复制上游网页、品牌图像、星图、字体、示例数据或第三方依赖。引擎自带系数在上述获许可的源码中；运行仅依赖 Python 标准库。

MIT 不代表原作者为本插件背书，不代表数值结果无误。上游维护活跃度下降；本插件只提供受限观测规划，具体范围和已知精度差异见 README。本项目自身的统一许可证由项目负责人决定，此说明不为本项目全部代码另行选择许可证。
