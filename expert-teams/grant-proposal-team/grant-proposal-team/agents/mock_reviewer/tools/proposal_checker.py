"""基金申请书专家团的校验工具（纯算术与文本核对，不联网、不写文件）。

action 取值：
- criteria_map：核对评审要点 → 申请书章节的映射，并逐字检查证据引文是否真的出现在章节正文中。
- budget：核对预算明细的数量×单价×年数、合计、总额上限与各类别占比上限。
- limits：按指南限制统计每节与全文的篇幅（中文按字、英文按词），列出超限项。
- score：按评审细则的权重汇总模拟评审打分，列出低分项与缺少依据的打分。
- review：一次跑完以上提供了输入的检查，给出 ready_to_submit 结论。
"""
import re
from typing import Annotated, Literal

from openjiuwen.core.foundation.tool import Tool, ToolCard
from pydantic import BaseModel, ConfigDict, Field


class Model(BaseModel):
    model_config = ConfigDict(extra="forbid", allow_inf_nan=False)


Id = Annotated[str, Field(min_length=1, max_length=80, pattern=r"\S")]
Text = Annotated[str, Field(min_length=1, max_length=20000, pattern=r"\S")]
Body = Annotated[str, Field(max_length=400000)]
Money = Annotated[float, Field(ge=0, le=1e13)]
Ratio = Annotated[float, Field(gt=0, le=1)]

CJK = re.compile(r"[㐀-䶿一-鿿豈-﫿　-〿＀-￯]")
WORD = re.compile(r"[A-Za-z0-9]+(?:[-'’.][A-Za-z0-9]+)*")
SPACE = re.compile(r"\s+")


# ---------- 输入模型 ----------

class Criterion(Model):
    id: Id
    text: Text
    weight: Annotated[float, Field(ge=0, le=1000)] = 1.0
    mandatory: bool = True


class Evidence(Model):
    criterion_id: Id
    quote: Text


class Section(Model):
    id: Id
    title: Text
    text: Body = ""
    evidence: list[Evidence] = Field(default_factory=list, max_length=500)


class BudgetLine(Model):
    item: Text
    category: Id
    quantity: Annotated[float, Field(ge=0, le=1e9)]
    unit_cost: Money
    years: Annotated[float, Field(gt=0, le=20)] = 1.0
    stated_amount: Money | None = None
    justification: str = Field(default="", max_length=4000)


class CategoryCap(Model):
    category: Id
    max_ratio: Ratio


class Budget(Model):
    currency: Annotated[str, Field(min_length=1, max_length=10, pattern=r"\S")]
    lines: list[BudgetLine] = Field(min_length=1, max_length=500)
    total_cap: Money | None = None
    stated_total: Money | None = None
    category_caps: list[CategoryCap] = Field(default_factory=list, max_length=50)
    tolerance: Annotated[float, Field(ge=0, le=1e6)] = 0.01


class Limit(Model):
    section_id: Id | None = None  # 为空表示全文限制
    max_units: Annotated[int, Field(gt=0, le=10000000)]
    unit: Literal["mixed", "chars", "words"] = "mixed"


class Score(Model):
    criterion_id: Id
    score: Annotated[float, Field(ge=0, le=1000)]
    max_score: Annotated[float, Field(gt=0, le=1000)]
    rationale: str = Field(default="", max_length=4000)


class Input(Model):
    action: Literal["criteria_map", "budget", "limits", "score", "review"] = "review"
    criteria: list[Criterion] = Field(default_factory=list, max_length=300)
    sections: list[Section] = Field(default_factory=list, max_length=200)
    budget: Budget | None = None
    limits: list[Limit] = Field(default_factory=list, max_length=200)
    scores: list[Score] = Field(default_factory=list, max_length=300)
    weak_threshold: Ratio = 0.6


# ---------- 工具函数 ----------

def _norm(s: str) -> str:
    return SPACE.sub(" ", s.replace("　", " ")).strip()


def _unique(ids, label):
    seen, dup = set(), []
    for i in ids:
        k = i.strip()
        if k in seen:
            dup.append(k)
        seen.add(k)
    if dup:
        raise ValueError(f"{label} ID 重复：{', '.join(sorted(set(dup)))}")


def count_units(text: str, unit: str = "mixed") -> int:
    """mixed：中文字符逐字计数 + 英文/数字按词计数；chars：去空白后的字符数；words：英文词数。"""
    if unit == "chars":
        return len(SPACE.sub("", text))
    if unit == "words":
        return len(WORD.findall(text))
    return len(CJK.findall(text)) + len(WORD.findall(CJK.sub(" ", text)))


def _need(cond, msg):
    if not cond:
        raise ValueError(msg)


# ---------- 各项检查 ----------

