"""流动效率与持续成本测算：两个确定性计算工具（原生只读，无网络、无文件访问、无时钟）。

- 本模块由本团队独立编写，不含上游代码。公式、判断顺序和提示语的依据是上游 Agile Forge Praxis
  两份技能说明里写出的算法（Agile Forge / Philip Müller，MIT，固定提交
  db7c20facb516b7b7c0c2088882f52368c54468b），见 THIRD_PARTY_NOTICES.md。
- 全部运算用有理数（fractions.Fraction）精确完成，只在输出时做四舍五入，所以显示值和公式里
  代入的数字不会因为浮点误差而对不上。
- 工具只做算术：不判断“好”或“坏”，不给行业正常值或经验法则。
"""
from __future__ import annotations

import asyncio
from copy import deepcopy
from decimal import Context, Decimal, ROUND_HALF_UP
from fractions import Fraction
import math
from typing import Any, AsyncIterator

from openjiuwen.core.foundation.tool import Tool, ToolCard

TOOL_PREFIX = "flow_cost_"
HOURS_PER_WORKDAY = 8
CALENDAR_TO_WORKING = Fraction(5, 7)
MAX_LEAD_DAYS = 5000
MAX_ITEMS_PER_YEAR = 100000
MAX_AMOUNT = 1_000_000_000
PAYBACK_CAP_MONTHS = 600
DEFAULT_SPEEDUP = 2
DEFAULT_WAIT_REDUCTION = Fraction(1, 2)
DEFAULT_USAGE_RATIO = Fraction(7, 10)
DEFAULT_COST_OVERRUN = Fraction(1, 2)
DEFAULT_CURRENCY = "元"
DEFAULT_YEARS = 3
USAGE_DIAL = Fraction(4, 10)  # “用量旋钮拧到底”：只剩计划用量的 40%
COST_DIAL = Fraction(1)       # “成本旋钮拧到底”：运行成本再多 100%

CTX = Context(prec=80, rounding=ROUND_HALF_UP)

NOTE_ZH = ("请用简体中文向用户说明结果，逐条展示 formulas_zh 里带代入数字的公式；只对显示做四舍五入并用“≈”连接，"
           "不要编造没有返回的数据，不要给出行业正常值、对标值或经验法则。")


class CalcError(Exception):
    def __init__(self, code: str, message: str, **details: Any) -> None:
        super().__init__(message)
        self.code = code
        self.message = message
        self.details = details


def error(code: str, message: str, **details: Any) -> dict:
    return {"ok": False, "error": {"code": code, "message": message, **details}}


# ---------------------------------------------------------------- 参数定义

