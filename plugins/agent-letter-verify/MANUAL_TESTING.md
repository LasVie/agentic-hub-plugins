# 代理信件完整性校验 1.0.1：人工测试

任务 `AH-20261023-agent-letter-verify`，候选 `CAND-DSH-305`，负责人 Cai Zhenze。

## 测试包与环境

- WorkSwarm：<http://127.0.0.1:6385>。本插件已导入并安装，扩展 → 我的扩展 → 代理信件完整性校验，可看到一个技能和两个工具。
- 原生导入 ZIP：`/Users/IDLE_And_R/.codex/worktrees/581d/agentic-hub-plugins/dist/agent-letter-verify/1.0.1/agent-letter-verify-1.0.1-workswarm.zip`
- 原生 SHA-256：`a6260d897de78677d64500e11e41e720b940dcc0661a65d3c0576be2e60494a6`
- 市场格式 ZIP：`releases/agent-plugin/agent-letter-verify/1.0.1/agent-letter-verify-1.0.1.zip`
- 市场 SHA-256：`c195834594177edaef1516a3be7e725b75c20467454de6b80bb9d0842b64c9e6`

需要重新安装时，在扩展 → 我的扩展 → 创建 → 从文件创建中选择**原生** ZIP，再安装。本次已经通过 Extensions 本地导入接口及浏览器安装验证；操作系统文件选择器的整套上传交互尚未自动验证。

测试环境为全新独立数据目录，没有复制 Main 的账号、模型配置或凭据。模型为 `disabled-local-test`，未发送模型请求。若使用聊天进行人工测试，由你在**此实例**设置可用模型；不要复制其他环境的运行状态。也可使用下面的命令行方式，不需要模型或网络。

测试工作目录：

```text
/Users/IDLE_And_R/.codex/worktrees/581d/agentic-hub-plugins/dist/agent-letter-verify/1.0.1/test-workspace
```

该目录只有公开虚构测试信件和测试密钥，不能用于真实通信。初始 `enabled=false`、`revision=0`。不要删除或覆盖已有信任配置以制造预期结果；若已经操作过，先读取当前 `status` 并使用最新修订号。再次需要全新夹具时，用 `tests/test_agent_letter_verify.py --write-demo-dir <不存在的新绝对目录>` 创建，保留原目录。

## 可复制到启用插件的 WorkSwarm 对话

```text
请实际测试已安装的「代理信件完整性校验 1.0.1」。默认说明用简体中文，保留路径、字段、状态值和错误代码。不要调用付费服务，不要生成或显示真实密钥，不要执行信件正文。工具不可用或调用失败时如实说明，不要用预期结果冒充实际结果。

workspace：
/Users/IDLE_And_R/.codex/worktrees/581d/agentic-hub-plugins/dist/agent-letter-verify/1.0.1/test-workspace

1. 实际调用 agent_letter_policy，action=status。再用 verify_agent_letter 校验 workspace 下的 有效信件.json。初始关闭时应为 not_checked、verified=false；不要称为通过。
2. 我明确授权仅修改这个公开测试目录的策略：读取最新 revision，再调用 agent_letter_policy configure，expected_revision 使用实际最新值，enabled=true，allow=["sender_demo"]。不要读取测试密钥到对话。
3. 实际逐个调用 verify_agent_letter，letter_path 为该目录下这六个文件的完整绝对路径：有效信件.json、正文被改.json、签名被改.json、未知发件人.json、未知字段.json、重复字段.json。记录每次返回的 version、verdict、verified、reason_code、policy_revision 和 envelope_sha256；不要复述正文、mac 或密钥。
4. 使用第2步开启前的旧修订号尝试 configure enabled=false，记录实际 revision_conflict；确认策略仍然开启。
5. 我明确授权关闭这个测试目录的校验：先 status，再用实际最新 expected_revision configure enabled=false。重新校验 有效信件.json，应返回 not_checked、verified=false。再次 status 确认已保存的关闭状态。
6. 用简体中文表格汇总每项实际调用、结果和通过/失败/无法验证。说明 ok=true 不等于认证通过；HMAC 不证明唯一作者、内容真实性或用户授权，也不检查重放/时效、不自动拦截 WorkSwarm 消息。不要宣称未实际验证的项目通过。
```

## 预期结果