def check_criteria_map(data: Input) -> dict:
    _need(data.criteria, "criteria_map 需要 criteria（评审要点清单）")
    _need(data.sections, "criteria_map 需要 sections（章节与证据引文）")
    _unique([c.id for c in data.criteria], "评审要点")
    _unique([s.id for s in data.sections], "章节")
    known = {c.id.strip(): c for c in data.criteria}
    covered: dict[str, list[str]] = {k: [] for k in known}
    bad_quotes, unknown_refs = [], []
    for s in data.sections:
        body = _norm(s.text)
        for ev in s.evidence:
            cid = ev.criterion_id.strip()
            if cid not in known:
                unknown_refs.append({"section_id": s.id, "criterion_id": cid})
                continue
            if _norm(ev.quote) in body and body:
                covered[cid].append(s.id)
            else:
                bad_quotes.append({"section_id": s.id, "criterion_id": cid, "quote": ev.quote[:200]})
    rows, missing_mandatory, missing_optional = [], [], []
    for cid, c in known.items():
        secs = sorted(set(covered[cid]))
        rows.append({"criterion_id": cid, "mandatory": c.mandatory, "covered_by": secs, "status": "covered" if secs else "missing"})
        if not secs:
            (missing_mandatory if c.mandatory else missing_optional).append(cid)
    passed = not missing_mandatory and not bad_quotes and not unknown_refs
    return {
        "check": "criteria_map",
        "passed": passed,
        "coverage": rows,
        "missing_mandatory": missing_mandatory,
        "missing_optional": missing_optional,
        "quotes_not_found": bad_quotes,
        "unknown_criterion_refs": unknown_refs,
        "basis": "引文去除多余空白后须逐字出现在所属章节正文中才算覆盖；只核对文本是否存在，不判断论证质量。",
    }


def check_budget(data: Input) -> dict:
    _need(data.budget is not None, "budget 检查需要 budget 输入")
    b = data.budget
    tol = b.tolerance
    lines, mismatches, no_reason = [], [], []
    by_cat: dict[str, float] = {}
    for ln in b.lines:
        amount = ln.quantity * ln.unit_cost * ln.years
        row = {"item": ln.item, "category": ln.category.strip(), "computed_amount": round(amount, 2)}
        if ln.stated_amount is not None and abs(ln.stated_amount - amount) > tol:
            row["stated_amount"] = ln.stated_amount
            mismatches.append({"item": ln.item, "stated": ln.stated_amount, "computed": round(amount, 2)})
        if not ln.justification.strip():
            no_reason.append(ln.item)
        by_cat[row["category"]] = by_cat.get(row["category"], 0.0) + amount
        lines.append(row)
    total = sum(by_cat.values())
    issues = []
    if b.stated_total is not None and abs(b.stated_total - total) > tol:
        issues.append({"rule": "stated_total", "stated": b.stated_total, "computed": round(total, 2)})
    if b.total_cap is not None and total > b.total_cap + tol:
        issues.append({"rule": "total_cap", "cap": b.total_cap, "computed": round(total, 2), "over_by": round(total - b.total_cap, 2)})
    cats = []
    caps = {c.category.strip(): c.max_ratio for c in b.category_caps}
    for cat, amt in sorted(by_cat.items(), key=lambda kv: -kv[1]):
        ratio = amt / total if total > 0 else 0.0
        row = {"category": cat, "amount": round(amt, 2), "share": round(ratio, 4)}
        if cat in caps:
            row["max_share"] = caps[cat]
            if ratio > caps[cat] + 1e-9:
                issues.append({"rule": "category_cap", "category": cat, "share": round(ratio, 4), "max_share": caps[cat]})
        cats.append(row)
    for cat in caps:
        if cat not in by_cat:
            cats.append({"category": cat, "amount": 0.0, "share": 0.0, "max_share": caps[cat]})
    passed = not issues and not mismatches
    return {
        "check": "budget",
        "passed": passed,
        "currency": b.currency,
        "computed_total": round(total, 2),
        "lines": lines,
        "by_category": cats,
        "line_mismatches": mismatches,
        "issues": issues,
        "lines_without_justification": no_reason,
        "basis": f"每行金额 = 数量 × 单价 × 年数；容差 {tol} {b.currency}。类别占比 = 类别合计 / 总额。不判断单价是否合理，也不核对资助方政策原文。",
    }


