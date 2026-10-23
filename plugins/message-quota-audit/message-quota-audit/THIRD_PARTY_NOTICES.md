# 第三方来源与修改

- 上游：https://github.com/deepsleepAquarium/dsh-whale-post/tree/d78a82699722f0da6ae3d2b4cbdbaa411f2f67af/packages/gate
- 包版本dsh-whale-post-gate0.6.1；固定提交d78a82699722f0da6ae3d2b4cbdbaa411f2f67af。
- 原版权：**Copyright (c) 2026 The Tank**；完整MIT版权/许可条件/免责声明在 `licenses/whale-post-gate/LICENSE`，原字节保留。根与包LICENSE相同，无适用NOTICE或嵌套许可。
- 原index.js开头完整注释逐字保留于 `licenses/whale-post-gate/UPSTREAM_HEADER.txt`，属于历史来源记录，不是当前功能保证。
- 实际复用：index.js回执词/单位计量/桶配额/同对窗口/回复深度及对账需求 → runtime/quota.py；README接口语义 → README.md的受限说明。
- 修改：Python标准库SQLite事务、严格输入/权限边界、幂等/冲突拒绝、显式时区、损坏数据失败、只读预览/对账、中文openJiuwen工具。不是native或完全原创声明。
- 未搬入其他包、DSH/Cordis运行时、发送/总线/验证模块、费用/force/手机/群折算、品牌图标、字体、媒体、数据或二进制。上游本包没有目录描述所称的静默时段功能。
- 宿主SDK、Python、SQLite和系统时区资料仅为外部运行依赖，未重新分发。本说明不决定团队代码统一许可，不暗示上游背书。