CATALOG: dict[str, dict] = {
    "flow_efficiency": {
        "description": "计算一个事项的流动效率：流动效率 = 实际处理工时 ÷ 周期总工时 × 100。需要周期天数（说明是工作日还是日历日）"
                       "和处理小时数；返回等待时间、两个改进杠杆（处理加快 / 等待缩短）各自节省的工作日及哪个更大，"
                       "每一步公式都带代入数字，可选年度推算。只做算术，不给“正常值”。",
        "schema": {"type": "object", "additionalProperties": False, "required": ["lead_time_days", "day_type", "touch_hours"], "properties": {
            "lead_time_days": {"type": "number", "exclusiveMinimum": 0, "maximum": MAX_LEAD_DAYS,
                               "description": "周期天数：从最初的请求（不是第一个处理步骤）到请求方拿到可用结果。必须同时说明 day_type。"},
            "day_type": {"type": "string", "enum": ["working", "calendar"],
                         "description": "lead_time_days 的单位：working 工作日，calendar 日历日（按 5/7 近似折算成工作日，不考虑节假日）。"},
            "touch_hours": {"type": "number", "exclusiveMinimum": 0,
                            "description": "实际有人在处理该事项的小时数（含真正做过的检查与审批）；队列、邮箱、批处理窗口、等排期或等发布窗口的等待不算。"},
            "items_per_year": {"type": "integer", "minimum": 0, "maximum": MAX_ITEMS_PER_YEAR,
                               "description": "每年事项数，用于年度推算；0 或不填表示未提供。"},
            "speedup_factor": {"type": "number", "exclusiveMinimum": 1, "maximum": 100,
                               "description": f"杠杆 A：处理速度加快的倍数，默认 {DEFAULT_SPEEDUP}。"},
            "wait_reduction_ratio": {"type": "number", "exclusiveMinimum": 0, "maximum": 1,
                                     "description": "杠杆 B：等待时间减少的比例（0 到 1），默认 0.5。"},
        }},
    },
    "business_case": {
        "description": "计算含持续运行成本的简单商业论证：一次性项目成本、每年运行成本、每年收益、期限（3 或 5 年）；"
                       "返回运行成本占比、总成本与总收益、结果、回收期（月）、投资回报率、盈亏平衡用量与盈亏平衡成本超支，"
                       "以及“用量只有计划的一部分”“运行成本超支”两种偏离的结果，每一步公式都带代入数字。只做算术，不折现。",
        "schema": {"type": "object", "additionalProperties": False, "required": ["one_time_cost", "running_cost_per_year", "benefit_per_year"], "properties": {
            "one_time_cost": {"type": "number", "minimum": 0, "maximum": MAX_AMOUNT,
                              "description": "一次性项目成本：到上线为止的全部投入（开发、集成、数据准备、上线培训等）。"},
            "running_cost_per_year": {"type": "number", "minimum": 0, "maximum": MAX_AMOUNT,
                                      "description": "每年运行成本：托管、许可、AI 项目的接口与推理费用、支持与维护、版本更新、治理工作量、第二年起的新人培训等。填 0 几乎总是不对，请让用户粗估。"},
            "benefit_per_year": {"type": "number", "exclusiveMinimum": 0, "maximum": MAX_AMOUNT,
                                 "description": "稳定状态下每年的预期收益：避免的成本、节省的时间（仅限已决定去向的）、新增收入（保守估计）。"},
            "years": {"type": "integer", "enum": [3, 5], "description": "计算期限（年），3 或 5，默认 3。"},
            "usage_ratio": {"type": "number", "exclusiveMinimum": 0, "exclusiveMaximum": 1,
                            "description": "偏离情形一：实际用量占计划的比例，默认 0.7；运行成本不随用量变化。"},
            "running_cost_overrun_ratio": {"type": "number", "exclusiveMinimum": 0, "maximum": 10,
                                           "description": "偏离情形二：运行成本超出计划的比例，默认 0.5（即多 50%）；收益不变。"},
            "currency": {"type": "string", "maxLength": 8, "description": f"金额的货币或单位标签，只用于显示，默认“{DEFAULT_CURRENCY}”。"},
        }},
    },
}


def check_value(name: str, spec: dict, value: Any) -> str | None:
    kind = spec.get("type")
    if kind in ("number", "integer"):
        if isinstance(value, bool) or not isinstance(value, (int, float)):
            return f"{name} 必须是{'整数' if kind == 'integer' else '数字'}。"
        if kind == "integer" and isinstance(value, float):
            return f"{name} 必须是整数。"
        if isinstance(value, float) and not math.isfinite(value):
            return f"{name} 必须是有限的数字。"
        if "enum" in spec and value not in spec["enum"]:
            return f"{name} 只能是：{'、'.join(str(v) for v in spec['enum'])}。"
        if "minimum" in spec and value < spec["minimum"]:
            return f"{name} 不能小于 {spec['minimum']}。"
        if "exclusiveMinimum" in spec and value <= spec["exclusiveMinimum"]:
            return f"{name} 必须大于 {spec['exclusiveMinimum']}。"
        if "maximum" in spec and value > spec["maximum"]:
            return f"{name} 不能大于 {spec['maximum']}。"
        if "exclusiveMaximum" in spec and value >= spec["exclusiveMaximum"]:
            return f"{name} 必须小于 {spec['exclusiveMaximum']}。"
    elif kind == "string":
        if not isinstance(value, str):
            return f"{name} 必须是字符串。"
        text = value.strip()
        if "enum" in spec:
            if text not in spec["enum"]:
                return f"{name} 只能是：{'、'.join(spec['enum'])}。"
            return None
        if not text:
            return f"{name} 不能为空。"
        if len(text) > spec.get("maxLength", 80):
            return f"{name} 过长（最多 {spec.get('maxLength', 80)} 个字符）。"
        if any(ord(ch) < 32 for ch in text):
            return f"{name} 不能包含控制字符或换行。"
    return None