def check_limits(data: Input) -> dict:
    _need(data.limits, "limits 检查需要 limits（篇幅限制）")
    _need(data.sections, "limits 检查需要 sections（章节正文）")
    secs = {s.id.strip(): s for s in data.sections}
    rows, over, unknown = [], [], []
    for lim in data.limits:
        if lim.section_id is None:
            text = "\n".join(s.text for s in data.sections)
            target = "__total__"
        else:
            sid = lim.section_id.strip()
            if sid not in secs:
                unknown.append(sid)
                continue
            text, target = secs[sid].text, sid
        used = count_units(text, lim.unit)
        row = {"target": target, "unit": lim.unit, "used": used, "max": lim.max_units, "remaining": lim.max_units - used}
        rows.append(row)
        if used > lim.max_units:
            over.append(row)
    return {
        "check": "limits",
        "passed": not over and not unknown,
        "results": rows,
        "over_limit": over,
        "unknown_sections": unknown,
        "basis": "mixed：每个汉字/全角符号计 1，英文与数字按词计 1；chars：去空白后的字符数；words：英文词数。资助方的计数规则可能不同，以官方系统为准。",
    }


def check_score(data: Input) -> dict:
    _need(data.criteria, "score 需要 criteria（含权重）")
    _need(data.scores, "score 需要 scores（模拟评审打分）")
    _unique([c.id for c in data.criteria], "评审要点")
    _unique([s.criterion_id for s in data.scores], "打分")
    known = {c.id.strip(): c for c in data.criteria}
    got = {s.criterion_id.strip(): s for s in data.scores}
    unknown = sorted(set(got) - set(known))
    unscored = [cid for cid in known if cid not in got]
    rows, weak, no_reason = [], [], []
    wsum = wtot = 0.0
    for cid, c in known.items():
        s = got.get(cid)
        if s is None:
            continue
        _need(s.score <= s.max_score, f"要点 {cid} 的得分 {s.score} 超过满分 {s.max_score}")
        ratio = s.score / s.max_score
        wsum += c.weight * ratio
        wtot += c.weight
        row = {"criterion_id": cid, "score": s.score, "max_score": s.max_score, "ratio": round(ratio, 4), "weight": c.weight}
        rows.append(row)
        if ratio < data.weak_threshold:
            weak.append(row)
        if not s.rationale.strip():
            no_reason.append(cid)
    rows.sort(key=lambda r: r["ratio"])
    weighted = round(wsum / wtot, 4) if wtot > 0 else None
    return {
        "check": "score",
        "passed": not weak and not unscored and not unknown and not no_reason,
        "weighted_ratio": weighted,
        "scores_low_to_high": rows,
        "weak_criteria": weak,
        "unscored_criteria": unscored,
        "unknown_criterion_refs": unknown,
        "scores_without_rationale": no_reason,
        "basis": f"加权得分率 = Σ(权重 × 得分/满分) / Σ权重（只计已打分项）；低于 {data.weak_threshold} 视为薄弱。分数来自模拟评审的判断，不代表真实评审结果或资助概率。",
    }


CHECKS = {"criteria_map": check_criteria_map, "budget": check_budget, "limits": check_limits, "score": check_score}


def run(data: Input) -> dict:
    if data.action != "review":
        return CHECKS[data.action](data)
    results, skipped = {}, []
    plan = {
        "criteria_map": bool(data.criteria and data.sections),
        "budget": data.budget is not None,
        "limits": bool(data.limits and data.sections),
        "score": bool(data.criteria and data.scores),
    }
    for name, ok in plan.items():
        if ok:
            results[name] = CHECKS[name](data)
        else:
            skipped.append(name)
    _need(results, "review 至少需要一组可检查的输入")
    ready = all(r["passed"] for r in results.values()) and not skipped
    return {
        "check": "review",
        "ready_to_submit": ready,
        "failed": [k for k, r in results.items() if not r["passed"]],
        "skipped": skipped,
        "results": results,
        "basis": "四项检查全部提供且全部通过才为 ready_to_submit；缺任一项视为未完成。这只是形式与内部一致性检查，不代替资助方的形式审查或专家评审。",
    }


class ProposalCheckerTool(Tool):
    def __init__(self):
        super().__init__(
            ToolCard(
                id="proposal_checker",
                name="proposal_checker",
                description=(
                    "基金申请书校验：criteria_map 核对评审要点覆盖与证据引文；budget 核对预算算术、总额与类别占比上限；"
                    "limits 统计篇幅是否超限；score 汇总模拟评审加权得分；review 一次运行全部检查并给出 ready_to_submit。"
                    "只做文本与算术核对，不联网、不写文件、不判断科学价值。"
                ),
                input_params=Input.model_json_schema(),
            )
        )

    async def invoke(self, inputs, **kwargs):
        try:
            return {"success": True, **run(Input.model_validate(inputs))}
        except (ValueError, ArithmeticError) as exc:
            return {"success": False, "error": str(exc)}

    async def stream(self, inputs, **kwargs):
        yield await self.invoke(inputs, **kwargs)
