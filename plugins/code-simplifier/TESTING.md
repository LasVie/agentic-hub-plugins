# Code Simplifier 1.0.1 test guide

Task AH-20261022-code-simplifier; owner Cai Zhenze.

## Choose the archive

- JiuwenSwarm / WorkSwarm local **Create → Create from file**: use
  `code-simplifier-1.0.1-native.zip` (root-level manifest.json).
- Repository / Hub format: `code-simplifier-1.0.1.zip` (plugin.yaml plus
  code-simplifier/code-simplifier/). The current local importer does not unwrap
  this double nesting. Use the native ZIP or extracted inner payload locally.

Both carry exactly the same native files, with different archive hashes.
The skill instructions are byte-identical to the supplied 1.0.0 version.

## Install and exercise

Environment: built-in, non-team JiuwenSwarm/WorkSwarm agent with a configured
model and read/edit/test access to a disposable project. No added MCP, hook,
script, token or dependency is required by this Plugin.

1. Check for an existing code-simplifier ID. The host rejects duplicate IDs.
   Use the normal application replacement/clean test-profile flow when needed;
   do not overwrite runtime directories or remove unrelated installed copies.
2. Extensions → Plugins → Create → Create from file: import the native 1.0.1 ZIP.
   Under My Extensions verify version 1.0.1, install and explicitly select it.
3. Ask: “使用代码简化技能，仅简化我指定的函数，遵循项目规范，保持输入输出、
   错误处理和副作用不变，运行允许的针对性测试，并说明改动与验证结果。”
4. Expect focused readable edits, no unrelated file changes, and a truthful
   summary of checks. Exercise normal, boundary and error cases with existing
   tests before/after. Model claims alone do not establish behavior equivalence.
5. Test missing scope in a fresh session (expect clarification), disallowed
   checks (expect restrictions honored and limitations reported), and already
   clear code (expect no unnecessary edits). No automatic hook or subagent runs.

Capture a real screenshot showing 1.0.1, a key operation and its result. Report
the tested archive/version/hash and any problems. Old 1.0.0 confirmation does not
confirm these new bytes. Package/loader checks do not prove generated-edit quality.
The accepted overlap remains recorded; no Hub delivery or acceptance is claimed.