def validate(tool: str, arguments: Any) -> tuple[dict | None, str | None]:
    if not isinstance(arguments, dict):
        return None, "参数必须是 JSON 对象，并直接传入字段，不要套 arguments。"
    schema = CATALOG[tool]["schema"]
    props = schema["properties"]
    unknown = sorted(set(arguments) - set(props))
    if unknown:
        return None, "存在未定义的参数：" + "、".join(unknown) + "。"
    values = {}
    for key, item in arguments.items():
        if item is None:
            return None, f"{key} 不能为 null；不需要时请省略该字段。"
        problem = check_value(key, props[key], item)
        if problem:
            return None, problem
        values[key] = item.strip() if isinstance(item, str) else item
    missing = [k for k in schema.get("required", []) if k not in values]
    if missing:
        return None, "缺少必填参数：" + "、".join(missing) + "。"
    return values, None


# ---------------------------------------------------------------- 数值与显示

def frac(value: Any) -> Fraction:
    """JSON 数字按其十进制写法精确转换（0.1 就是 1/10，不是二进制近似值）。"""
    return Fraction(str(value))


def dec(value: Fraction, places: int) -> Decimal:
    exact = CTX.divide(Decimal(value.numerator), Decimal(value.denominator))
    return exact.quantize(Decimal(1).scaleb(-places), rounding=ROUND_HALF_UP, context=CTX)


def num(value: Fraction, places: int) -> float:
    return float(dec(value, places))


def text(value: Fraction, places: int, grouped: bool = True) -> str:
    shown = dec(value, places)
    if shown == 0:  # 避免出现“-0.0”
        shown = abs(shown)
    return format(shown, ",f" if grouped else "f")


def exact_marker(value: Fraction, places: int) -> str:
    """显示值恰好等于精确值时用“=”，否则用“≈”。"""
    return "=" if Fraction(dec(value, places)) == value else "≈"


def percent(value: Fraction) -> Fraction:
    return value * 100


# ---------------------------------------------------------------- 流动效率