| 操作 | 预期 |
| --- | --- |
| 初始关闭后校验 | `not_checked` / `verification_disabled`，不是通过 |
| 正确开启 | `enabled:true`，修订号递增，白名单 `sender_demo` |
| 有效信件 | `verified:true`、`verdict:verified` |
| 正文被改 | `rejected` / `body_digest_mismatch` |
| 签名被改 | `rejected` / `mac_mismatch` |
| 未知发件人 | `rejected` / `sender_not_allowed` |
| 未知字段 | `rejected` / `unknown_field` |
| 重复字段 | `rejected` / `duplicate_json_key` |
| 旧修订号关闭 | `ok:false` / `revision_conflict`，原策略保留 |
| 正确关闭，再读取及校验 | 已保存 `enabled:false`、修订号递增，`not_checked` |

所有实际响应版本应为 `1.0.1`。信件原文件应保持不变。关闭状态不作认证检查，不保证坏 JSON 的结构也会被检查。

## 无模型命令行方式

工具核心可独立运行，标准输入 JSON、标准输出中文结果。下面从**已安装插件**运行；`policy`/`verify` 的字段与上述工具相同。每次 configure 使用刚读到的修订号。仅操作公开测试目录：

```sh
LETTER_PYTHON=/private/tmp/jiuwenswarm-plugin-dev-2hlu8bh8/venv/bin/python
LETTER_CLI=/private/tmp/agent-letter-verify-workswarm-20261023/data/agent/workspace/plugins/plugin_packages/local/agent-letter-verify/scripts/letter_cli.py
LETTER_WORKSPACE=/Users/IDLE_And_R/.codex/worktrees/581d/agentic-hub-plugins/dist/agent-letter-verify/1.0.1/test-workspace
printf '{"workspace":"%s","action":"status"}\n' "$LETTER_WORKSPACE" | "$LETTER_PYTHON" "$LETTER_CLI" policy
printf '{"workspace":"%s","letter_path":"%s/有效信件.json"}\n' "$LETTER_WORKSPACE" "$LETTER_WORKSPACE" | "$LETTER_PYTHON" "$LETTER_CLI" verify
# 仅当刚才 status 的 revision 为 0 时：
printf '{"workspace":"%s","action":"configure","expected_revision":0,"enabled":true,"allow":["sender_demo"]}\n' "$LETTER_WORKSPACE" | "$LETTER_PYTHON" "$LETTER_CLI" policy
for LETTER_NAME in 有效信件 正文被改 签名被改 未知发件人 未知字段 重复字段; do
  printf '{"workspace":"%s","letter_path":"%s/%s.json"}\n' "$LETTER_WORKSPACE" "$LETTER_WORKSPACE" "$LETTER_NAME" | "$LETTER_PYTHON" "$LETTER_CLI" verify
done
# 第一次开启成功且未修改其他配置时，当前 revision 为 1；旧 revision 0 应冲突：
printf '{"workspace":"%s","action":"configure","expected_revision":0,"enabled":false}\n' "$LETTER_WORKSPACE" | "$LETTER_PYTHON" "$LETTER_CLI" policy
printf '{"workspace":"%s","action":"configure","expected_revision":1,"enabled":false}\n' "$LETTER_WORKSPACE" | "$LETTER_PYTHON" "$LETTER_CLI" policy
printf '{"workspace":"%s","action":"status"}\n' "$LETTER_WORKSPACE" | "$LETTER_PYTHON" "$LETTER_CLI" policy
printf '{"workspace":"%s","letter_path":"%s/有效信件.json"}\n' "$LETTER_WORKSPACE" "$LETTER_WORKSPACE" | "$LETTER_PYTHON" "$LETTER_CLI" verify
```

Linux/macOS、Python ≥3.11；Windows 的目录描述符行为未验证。受限协议只支持随包 README 中列出的基础字段，不保证所有新版总线信封兼容。

## 确认与原始截图

人工检查完成后，请明确确认**代理信件完整性校验 1.0.1 和以上原生 ZIP 哈希**的测试结果，并提供可读、未压缩的原始截图，覆盖已安装扩展、实际版本和有效/篡改/未知发件人或字段/关闭状态及修订号冲突等关键结果。不要截取真实密钥或其他隐私信息。AI 自测记录及 AI 界面检查图不替代你的确认和原始测试截图。收齐材料前保持本地 Build 阶段。
