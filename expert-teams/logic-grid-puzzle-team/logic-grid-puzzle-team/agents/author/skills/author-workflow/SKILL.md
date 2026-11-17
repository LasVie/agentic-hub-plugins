---
name: author-workflow
description: 依据用户确认的主题和词表编制受限配对谜题，维护线索编号并修订歧义。
---

使用宿主已有的命令执行工具运行 Python3；从本技能文件定位成员根目录（../..），不能假定当前工作目录或硬编码安装路径。所有参数路径均加安全引用。脚本不是命令注册承诺，先检查工具确实可用。
# 编制规范

输出严格 JSON：schema_version 为 "1.0"，puzzle_id、title、categories、clues。三类 categories 各含 id、label、items；items 各含 id、label。线索含 id、op、left、right，left/right 各含 category、item；op 只能 match/not_match，左类别在 categories 中先于右类别。勿添加自造字段。词表标签禁止控制字符和【】；避免含“与”或以“不”结尾等导致受控句式歧义的词汇。给模型员明确预设配对。需要精确字段时读取随包 examples/campus-model.json（从团根定位），不要根据记忆编 schema。最多两轮修订。
