---
name: independent-timezone-review
description: 先凭原始案例独立复算，再比对实际规划与时区数据指纹。
---

从 skill_tool 返回的本成员技能路径定位 tools/verify.py。先只读取已确认的原始案例。运行 python3 -B 及 baseline --input 原始案例 --output 全新基线的绝对路径，此时不得读取规划结果。实算后交接实际路径，提示主理人解除规划前置任务。
收到规划后，用同一随包脚本作 compare --input 原始案例 --intake 回执 --baseline 基线 --plan 规划 --output 新复核报告。独立程序采用 UTC 枚举与窗口分钟掩码。核对实际输出、状态和输入指纹，交接真实复核文件。若存在不一致或重要来源疑问，明确指出，不能以同意替代。