def run_flow_efficiency(values: dict) -> dict:
    d = frac(values["lead_time_days"])
    h = frac(values["touch_hours"])
    calendar = values["day_type"] == "calendar"
    n = int(values.get("items_per_year", 0))
    factor = frac(values.get("speedup_factor", DEFAULT_SPEEDUP))
    ratio = frac(values.get("wait_reduction_ratio", DEFAULT_WAIT_REDUCTION))
    per_day = Fraction(HOURS_PER_WORKDAY)

    working_days = d * CALENDAR_TO_WORKING if calendar else d
    lead_hours = working_days * per_day
    if h > lead_hours:
        raise CalcError("CAPACITY_EXCEEDED",
                        f"处理工时 {text(h, 2)} 小时超过周期内的工作时间 {text(lead_hours, 2)} 小时"
                        f"（{text(working_days, 2)} 个工作日 × {HOURS_PER_WORKDAY} 小时），这组数字对不上；请向用户确认周期天数、"
                        "是工作日还是日历日、以及处理小时数。",
                        lead_time_hours=num(lead_hours, 2), touch_hours=num(h, 2))
    wait_hours = lead_hours - h
    wait_days = wait_hours / per_day
    fe = h / lead_hours
    wait_share = wait_hours / lead_hours

    lever_a_new = wait_hours + h / factor
    lever_a_saved = lead_hours - lever_a_new
    lever_b_new = wait_hours * (1 - ratio) + h
    lever_b_saved = lead_hours - lever_b_new
    if lever_a_saved > lever_b_saved:
        bigger = "A"
    elif lever_b_saved > lever_a_saved:
        bigger = "B"
    else:
        bigger = "equal"

    formulas = []
    if calendar:
        formulas.append(f"工作日 = 日历日 × 5/7 = {text(d, 2)} × 5/7 {exact_marker(working_days, 2)} {text(working_days, 2)} 个工作日（近似，未考虑节假日）")
    else:
        formulas.append(f"工作日 = {text(d, 2)} 个工作日")
    formulas += [
        f"周期总工时 = 工作日 × {HOURS_PER_WORKDAY} = {text(working_days, 2)} × {HOURS_PER_WORKDAY} {exact_marker(lead_hours, 2)} {text(lead_hours, 2)} 小时",
        f"等待工时 = 周期总工时 − 处理工时 = {text(lead_hours, 2)} − {text(h, 2)} {exact_marker(wait_hours, 2)} {text(wait_hours, 2)} 小时"
        f"（约 {text(wait_days, 2)} 个工作日）",
        f"流动效率 = 处理工时 ÷ 周期总工时 × 100 = {text(h, 2)} ÷ {text(lead_hours, 2)} × 100 {exact_marker(percent(fe), 1)} {text(percent(fe), 1)}%",
        f"杠杆 A（处理加快 {text(factor, 2)} 倍）：新周期 = 等待 + 处理 ÷ 倍数 = {text(wait_hours, 2)} + {text(h, 2)} ÷ {text(factor, 2)} "
        f"{exact_marker(lever_a_new, 2)} {text(lever_a_new, 2)} 小时（{text(lever_a_new / per_day, 2)} 个工作日），节省 {text(lever_a_saved / per_day, 2)} 个工作日",
        f"杠杆 B（等待缩短 {text(percent(ratio), 1)}%）：新周期 = 等待 × (1 − 比例) + 处理 = {text(wait_hours, 2)} × (1 − {text(ratio, 2)}) + {text(h, 2)} "
        f"{exact_marker(lever_b_new, 2)} {text(lever_b_new, 2)} 小时（{text(lever_b_new / per_day, 2)} 个工作日），节省 {text(lever_b_saved / per_day, 2)} 个工作日",
    ]
    yearly = None
    if n > 0:
        yearly = wait_days * n
        formulas.append(f"年度推算 = 每事项等待工作日 × 每年事项数 = {text(wait_days, 2)} × {n:,} {exact_marker(yearly, 1)} {text(yearly, 1)} 事项·天")

    flags = []
    if fe < Fraction(5, 100):
        flags.append("结果低于 5%：请和用户核对——处理工时的估计是否覆盖了每一分钟？是否把自动化处理（无需人工介入但确实在运行）误算成了等待？")
    if fe == 1:
        flags.append("结果正好是 100%，即没有等待时间。这种情况很少成立，请和用户一起核对计时从哪里开始、到哪里结束。")
    if bigger == "equal":
        flags.append("两个杠杆节省的时间相同。")
    caveats = [
        "单个事项只是数量级参考，不是对流程的结论；要看多个事项及其离散程度才能下结论。",
        "这个指标只说明东西流得多快，不说明流过去的是不是对的东西。",
        "它诊断的是系统，不适合用来评价个人或团队。",
        "年度推算是“事项·天”的总和，不是日历时间，因为很多事项在并行等待。" if n > 0 else "未提供每年事项数，没有做年度推算。",
    ]
    if calendar:
        caveats.append("日历日按 × 5/7 折算为工作日，是近似值，节假日没有扣除。")

    data = {
        "inputs": {"lead_time_days": num(d, 4), "day_type": values["day_type"], "touch_hours": num(h, 4), "items_per_year": n,
                   "speedup_factor": num(factor, 4), "wait_reduction_ratio": num(ratio, 4)},
        "working_days": num(working_days, 2), "lead_time_hours": num(lead_hours, 2),
        "wait_hours": num(wait_hours, 2), "wait_working_days": num(wait_days, 2),
        "flow_efficiency_percent": num(percent(fe), 1), "wait_share_percent": num(percent(wait_share), 1),
        "yearly_wait_item_days": num(yearly, 1) if yearly is not None else None,
        "lever_a": {"speedup_factor": num(factor, 4), "new_lead_time_working_days": num(lever_a_new / per_day, 2),
                    "saved_working_days": num(lever_a_saved / per_day, 2)},
        "lever_b": {"wait_reduction_ratio": num(ratio, 4), "new_lead_time_working_days": num(lever_b_new / per_day, 2),
                    "saved_working_days": num(lever_b_saved / per_day, 2)},
        "bigger_lever": bigger,
        "formulas_zh": formulas, "caveats_zh": caveats,
    }
    summary = [f"流动效率 {text(percent(fe), 1)}%：周期 {text(lead_hours, 1)} 小时，其中处理 {text(h, 1)} 小时、等待 {text(wait_hours, 1)} 小时。"]
    if bigger == "A":
        summary.append(f"处理加快的杠杆更大（节省 {text(lever_a_saved / per_day, 2)} 个工作日，对比 {text(lever_b_saved / per_day, 2)}）。")
    elif bigger == "B":
        summary.append(f"缩短等待的杠杆更大（节省 {text(lever_b_saved / per_day, 2)} 个工作日，对比 {text(lever_a_saved / per_day, 2)}）。")
    return envelope("flow_efficiency", values, data, summary, flags)


