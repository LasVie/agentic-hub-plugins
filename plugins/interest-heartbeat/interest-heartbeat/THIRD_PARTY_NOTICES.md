# 第三方来源和修改说明

## dsh-heartbeat

- 来源：https://github.com/Kanadego/dsh-heartbeat（npm `@kanadego/dsh-heartbeat`）
- 固定版本：8880365836fc4247839122aee7b542d73403a532（npm 2.0.0 的 gitHead）
- 版权：Copyright (c) 2026 Kanadego
- 许可：MIT，完整原文见 licenses/dsh-heartbeat/LICENSE

涉及文件：

- `runtime/engine.py` 中的分寸闸门判定顺序与“说完再记账”规则、HH:MM 跨午夜窗口算法、素材池规则（标签 TTL、同话题合并、分类上限与评分淘汰、用后退役、冷板凳、归档上限）、闲逛时段与焦点冷却，以及默认参数，改编自上游 `src/gate/gate.ts`、`src/core/time-window.ts`、`src/seeds/pool.ts`、`src/seeds/types.ts`、`config/policy.json`、`config/interests.json`（文件头已注明修改）。
- `skills/interest-heartbeat/SKILL.md` 的一跳流程（维护 → 闲逛 → 闸门 → 备料 → 投递 → 留痕）与“沉默必带原因、开口要有来处”的原则改编自上游 README.md 与 DESIGN.md。

修改摘要：由 DeepSeek Harness / Cordis 插件（TypeScript，仅 Windows）改写为 WorkSwarm 原生 Python 工具，由宿主定时任务驱动；去掉全屏截图、前台窗口与在场探测（PowerShell）、DPAPI 加密、设置卡界面、周报、摘抄本与换机迁移；忙闲判定改为用户声明的忙时窗口；新增暂停开关；默认兴趣改为通用条目。工具封装、README 与测试为本适配新写。

未声明上游作者认可本适配。DeepSeek 是其权利人的商标，本插件与之无关。
