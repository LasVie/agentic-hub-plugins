"""proposal_checker 功能测试：python -B tests/test_proposal_checker.py [tool-file]"""
import asyncio
import importlib.util
import sys
from pathlib import Path

ROOT = Path(__file__).resolve().parents[1]
tool_file = Path(sys.argv[1]) if len(sys.argv) > 1 else ROOT / "src" / "proposal_checker.py"
spec = importlib.util.spec_from_file_location("proposal_checker", tool_file)
pc = importlib.util.module_from_spec(spec)
spec.loader.exec_module(pc)
tool = pc.ProposalCheckerTool()
passed = failed = 0


def check(name, cond, detail=""):
    global passed, failed
    if cond:
        passed += 1
        print("PASS:", name)
    else:
        failed += 1
        print("FAIL:", name, "—", str(detail)[:600])


def call(**q):
    return asyncio.run(tool.invoke(q))


CRITERIA = [
    {"id": "C1", "text": "科学意义与创新性", "weight": 3},
    {"id": "C2", "text": "研究方案可行性", "weight": 2},
    {"id": "C3", "text": "研究基础与团队", "weight": 1, "mandatory": False},
]
SECTIONS = [
    {"id": "S1", "title": "立项依据", "text": "本项目首次提出 graph-based  retrieval 方法，填补了低资源语种检索的空白。",
     "evidence": [{"criterion_id": "C1", "quote": "首次提出 graph-based retrieval 方法"}]},
    {"id": "S2", "title": "研究方案", "text": "技术路线分三个阶段，每阶段设有可量化的里程碑。",
     "evidence": [{"criterion_id": "C2", "quote": "每阶段设有可量化的里程碑"}]},
]

# 1. 要点映射：全覆盖（C3 非必需）
r = call(action="criteria_map", criteria=CRITERIA, sections=SECTIONS)
check("criteria_map passes with mandatory covered", r["success"] and r["passed"], r)
check("optional missing listed", r.get("missing_optional") == ["C3"], r)
check("whitespace-normalised quote matches", "S1" in r["coverage"][0]["covered_by"], r)

# 2. 引文不在正文中
bad = [dict(SECTIONS[0], evidence=[{"criterion_id": "C1", "quote": "国际领先水平"}]), SECTIONS[1]]
r = call(action="criteria_map", criteria=CRITERIA, sections=bad)
check("fabricated quote fails", r["success"] and not r["passed"] and r["quotes_not_found"], r)
check("C1 then missing", "C1" in r["missing_mandatory"], r)

# 3. 引用不存在的要点
bad = [dict(SECTIONS[0], evidence=SECTIONS[0]["evidence"] + [{"criterion_id": "C9", "quote": "首次提出"}]), SECTIONS[1]]
r = call(action="criteria_map", criteria=CRITERIA, sections=bad)
check("unknown criterion ref fails", not r["passed"] and r["unknown_criterion_refs"], r)

# 4. 重复 ID
r = call(action="criteria_map", criteria=CRITERIA + [CRITERIA[0]], sections=SECTIONS)
check("duplicate criterion id rejected", not r["success"] and "重复" in r["error"], r)

# 5. 预算：通过
BUDGET = {
    "currency": "CNY", "total_cap": 500000, "stated_total": 480000,
    "category_caps": [{"category": "设备费", "max_ratio": 0.3}],
    "lines": [
        {"item": "GPU 服务器", "category": "设备费", "quantity": 1, "unit_cost": 120000, "justification": "训练模型"},
        {"item": "博士生劳务", "category": "劳务费", "quantity": 2, "unit_cost": 60000, "years": 3, "stated_amount": 360000, "justification": "2 人 × 3 年"},
    ],
}
r = call(action="budget", budget=BUDGET)
check("budget passes", r["success"] and r["passed"] and r["computed_total"] == 480000, r)
check("equipment share 25%", r["by_category"][1]["share"] == 0.25, r)

# 6. 预算：行金额错、超上限、类别超比例
b = dict(BUDGET, total_cap=400000, stated_total=450000,
         category_caps=[{"category": "设备费", "max_ratio": 0.2}],
         lines=[dict(BUDGET["lines"][0]), dict(BUDGET["lines"][1], stated_amount=300000, justification="")])
r = call(action="budget", budget=b)
rules = sorted(i["rule"] for i in r["issues"])
check("budget fails three ways", not r["passed"] and rules == ["category_cap", "stated_total", "total_cap"], r)
check("line mismatch caught", r["line_mismatches"][0]["computed"] == 360000, r)
check("missing justification listed", r["lines_without_justification"] == ["博士生劳务"], r)

# 7. 篇幅：中英混排计数
check("mixed count", pc.count_units("本项目 uses GPT-4 和 RAG。", "mixed") == 8, pc.count_units("本项目 uses GPT-4 和 RAG。"))
r = call(action="limits", sections=SECTIONS, limits=[{"section_id": "S2", "max_units": 10}, {"max_units": 1000}, {"section_id": "S7", "max_units": 5}])
check("limits flags over and unknown", not r["passed"] and r["over_limit"][0]["target"] == "S2" and r["unknown_sections"] == ["S7"], r)

# 8. 模拟评审打分
SCORES = [
    {"criterion_id": "C1", "score": 4, "max_score": 5, "rationale": "创新点明确"},
    {"criterion_id": "C2", "score": 2, "max_score": 5, "rationale": "缺少风险预案"},
    {"criterion_id": "C3", "score": 5, "max_score": 5, "rationale": "前期成果充分"},
]
r = call(action="score", criteria=CRITERIA, scores=SCORES)
check("weighted ratio", r["success"] and r["weighted_ratio"] == round((3 * 0.8 + 2 * 0.4 + 1 * 1.0) / 6, 4), r)
check("weak C2 flagged", not r["passed"] and r["weak_criteria"][0]["criterion_id"] == "C2", r)
r = call(action="score", criteria=CRITERIA, scores=[dict(SCORES[0], score=6)])
check("score above max rejected", not r["success"], r)

# 9. review 汇总
good_scores = [dict(s, score=5) for s in SCORES]
r = call(action="review", criteria=CRITERIA, sections=SECTIONS, budget=BUDGET, limits=[{"max_units": 1000}], scores=good_scores)
check("review ready when all pass", r["success"] and r["ready_to_submit"], r)
r = call(action="review", criteria=CRITERIA, sections=SECTIONS, budget=BUDGET)
check("review not ready when checks skipped", r["success"] and not r["ready_to_submit"] and set(r["skipped"]) == {"limits", "score"}, r)
r = call(action="review", criteria=CRITERIA, sections=SECTIONS, budget=dict(BUDGET, total_cap=100), limits=[{"max_units": 1000}], scores=good_scores)
check("review fails on budget", not r["ready_to_submit"] and r["failed"] == ["budget"], r)

# 10. 非法输入
r = call(action="budget", budget={"currency": "CNY", "lines": [{"item": "x", "category": "y", "quantity": -1, "unit_cost": 1}]})
check("negative quantity rejected", not r["success"], r)
r = call(action="nope")
check("unknown action rejected", not r["success"], r)

print(f"\n{passed} passed, {failed} failed")
sys.exit(1 if failed else 0)