# ---------------------------------------------------------------- 商业论证

def run_business_case(values: dict) -> dict:
    p = frac(values["one_time_cost"])
    l = frac(values["running_cost_per_year"])
    n = frac(values["benefit_per_year"])
    j = int(values.get("years", DEFAULT_YEARS))
    usage = frac(values.get("usage_ratio", DEFAULT_USAGE_RATIO))
    overrun = frac(values.get("running_cost_overrun_ratio", DEFAULT_COST_OVERRUN))
    cur = values.get("currency", DEFAULT_CURRENCY)

    if p == 0 and l == 0:
        raise CalcError("ZERO_COST", "一次性成本和每年运行成本都是 0：没有成本就没有可算的。请让用户至少粗估其中一项。")

    rc_total = l * j
    total_cost = p + rc_total
    total_benefit = n * j
    result = total_benefit - total_cost
    share = rc_total / total_cost
    surplus_month = (n - l) / 12
    roi = result / total_cost
    a_star = total_cost / total_benefit
    u_star = (total_benefit - total_cost) / rc_total if rc_total > 0 else None

    if surplus_month <= 0:
        payback_months, payback_status = None, "never"
    else:
        payback_months = p / surplus_month
        payback_status = "over_50_years" if payback_months > PAYBACK_CAP_MONTHS else "ok"

    usage_benefit = n * usage
    usage_result = usage_benefit * j - total_cost
    eff_running = l * (1 + overrun)
    cost_result = total_benefit - p - eff_running * j
    base_positive = result > 0
    usage_share = usage_result / result if base_positive else None
    cost_share = cost_result / result if base_positive else None

    loss_usage = (1 - USAGE_DIAL) * n * j
    loss_cost = COST_DIAL * l * j
    if loss_usage > loss_cost:
        bigger = "usage"
    elif loss_cost > loss_usage:
        bigger = "running_cost"
    else:
        bigger = "equal"

    u = lambda v, d=2: f"{text(v, d)} {cur}"  # noqa: E731
    formulas = [
        f"运行成本合计 = 每年运行成本 × 年数 = {u(l)} × {j} {exact_marker(rc_total, 2)} {u(rc_total)}",
        f"总成本 = 一次性成本 + 运行成本合计 = {u(p)} + {u(rc_total)} {exact_marker(total_cost, 2)} {u(total_cost)}",
        f"总收益 = 每年收益 × 年数 = {u(n)} × {j} {exact_marker(total_benefit, 2)} {u(total_benefit)}",
        f"结果 = 总收益 − 总成本 = {u(total_benefit)} − {u(total_cost)} {exact_marker(result, 2)} {u(result)}",
        f"运行成本占比 = 运行成本合计 ÷ 总成本 × 100 = {u(rc_total)} ÷ {u(total_cost)} × 100 {exact_marker(percent(share), 1)} {text(percent(share), 1)}%",
        f"每月盈余 = (每年收益 − 每年运行成本) ÷ 12 = ({u(n)} − {u(l)}) ÷ 12 {exact_marker(surplus_month, 2)} {u(surplus_month)}",
    ]
    if payback_status == "never":
        formulas.append("回收期 = 一次性成本 ÷ 每月盈余：每月盈余 ≤ 0，永远收不回来（“永不”）。")
    elif payback_status == "over_50_years":
        formulas.append(f"回收期 = 一次性成本 ÷ 每月盈余 = {u(p)} ÷ {u(surplus_month)} {exact_marker(payback_months, 1)} {text(payback_months, 1)} 个月（超过 50 年）。")
    else:
        formulas.append(f"回收期 = 一次性成本 ÷ 每月盈余 = {u(p)} ÷ {u(surplus_month)} {exact_marker(payback_months, 1)} {text(payback_months, 1)} 个月")
    formulas += [
        f"投资回报率 = 结果 ÷ 总成本 × 100 = {u(result)} ÷ {u(total_cost)} × 100 {exact_marker(percent(roi), 1)} {text(percent(roi), 1)}%",
        f"盈亏平衡用量 = 总成本 ÷ 总收益 = {u(total_cost)} ÷ {u(total_benefit)} {exact_marker(percent(a_star), 1)} {text(percent(a_star), 1)}%（达到计划收益的这个比例，结果为 0）",
    ]
    if u_star is not None:
        formulas.append(f"盈亏平衡成本超支 = (总收益 − 一次性成本 − 运行成本合计) ÷ 运行成本合计 = ({u(total_benefit)} − {u(p)} − {u(rc_total)}) ÷ {u(rc_total)} "
                        f"{exact_marker(percent(u_star), 0)} {'+' if u_star >= 0 else ''}{text(percent(u_star), 0)}%（运行成本最多可以再增加这个比例）")
    formulas.append(f"偏离一（用量只有计划的 {text(percent(usage), 0)}%）：有效收益 = {u(n)} × {text(usage, 2)} {exact_marker(usage_benefit, 2)} {u(usage_benefit)}；"
                    f"结果 = {u(usage_benefit)} × {j} − {u(total_cost)} {exact_marker(usage_result, 2)} {u(usage_result)}"
                    + (f"，约为原结果的 {text(percent(usage_share), 0)}%" if usage_share is not None else ""))
    formulas.append(f"偏离二（运行成本多 {text(percent(overrun), 0)}%）：有效运行成本 = {u(l)} × (1 + {text(overrun, 2)}) {exact_marker(eff_running, 2)} {u(eff_running)}；"
                    f"结果 = {u(total_benefit)} − {u(p)} − {u(eff_running)} × {j} {exact_marker(cost_result, 2)} {u(cost_result)}"
                    + (f"，约为原结果的 {text(percent(cost_share), 0)}%" if cost_share is not None else ""))
    formulas.append(f"两个旋钮拧到底：用量降到 40% 的损失 = (1 − 0.4) × 每年收益 × 年数 = 0.6 × {u(n)} × {j} {exact_marker(loss_usage, 2)} {u(loss_usage)}；"
                    f"运行成本再多 100% 的损失 = 1.0 × 每年运行成本 × 年数 = {u(l)} × {j} {exact_marker(loss_cost, 2)} {u(loss_cost)}")

    band = "low" if share < Fraction(25, 100) else ("mid" if share <= Fraction(60, 100) else "high")
    band_text = {
        "low": "运行成本占比低于 25%：项目预算占主导。这种情况存在，但也是运行侧估得太紧的典型样子，请让用户把运行成本清单再过一遍。",
        "mid": "运行成本占比在 25% 到 60% 之间：相当一部分成本发生在上线之后。只报项目成本的人会漏掉这个数字。",
        "high": "运行成本占比高于 60%：项目本身只是账单的小头。只批准项目金额，等于只批准了不到一半的决定。",
    }[band]
    flags = [band_text]
    if payback_status == "never":
        flags.append("收益没有超过每年运行成本，无论项目成本多少都永远收不回来。请明确说出：要么收益估得太保守，要么这笔账不成立。")
    elif payback_status == "over_50_years":
        flags.append("回收期超过 50 年：收益只比运行成本高出很小的数额。")
    if l == 0:
        flags.append("每年运行成本为 0 是允许的，但这意味着在按“上线后不产生任何成本”的项目计算，请向用户说明。")
    if result < 0:
        flags.append("在计划假设下结果已经为负，下面的偏离情形只是更差。")
    limits = [
        "没有折现：第三年的一块钱和今天的一块钱同等计算，折现率由财务部门决定。",
        "收益从上线起恒定，没有爬坡期。",
        "比较对象是“保持现状不变”。",
        "没有计入税、折旧或资本化。",
        "一个数字还不是商业论证，真正的内容是数字背后的假设。",
    ]

    data = {
        "inputs": {"one_time_cost": num(p, 2), "running_cost_per_year": num(l, 2), "benefit_per_year": num(n, 2), "years": j,
                   "usage_ratio": num(usage, 4), "running_cost_overrun_ratio": num(overrun, 4), "currency": cur},
        "running_cost_total": num(rc_total, 2), "total_cost": num(total_cost, 2), "total_benefit": num(total_benefit, 2),
        "result": num(result, 2), "running_cost_share_percent": num(percent(share), 1), "running_cost_share_band": band,
        "monthly_surplus": num(surplus_month, 2),
        "payback_months": num(payback_months, 1) if payback_months is not None else None, "payback_status": payback_status,
        "roi_percent": num(percent(roi), 1),
        "break_even_usage_percent": num(percent(a_star), 1),
        "break_even_cost_overrun_percent": num(percent(u_star), 0) if u_star is not None else None,
        "usage_scenario": {"usage_ratio": num(usage, 4), "effective_benefit_per_year": num(usage_benefit, 2), "result": num(usage_result, 2),
                           "share_of_base_result_percent": num(percent(usage_share), 0) if usage_share is not None else None},
        "cost_scenario": {"overrun_ratio": num(overrun, 4), "effective_running_cost_per_year": num(eff_running, 2), "result": num(cost_result, 2),
                          "share_of_base_result_percent": num(percent(cost_share), 0) if cost_share is not None else None},
        "dials": {"usage_to_40_percent_loss": num(loss_usage, 2), "running_cost_plus_100_percent_loss": num(loss_cost, 2), "bigger": bigger},
        "formulas_zh": formulas, "limits_zh": limits,
    }
    summary = [f"{j} 年总成本 {u(total_cost, 0)}（其中运行成本 {text(percent(share), 1)}%），总收益 {u(total_benefit, 0)}，结果 {u(result, 0)}。"]
    if payback_status == "ok":
        summary.append(f"回收期约 {text(payback_months, 1)} 个月，投资回报率约 {text(percent(roi), 1)}%。")
    return envelope("business_case", values, data, summary, flags)


