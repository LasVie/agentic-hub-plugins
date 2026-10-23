# Manual testing: 课表校验与导出 1.0.0

Candidate `CAND-CLD-219`; task `AH-20261023-fet-timetable-audit`; owner Cai Zhenze.

Use **http://127.0.0.1:6283/**, the existing isolated WorkSwarm frontend with backend/WebSocket port 29110. The backend already has Python and openJiuwen. Automated testing makes no model calls. Its currently selected provider is `local-testing-disabled`, a dummy endpoint: conversational testing requires you to select your own configured provider. A model-free CLI alternative is below.

## Files and installation

Repository root: `/Users/IDLE_And_R/Downloads/Huawei/agentic-hub-plugins`.

- Canonical delivery ZIP: `releases/agent-plugin/fet-timetable-audit/1.0.0/fet-timetable-audit-1.0.0.zip`.
- WorkSwarm testing ZIP: `dist/fet-timetable-audit/1.0.0/fet-timetable-audit-1.0.0-workswarm.zip`.
- Fictional Chinese inputs: `dist/fet-timetable-audit/1.0.0/test-inputs/示例学校.fet`, `无冲突课表.xml`, `冲突课表.xml`.
- Exact hashes/results: `TEST_REPORT.md`; native payload equality: `dist/fet-timetable-audit/1.0.0/companion-artifact.json`.

The native companion contains every canonical inner file unchanged and removes only the marketplace wrapper required for final delivery. Use the native companion in this WorkSwarm importer.

1. Open **Extensions → My Extensions → Create → Create from file**, choose the WorkSwarm testing ZIP and import/install it. If the automated installation is already present, inspect and use **课表校验与导出 1.0.0** without duplicating it.
2. Start a fresh Agent conversation, attach the plugin, and check that its Skill and the three tools `inspect_fet`, `verify_fet_timetable`, `export_fet_timetable` are listed.
3. Select a provider you authorize for your manual conversation, then use the prompt below. The backend must be able to read the absolute local paths.

```text
请使用“课表校验与导出”的实际工具，依次完成：
1. inspect_fet 检查：
/Users/IDLE_And_R/Downloads/Huawei/agentic-hub-plugins/dist/fet-timetable-audit/1.0.0/test-inputs/示例学校.fet
2. verify_fet_timetable 对照同一目录的 无冲突课表.xml。
3. 再对照同一目录的 冲突课表.xml，列出实际检测到的问题。
4. export_fet_timetable 导出无冲突课表，teacher="张老师"，format="csv"，
output_path="/Users/IDLE_And_R/Downloads/Huawei/agentic-hub-plugins/dist/fet-timetable-audit/1.0.0/test-inputs/用户测试-张老师课表.csv"。
用中文显示实际工具版本、教师工作量、校验结果、未检查范围、导出行数和文件哈希。
这些是虚构数据。不要生成或修复课表，不要把有限检查通过说成完整可行性证明。
如果文件已存在，停止且不覆盖；若工具或文件不可用，如实说明，不编造结果。
```

Expected: version **1.0.0**, three activities using four grid slots; 张老师 has three slots and 李老师 one. The supplied valid timetable passes supported checks. The conflicting timetable reports teacher overlap, student overlap and a teacher unavailable slot. Teacher-filtered CSV has two activity rows. Exports preserve any verification findings and never silently overwrite an existing file. Repeating the same export should return a Chinese file-exists error; use a new filename for another successful export.

4. Capture an original screenshot showing the Chinese plugin name, version, actual key operation and result. Explicitly confirm testing of this exact version/package is complete or report issues. Screenshots and automated tests alone do not authorize GitHub delivery.

## Model-free verification

From the repository root, run these without a model or host SDK:

```sh
python3 -B plugins/fet-timetable-audit/fet-timetable-audit/scripts/audit_cli.py inspect "$PWD/dist/fet-timetable-audit/1.0.0/test-inputs/示例学校.fet"
python3 -B plugins/fet-timetable-audit/fet-timetable-audit/scripts/audit_cli.py verify "$PWD/dist/fet-timetable-audit/1.0.0/test-inputs/示例学校.fet" "$PWD/dist/fet-timetable-audit/1.0.0/test-inputs/无冲突课表.xml"
python3 -B plugins/fet-timetable-audit/fet-timetable-audit/scripts/audit_cli.py verify "$PWD/dist/fet-timetable-audit/1.0.0/test-inputs/示例学校.fet" "$PWD/dist/fet-timetable-audit/1.0.0/test-inputs/冲突课表.xml"
```

Exit codes: 0 = no supported-check finding, 1 = findings, 2 = input/usage error. CLI checks do not test the conversational UI. Input XML is read-only; exported CSV/JSON is created only by the export tool. Unsupported constraints, room occupancy/capacity and full feasibility are outside this plugin's scope.

No GitHub push/PR/merge, Release or Agentic Hub action belongs to this handoff. Song Haoran handles Hub operations separately.