# ---------------------------------------------------------------- 封装与工具类

def envelope(tool: str, values: dict, data: dict, summary: list[str], warnings: list[str]) -> dict:
    return {"ok": True, "tool": TOOL_PREFIX + tool, "arguments": dict(values), "message": NOTE_ZH,
            "summary_zh": summary, "data": data, "warnings_zh": warnings}


RUNNERS = {"flow_efficiency": run_flow_efficiency, "business_case": run_business_case}


async def call_tool(name: str, arguments: Any) -> dict:
    values, message = validate(name, arguments)
    if message:
        return error("INVALID_ARGUMENTS", message, tool=TOOL_PREFIX + name)
    try:
        return RUNNERS[name](values)
    except CalcError as exc:
        return error(exc.code, exc.message, tool=TOOL_PREFIX + name, **exc.details)
    except asyncio.CancelledError:
        raise
    except Exception as exc:  # 不向用户暴露内部堆栈，也不伪造结果
        return error("INTERNAL_ERROR", f"工具内部出错（{type(exc).__name__}）；本次没有返回结果。", tool=TOOL_PREFIX + name)


class FlowCostTool(Tool):
    key = ""

    def __init__(self) -> None:
        entry = CATALOG[self.key]
        super().__init__(ToolCard(id=TOOL_PREFIX + self.key, name=TOOL_PREFIX + self.key, description=entry["description"],
                                  input_params=deepcopy(entry["schema"])))

    async def invoke(self, inputs: dict, **kwargs: Any) -> dict:
        return await call_tool(self.key, inputs)

    async def stream(self, inputs: dict, **kwargs: Any) -> AsyncIterator[dict]:
        yield await self.invoke(inputs, **kwargs)


class FlowEfficiencyTool(FlowCostTool):
    key = "flow_efficiency"


class BusinessCaseTool(FlowCostTool):
    key = "business_case"
