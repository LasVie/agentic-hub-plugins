"""采购报价比选：有界输入、来源引用、金额复算及新目录交付。仅使用标准库。

本工具不判断引文是否充分支持结论，不证明成员身份或独立参与，不联网。
"""
from __future__ import annotations

import argparse
import csv
import hashlib
import html
import io
import json
import os
import re
from pathlib import Path, PurePosixPath
import shutil
import sys
import tempfile
from decimal import Decimal, InvalidOperation, localcontext

VERSION = "1.0.1"
LIMIT = 256 * 1024


class QuoteError(ValueError):
    def __init__(self, code, message):
        super().__init__(message)
        self.code = code


def require(condition, code, message):
    if not condition:
        raise QuoteError(code, message)


def text(value, label, maximum=4000):
    require(isinstance(value, str) and bool(value.strip()) and len(value) <= maximum,
            "invalid_input", f"{label}须为非空文本，且不超过{maximum}字。")
    return value


def no_symlinks(path):
    path = Path(os.path.abspath(path))
    for part in (path, *path.parents):
        require(not part.is_symlink(), "unsafe_path", "不支持符号链接路径。")
    return path


def read_bytes(path):
    path = no_symlinks(path)
    require(path.is_file(), "missing_file", "所需输入文件不存在或不是普通文件。")
    require(path.stat().st_size <= LIMIT, "input_too_large", "单个输入文件不得超过256 KiB。")
    with path.open("rb") as stream:
        data = stream.read(LIMIT + 1)
    require(len(data) <= LIMIT, "input_too_large", "输入超过读取上限。")
    return data


def duplicate_keys(pairs):
    result = {}
    for key, value in pairs:
        require(key not in result, "duplicate_key", "JSON对象含重复字段。")
        result[key] = value
    return result


def read_json(path):
    data = read_bytes(path)
    try:
        obj = json.loads(data.decode("utf-8"), object_pairs_hook=duplicate_keys,
                         parse_constant=lambda _: (_ for _ in ()).throw(ValueError("非有限值")))
    except (UnicodeError, json.JSONDecodeError, ValueError) as exc:
        if isinstance(exc, QuoteError):
            raise
        raise QuoteError("invalid_json", "输入须为有效UTF-8 JSON，不接受非有限数。") from None
    require(isinstance(obj, dict), "invalid_input", "JSON根须为对象。")
    return obj, data


def money(value, label, maximum="1000000000000"):
    require(isinstance(value, str) and len(value) <= 40, "invalid_number",
            f"{label}须为十进制字符串，不能使用浮点数、布尔值或空值。")
    try:
        number = Decimal(value)
    except InvalidOperation:
        raise QuoteError("invalid_number", f"{label}不是有效十进制数。") from None
    require(number.is_finite() and -8 <= number.as_tuple().exponent <= 22 and
            0 <= number <= Decimal(maximum),
            "invalid_number", f"{label}须为范围内非负有限数，最多8位小数。")
    return number


def fmt(value):
    return format(value, "f") if value is not None else None


def unique(items, label):
    require(len(items) == len(set(items)), "duplicate_id", f"{label}标识重复。")


def evidence(ref, source_texts, permitted):
    require(isinstance(ref, dict), "invalid_evidence", "证据须为来源、行号和原文对象。")
    require(set(ref) == {"source_id", "line", "quote"}, "invalid_evidence", "证据仅可含source_id、line、quote。")
    source = ref.get("source_id")
    require(isinstance(source, str) and source in permitted and source in source_texts,
            "invalid_evidence", "证据来源不属于该报价或未声明。")
    line = ref.get("line")
    require(type(line) is int and line > 0, "invalid_evidence", "证据行号须为正整数。")
    quote = text(ref.get("quote"), "证据原文")
    lines = source_texts[source].splitlines()
    require(line <= len(lines) and quote in lines[line - 1], "invalid_evidence",
            "证据原文与指定来源行不一致。")
    return {"source_id": source, "line": line, "quote": quote}


def load_case(case_path):
    path = no_symlinks(case_path)
    case, raw = read_json(path)
    require(type(case.get("schema_version")) is int and case["schema_version"] == 1,
            "invalid_schema", "输入schema_version须为1。")
    text(case.get("title"), "项目名称", 200)
    require(case.get("ranking_method") == "weighted-min-cost-v1", "unsupported_method",
            "须明确选用ranking_method=weighted-min-cost-v1；本版仅支持已说明的技术加权与最低合格成本比值法，不能自动替换其他评分规则。")
    currency = case.get("currency")
    require(currency is None or (isinstance(currency, str) and len(currency) == 3 and
                                currency.isascii() and currency.isupper() and currency.isalpha()),
            "invalid_input", "币种须为三位大写字母或null。")
    horizon = case.get("horizon_months")
    require(type(horizon) is int and 1 <= horizon <= 120, "invalid_input", "比较期间须为1–120个月。")
    tw, cw = money(case.get("technical_weight"), "技术权重", "100"), money(case.get("cost_weight"), "成本权重", "100")
    require(tw + cw == 100 and tw > 0 and cw > 0, "invalid_input", "技术和成本权重须均大于0，合计100。")
    criteria, offers, sources = case.get("criteria"), case.get("offers"), case.get("sources")
    require(isinstance(criteria, list) and 1 <= len(criteria) <= 10, "invalid_input", "须有1–10条评审要求。")
    require(isinstance(offers, list) and 2 <= len(offers) <= 4, "invalid_input", "须有2–4份报价。")
    require(isinstance(sources, list) and 1 <= len(sources) <= 16, "invalid_input", "须有1–16个来源文件。")
    source_texts, hashes, used_paths = {}, {"case.json": hashlib.sha256(raw).hexdigest()}, []
    for source in sources:
        require(isinstance(source, dict), "invalid_input", "来源记录须为对象。")
        sid = text(source.get("id"), "来源标识", 64)
        require(re.fullmatch(r"[A-Za-z][A-Za-z0-9_-]{0,63}", sid) is not None,
                "invalid_input", "来源标识须以英文字母开头，只含字母、数字、下划线或连字符。")
        relative = text(source.get("path"), "来源路径", 240)
        p = PurePosixPath(relative)
        require(not p.is_absolute() and ".." not in p.parts and "\\" not in relative and
                p.suffix.lower() in {".md", ".txt", ".csv", ".json"}, "unsafe_path", "来源须为案例目录内相对文本文件。")
        target = no_symlinks(path.parent / relative)
        require(target.resolve().is_relative_to(path.parent.resolve()) and target != path,
                "unsafe_path", "来源不能指向案例自身或目录外。")
        canonical = str(target.resolve()).casefold()
        require(sid not in source_texts and canonical not in used_paths,
                "duplicate_id", "来源标识或路径重复。")
        used_paths.append(canonical)
        data = read_bytes(target)
        try:
            source_texts[sid] = data.decode("utf-8")
        except UnicodeError:
            raise QuoteError("invalid_encoding", "来源须为UTF-8文本。") from None
        hashes[f"source:{sid}"] = hashlib.sha256(data).hexdigest()
    weights = Decimal(0)
    for criterion in criteria:
        require(isinstance(criterion, dict), "invalid_input", "要求须为对象。")
        text(criterion.get("id"), "要求标识", 64)
        text(criterion.get("text"), "要求正文")
        require(type(criterion.get("mandatory")) is bool, "invalid_input", "mandatory须为布尔值。")
        weight = money(criterion.get("weight"), "要求权重", "100")
        maximum = money(criterion.get("max_score"), "评分上限", "100")
        require(maximum > 0, "invalid_input", "评分上限须大于0。")
        if criterion["mandatory"]:
            require(weight == 0, "invalid_input", "必备要求不参与加权评分，权重须为0。")
        else:
            require(weight > 0, "invalid_input", "评分要求权重须大于0。")
            weights += weight
    require(weights == 100, "invalid_input", "非必备评分要求权重须合计100。")
    unique([c["id"] for c in criteria], "要求")
    unique([text(o.get("id"), "报价标识", 64) for o in offers if isinstance(o, dict)], "报价")
    input_issues, costs = [], []
    if not currency:
        input_issues.append({"scope": "global", "category": "evaluation",
                             "message": "项目缺少明确币种，不能比较或排名。"})
    for offer in offers:
        require(isinstance(offer, dict), "invalid_input", "报价须为对象。")
        oid = text(offer.get("id"), "报价标识", 64)
        text(offer.get("name"), "供应方名称", 200)
        allowed = offer.get("source_ids")
        require(isinstance(allowed, list) and allowed and all(isinstance(x, str) and x in source_texts for x in allowed),
                "invalid_input", "报价须声明有效source_ids。")
        unique(allowed, "报价来源")
        currency_ok = currency is not None and offer.get("currency") == currency
        offered_currency = offer.get("currency")
        require(offered_currency is None or (isinstance(offered_currency, str) and
                len(offered_currency) == 3 and offered_currency.isascii() and
                offered_currency.isupper() and offered_currency.isalpha()),
                "invalid_input", "报价币种须为三位大写字母或null。")
        if not currency_ok:
            input_issues.append({"scope": "offer", "offer_id": oid, "category": "evaluation",
                                 "message": f"报价{oid}币种缺失或不一致；本工具不查询或猜测汇率。"})
        rows = offer.get("costs")
        require(isinstance(rows, list) and 1 <= len(rows) <= 30, "invalid_input", "每份报价须有1–30条成本。")
        total, complete, details, ids = Decimal(0), True, [], []
        for row in rows:
            require(isinstance(row, dict), "invalid_input", "成本项须为对象。")
            ids.append(text(row.get("id"), "成本标识", 64))
            text(row.get("description"), "成本说明", 500)
            evidence(row.get("evidence"), source_texts, allowed)
            if any(row.get(k) is None for k in ("amount", "quantity", "occurrences")):
                complete = False
                input_issues.append({"scope": "offer", "offer_id": oid, "category": "evaluation",
                                     "message": f"报价{oid}成本{row['id']}缺少金额、数量或次数，不能推定为0。"})
                subtotal = None
            else:
                amount = money(row["amount"], "单价")
                quantity = money(row["quantity"], "数量", "1000000")
                count = row["occurrences"]
                require(quantity > 0 and type(count) is int and 1 <= count <= 10000,
                        "invalid_number", "数量须大于0，次数须为1–10000的整数。")
                subtotal = amount * quantity * count
                require(subtotal <= Decimal("100000000000000000000"), "invalid_number", "成本超过允许范围。")
                total += subtotal
            details.append({"id": row["id"], "description": row["description"], "subtotal": fmt(subtotal)})
        unique(ids, "成本")
        costs.append({"offer_id": oid, "currency": offer.get("currency"),
                      "total": fmt(total) if complete and currency_ok else None, "lines": details})
    binding = json.dumps(hashes, sort_keys=True, separators=(",", ":")).encode()
    return case, source_texts, hashes, hashlib.sha256(binding).hexdigest(), costs, input_issues


def inspect_case(case_path):
    with localcontext() as ctx:
        ctx.prec = 60
        case, _, hashes, digest, costs, input_issues = load_case(case_path)
    clarifications = [x["message"] for x in input_issues]
    return {"ok": True, "version": VERSION, "case_sha256": digest, "title": case["title"],
            "input_hashes": hashes, "costs": costs, "clarifications": clarifications, "input_issues": input_issues,
            "status": "clarification_required" if clarifications else "inputs_validated",
            "notice": "只验证输入、引文与金额；没有证明技术结论、成员参与或人工验收。"}


def load_report(path, role, digest, offers):
    record, data = read_json(path)
    require(type(record.get("schema_version")) is int and record["schema_version"] == 2,
            "invalid_report", "成员记录schema_version须为2；旧版文字问题不能自动归类，须保留原稿并重新形成新版记录。")
    require(record.get("role") == role, "invalid_report", "成员记录角色不符。")
    require(record.get("case_sha256") == digest, "stale_report", "输入已变更或成员记录对应其他案例；须重新评审。")
    allowed = {"schema_version", "role", "case_sha256", "notes", "issues"}
    allowed.update({"assessments"} if role == "technical" else {"totals"} if role == "commercial" else {"assessments", "totals"})
    require(set(record) == allowed, "invalid_report", "成员记录须含本角色的全部规定字段，不能增加未声明字段。")
    notes = record.get("notes")
    require(isinstance(notes, list) and len(notes) <= 50 and
            all(isinstance(x, str) and 0 < len(x.strip()) and len(x) <= 2000 for x in notes),
            "invalid_report", "notes须为有界非空说明列表；说明不代表问题已解决，不得把真实阻断问题移入说明。")
    issues = record.get("issues")
    require(isinstance(issues, list) and len(issues) <= 50,
            "invalid_report", "issues须为最多50条的结构化问题列表；没有问题时用空列表。")
    for issue in issues:
        require(isinstance(issue, dict), "invalid_report", "问题须为结构化对象，不能使用旧版文字字符串。")
        require(issue.get("scope") in ("global", "offer") and issue.get("category") in ("eligibility", "evaluation"),
                "invalid_report", "问题须明确global/offer范围及eligibility/evaluation类别。")
        keys = {"scope", "category", "message"} | ({"offer_id"} if issue["scope"] == "offer" else set())
        require(set(issue) == keys, "invalid_report", "问题字段不符；报价问题必须含有效offer_id，全局问题不能指定报价。")
        if issue["scope"] == "offer":
            require(isinstance(issue["offer_id"], str) and issue["offer_id"] in offers,
                    "invalid_report", "问题引用了未知报价。")
        text(issue.get("message"), "问题说明", 2000)
    return record, hashlib.sha256(data).hexdigest()


def assessment_map(report, case, sources):
    records = report.get("assessments")
    expected = {(o["id"], c["id"]) for o in case["offers"] for c in case["criteria"]}
    require(isinstance(records, list) and len(records) == len(expected), "invalid_report", "须逐份报价逐条覆盖全部要求。")
    mapped, criteria = {}, {c["id"]: c for c in case["criteria"]}
    offers = {o["id"]: o for o in case["offers"]}
    for row in records:
        require(isinstance(row, dict), "invalid_report", "评估项须为对象。")
        require(set(row) == {"offer_id", "criterion_id", "status", "score", "evidence", "rationale"},
                "invalid_report", "评估项须含完整规定字段，不能增加未声明字段。")
        key = (row.get("offer_id"), row.get("criterion_id"))
        require(key in expected and key not in mapped, "invalid_report", "评估项遗漏、重复或包含未知标识。")
        require(row.get("status") in {"pass", "fail", "unknown"}, "invalid_report", "评估状态须为pass/fail/unknown。")
        text(row.get("rationale"), "评估理由", 4000)
        refs = row.get("evidence")
        require(isinstance(refs, list) and len(refs) <= 5, "invalid_evidence", "每项证据最多5条。")
        require(row["status"] == "unknown" or refs, "invalid_evidence", "明确通过或失败必须提供来源证据。")
        for ref in refs:
            evidence(ref, sources, offers[key[0]]["source_ids"])
        criterion = criteria[key[1]]
        if criterion["mandatory"] or row["status"] == "unknown":
            require(row.get("score") is None, "invalid_report", "必备或未知项评分须为null。")
        else:
            value = money(row.get("score"), "评分", criterion["max_score"])
            require(row["status"] != "fail" or value == 0, "invalid_report", "评分失败项必须为0分。")
        mapped[key] = row
    return mapped


def totals_map(report, offers):
    rows = report.get("totals")
    require(isinstance(rows, list) and len(rows) == len(offers), "invalid_report", "成本记录须覆盖全部报价。")
    result = {}
    for row in rows:
        require(isinstance(row, dict), "invalid_report", "成本记录须为对象。")
        require(set(row) == {"offer_id", "total"}, "invalid_report", "合计记录仅可含offer_id与total。")
        oid = row.get("offer_id")
        require(oid in offers and oid not in result, "invalid_report", "成本报价标识重复或未知。")
        value = row.get("total")
        result[oid] = money(value, "复算合计", "10000000000000000000000") if value is not None else None
    return result


def evaluate(case_path, technical_path, commercial_path, review_path):
    with localcontext() as ctx:
        ctx.prec = 60
        case, sources, hashes, digest, costs, input_issues = load_case(case_path)
        oids = [o["id"] for o in case["offers"]]
        tech, th = load_report(technical_path, "technical", digest, oids)
        commercial, ch = load_report(commercial_path, "commercial", digest, oids)
        review, rh = load_report(review_path, "verifier", digest, oids)
        # Validate ALL reports, references and totals before deciding relevance.
        # Exclusion never makes malformed or stale evidence acceptable.
        tm, vm = assessment_map(tech, case, sources), assessment_map(review, case, sources)
        cm, rm = totals_map(commercial, oids), totals_map(review, oids)
        reports = (("技术", tech), ("商务", commercial), ("复核", review))
        compliance, eligibility = [], []
        for offer in case["offers"]:
            oid, failures, uncertainty, reasons = offer["id"], [], [], []
            for criterion in case["criteria"]:
                a, b = tm[(oid, criterion["id"])], vm[(oid, criterion["id"])]
                compliance.append({"offer_id": oid, "criterion_id": criterion["id"],
                                   "mandatory": criterion["mandatory"], "technical": a, "verification": b})
                if not criterion["mandatory"]:
                    continue
                if a["status"] == b["status"] == "fail":
                    failures.append(criterion["id"])
                    reasons.append(f"必备要求{criterion['id']}经技术与复核双方明确判定不符合：{a['rationale']}；独立复核：{b['rationale']}")
                if a["status"] != b["status"] or "unknown" in (a["status"], b["status"]):
                    uncertainty.append(criterion["id"])
                    reasons.append(f"必备要求{criterion['id']}的资格判断未知或双方不一致，不能自行排除或认定合格。")
            for role, report in reports:
                for issue in report["issues"]:
                    if issue["scope"] == "offer" and issue["offer_id"] == oid and issue["category"] == "eligibility":
                        uncertainty.append(issue["message"])
                        reasons.append(f"{role}尚有资格问题：{issue['message']}")
            state = "uncertain" if uncertainty else "excluded" if failures else "eligible"
            if not reasons:
                reasons.append("技术与复核对全部必备要求均明确通过，未报告报价资格问题。")
            eligibility.append({"offer_id": oid, "status": state, "reasons": reasons,
                                "exclusion_criteria": failures})
        states = {x["offer_id"]: x["status"] for x in eligibility}
        issues = []

        def add_issue(item, origin, kind="issue", criterion_id=None):
            oid = item.get("offer_id")
            blocking = (item["scope"] == "global" or item["category"] == "eligibility"
                        or states[oid] != "excluded")
            record = {**item, "origin": origin, "kind": kind, "blocking": blocking}
            if criterion_id is not None:
                record["criterion_id"] = criterion_id
            issues.append(record)

        for issue in input_issues:
            add_issue(issue, "输入")
        notes = []
        for role, report in reports:
            notes.extend(f"{role}说明：{note}" for note in report["notes"])
            for issue in report["issues"]:
                add_issue(issue, role)
        for cost in costs:
            oid = cost["offer_id"]
            expected = Decimal(cost["total"]) if cost["total"] is not None else None
            if cm[oid] != expected or rm[oid] != expected:
                add_issue({"scope": "offer", "offer_id": oid, "category": "evaluation",
                           "message": f"报价{oid}的成员合计与原始金额复算不一致。"}, "成本核对", "conflict")
        scores = {}
        for row in compliance:
            oid, cid, mandatory = row["offer_id"], row["criterion_id"], row["mandatory"]
            a, b = row["technical"], row["verification"]
            av = Decimal(a["score"]) if a.get("score") is not None else None
            bv = Decimal(b["score"]) if b.get("score") is not None else None
            category = "eligibility" if mandatory else "evaluation"
            if a["status"] != b["status"] or av != bv:
                add_issue({"scope": "offer", "offer_id": oid, "category": category,
                           "message": f"报价{oid}要求{cid}的技术判断或评分存在分歧。"}, "交叉复核", "conflict", cid)
            if "unknown" in (a["status"], b["status"]):
                add_issue({"scope": "offer", "offer_id": oid, "category": category,
                           "message": f"报价{oid}要求{cid}尚未核实，未补写评分。"}, "逐项核对", "unknown", cid)
            elif not mandatory and states[oid] == "eligible":
                criterion = next(c for c in case["criteria"] if c["id"] == cid)
                scores[oid] = scores.get(oid, Decimal(0)) + av / Decimal(criterion["max_score"]) * Decimal(criterion["weight"])
        conflicts = [x["message"] for x in issues if x["blocking"] and x["kind"] == "conflict"]
        clarifications = [x["message"] for x in issues if x["blocking"] and x["kind"] != "conflict"]
        warnings = [f"{x['origin']}：{x['message']}（报价已明确排除，保留记录，不影响其余合格报价排名）"
                    for x in issues if not x["blocking"]]
        eligible = [oid for oid in oids if states[oid] == "eligible"]
        rankings = []
        if not clarifications and not conflicts and eligible:
            # Only comparable, eligible costs enter either Decimal conversion or the minimum.
            totals = {x["offer_id"]: Decimal(x["total"]) for x in costs if x["offer_id"] in eligible}
            minimum = min(totals.values())
            require(minimum > 0, "invalid_number", "排名所用可比总成本须大于0。")
            for oid in eligible:
                total = totals[oid]
                combined = scores[oid] * Decimal(case["technical_weight"]) / 100 + minimum / total * Decimal(case["cost_weight"])
                rankings.append({"offer_id": oid, "technical_score": fmt(scores[oid]), "total": fmt(total), "combined_score": fmt(combined)})
            rankings.sort(key=lambda x: Decimal(x["combined_score"]), reverse=True)
            previous, rank = None, 0
            for index, row in enumerate(rankings, 1):
                if row["combined_score"] != previous:
                    rank = index
                row["rank"] = rank
                previous = row["combined_score"]
        status = "clarification_required" if clarifications or conflicts else "reviewed" if eligible else "no_eligible_offer"
        return {"ok": True, "version": VERSION, "report_schema_version": 2,
                "title": case["title"], "case_sha256": digest,
                "input_hashes": hashes, "report_hashes": {"technical": th, "commercial": ch, "verifier": rh},
                "status": status, "currency": case.get("currency"), "horizon_months": case["horizon_months"],
                "ranking_method": case["ranking_method"], "eligibility": eligibility,
                "costs": costs, "compliance": compliance, "rankings": rankings,
                "issues": issues, "notes": notes, "warnings": warnings,
                "clarifications": clarifications, "conflicts": conflicts,
                "participation_verified": False,
                "notice": "本结果仅为有界算术、引文及成员记录一致性检查。记录中的角色字段不证明真实参与或独立性；引文存在不证明语义正确。用户决定是否采纳，不自动授标。"}


def safe_csv(rows):
    stream = io.StringIO(newline="")
    writer = csv.writer(stream)
    for row in rows:
        writer.writerow([("'" + str(x)) if str(x).lstrip().startswith(("=", "+", "-", "@", "\t", "\r")) else str(x) for x in row])
    return "\ufeff" + stream.getvalue()


def render(result):
    e = lambda x: html.escape(str(x), quote=True)
    labels = {"reviewed": "已完成合格报价排名，请人工核对；排除项与非阻断警示另列", "clarification_required": "存在影响结果的阻断问题，需要澄清，未生成排名", "no_eligible_offer": "没有符合全部必备要求的报价"}
    states = {"eligible": "必备要求符合", "excluded": "已排除，不参与排名", "uncertain": "资格待澄清"}
    judgments = {"pass": "符合", "fail": "不符合", "unknown": "待核实（unknown）"}
    rows = "".join(f"<tr><td>{e(x['offer_id'])}</td><td>{e(x['currency'] or '未知')}</td><td>{e(x['total'] if x['total'] is not None else '未知')}</td></tr>" for x in result["costs"])
    ranking = "".join(f"<tr><td>{x['rank']}</td><td>{e(x['offer_id'])}</td><td>{e(x['technical_score'])}</td><td>{e(x['combined_score'])}</td></tr>" for x in result["rankings"])
    admission = "".join(f"<tr><td>{e(x['offer_id'])}</td><td>{e(states[x['status']])}</td><td>{e('；'.join(x['reasons']))}</td></tr>" for x in result["eligibility"])
    compliance = []
    for row in result["compliance"]:
        a, b = row["technical"], row["verification"]
        refs = "；".join(f"{r['source_id']}:{r['line']}「{r['quote']}」" for r in b["evidence"])
        compliance.append(f"<tr><td>{e(row['offer_id'])}</td><td>{e(row['criterion_id'])}</td><td>{e(judgments[a['status']])}</td><td>{e(judgments[b['status']])}</td><td>{e(b['rationale'])}<br>{e(refs)}</td></tr>")
    def listing(items):
        return "".join(f"<li>{e(x)}</li>" for x in items) or "<li>无</li>"
    return f'''<!doctype html><html lang="zh-CN"><meta charset="utf-8"><meta name="viewport" content="width=device-width"><meta http-equiv="Content-Security-Policy" content="default-src 'none'; style-src 'unsafe-inline'; base-uri 'none'; form-action 'none'"><title>采购报价比选复核</title><style>body{{font:16px/1.6 system-ui,sans-serif;max-width:1100px;margin:40px auto;padding:0 20px;background:#f5f5ef;color:#18352e}}table{{border-collapse:collapse;width:100%;background:white;margin:16px 0}}td,th{{border:1px solid #bbc9c1;padding:10px;text-align:left;overflow-wrap:anywhere}}aside{{padding:16px;background:#e4ecdf}}code{{overflow-wrap:anywhere}}</style><h1>{e(result['title'])}</h1><p>采购报价比选复核专家团 · v{VERSION} · {result['horizon_months']}个月</p><aside>{e(labels[result['status']])}</aside><h2>必备资格与排除理由</h2><table><tr><th>报价</th><th>资格状态</th><th>依据与理由</th></tr>{admission}</table><h2>声明成本复算</h2><table><tr><th>报价</th><th>币种</th><th>声明合计（不代表合格）</th></tr>{rows}</table><h2>按冻结规则的排序</h2><table><tr><th>名次</th><th>报价</th><th>技术分</th><th>综合分</th></tr>{ranking}</table><p>仅合格报价参与最低成本基准与排名；资格不确定或可能影响合格报价排序的缺口/分歧仍会阻断。明确排除报价的非必要细节保留为警示，不补写未知评分。</p><h2>逐项评估与复核</h2><table><tr><th>报价</th><th>要求</th><th>技术判断</th><th>复核判断</th><th>复核理由及原文</th></tr>{''.join(compliance)}</table><h2>影响排名的阻断问题与分歧</h2><ul>{listing(result['clarifications'] + result['conflicts'])}</ul><h2>非阻断警示（保留未知与分歧）</h2><ul>{listing(result['warnings'])}</ul><h2>信息性复核说明</h2><ul>{listing(result['notes'])}</ul><h2>边界与追溯</h2><p>{e(result['notice'])}</p><p>输入摘要 <code>{result['case_sha256']}</code></p><p>金额按输入的单价×数量×次数累加，不推定税费、汇率或次数，不自动根据月数填充。</p></html>'''


def render_markdown(result):
    states = {"eligible": "必备要求符合", "excluded": "已排除", "uncertain": "资格待澄清"}
    sections = [f"# {result['title']}", f"版本：{VERSION}；状态：{result['status']}", "## 必备资格与排除理由"]
    sections.extend(f"- 报价{x['offer_id']}：{states[x['status']]}；{'；'.join(x['reasons'])}" for x in result["eligibility"])
    sections.append("## 合格报价排名")
    sections.extend(f"- 第{x['rank']}名：报价{x['offer_id']}；技术分{x['technical_score']}；综合分{x['combined_score']}" for x in result["rankings"])
    if not result["rankings"]:
        sections.append("未生成排名；检查以下阻断问题或无合格报价原因。")
    for title, items in (("阻断问题与分歧", result["clarifications"] + result["conflicts"]),
                         ("非阻断警示", result["warnings"]), ("信息性说明", result["notes"])):
        sections.append("## " + title)
        sections.extend("- " + x for x in items) if items else sections.append("- 无")
    sections.extend(("## 边界与追溯", result["notice"], "输入摘要：" + result["case_sha256"]))
    return "\n\n".join(sections) + "\n"


def deliver(case_path, technical_path, commercial_path, review_path, output_dir):
    result = evaluate(case_path, technical_path, commercial_path, review_path)
    output = no_symlinks(output_dir)
    require(Path(output_dir).is_absolute(), "unsafe_path", "交付目录须为明确的绝对路径。")
    require(not output.exists(), "output_exists", "交付目录已存在；拒绝覆盖，请由用户指定新目录。")
    require(output.parent.is_dir(), "missing_directory", "交付目录的父目录须已存在。")
    paths = [no_symlinks(p) for p in (case_path, technical_path, commercial_path, review_path)]
    # Read all snapshots before creating any output. A changed input invalidates reports.
    case_name = paths[0].name
    snapshots = {f"inputs/case/{case_name}": read_bytes(paths[0])}
    snapshots.update({f"inputs/reports/{name}": read_bytes(p) for name, p in
                      zip(("technical.json", "commercial.json", "verifier.json"), paths[1:])})
    case, raw = read_json(case_path)
    for source in case["sources"]:
        snapshots[f"inputs/case/{PurePosixPath(source['path']).as_posix()}"] = read_bytes(Path(case_path).parent / source["path"])
    for name, key in ((case_name, "case.json"), *[(PurePosixPath(s['path']).as_posix(), f"source:{s['id']}") for s in case["sources"]]):
        require(hashlib.sha256(snapshots[f"inputs/case/{name}"]).hexdigest() == result["input_hashes"][key],
                "stale_report", "交付快照与已经评审的来源不一致。")
    for name, role in (("technical.json", "technical"), ("commercial.json", "commercial"), ("verifier.json", "verifier")):
        require(hashlib.sha256(snapshots[f"inputs/reports/{name}"]).hexdigest() == result["report_hashes"][role],
                "stale_report", "交付快照与已经检查的成员记录不一致。")
    fresh = evaluate(case_path, technical_path, commercial_path, review_path)
    require(fresh == result, "stale_report", "交付前输入或成员记录发生变化，请重新评审。")
    states = {"eligible": "必备要求符合", "excluded": "已排除", "uncertain": "资格待澄清"}
    admission = {x["offer_id"]: states[x["status"]] for x in result["eligibility"]}
    rows = [["报价", "资格状态", "要求", "必备", "技术判断", "复核判断", "复核理由", "证据", "阻断问题或非阻断警示"]]
    for row in result["compliance"]:
        b = row["verification"]
        relevant = [x for x in result["issues"] if x["scope"] == "global" or
                    (x.get("offer_id") == row["offer_id"] and x.get("criterion_id", row["criterion_id"]) == row["criterion_id"])]
        hints = "；".join(("阻断：" if x["blocking"] else "非阻断警示：") + x["message"] for x in relevant)
        rows.append([row["offer_id"], admission[row["offer_id"]], row["criterion_id"], row["mandatory"], row["technical"]["status"], b["status"], b["rationale"], json.dumps(b["evidence"], ensure_ascii=False), hints])
    contents = {"comparison.html": render(result).encode(),
                "evaluation.json": (json.dumps(result, ensure_ascii=False, indent=2) + "\n").encode(),
                "compliance.csv": safe_csv(rows).encode(),
                "costs.csv": safe_csv([["报价", "资格状态", "币种", "比较期（月）", "声明总成本（不代表合格）"], *[[c["offer_id"], admission[c["offer_id"]], c["currency"] or "未知", result["horizon_months"], c["total"] if c["total"] is not None else "未知"] for c in result["costs"]]]).encode(),
                "review.md": render_markdown(result).encode(), **snapshots}
    inventory = {name: hashlib.sha256(data).hexdigest() for name, data in contents.items()}
    contents["artifact.json"] = (json.dumps({"version": VERSION, "case_sha256": result["case_sha256"], "files_sha256": inventory}, indent=2) + "\n").encode()
    stage = Path(tempfile.mkdtemp(prefix=".quote-review-", dir=output.parent))
    created = []
    owned_dirs = []
    try:
        for name, data in contents.items():
            p = stage / name
            p.parent.mkdir(parents=True, exist_ok=True)
            p.write_bytes(data)
        try:
            output.mkdir(mode=0o700)
            owned_dirs.append((output, output.stat()))
        except FileExistsError:
            raise QuoteError("output_exists", "交付目录已存在，拒绝覆盖。") from None
        directories = {parent for name in contents for parent in (output / name).parents if parent != output and parent.is_relative_to(output)}
        for directory in sorted(directories, key=lambda p: len(p.parts)):
            directory.mkdir(mode=0o700)
            owned_dirs.append((directory, directory.stat()))
        for name in contents:
            p = output / name
            # Exclusive hard links prevent overwriting even with concurrent creation.
            os.link(stage / name, p)
            created.append(p)
    except Exception:
        # Only remove paths still pointing at this operation's staged files.
        for p in reversed(created):
            original = stage / p.relative_to(output)
            if p.is_file() and not p.is_symlink() and os.path.samestat(p.stat(), original.stat()):
                p.unlink()
        for p, original_stat in reversed(owned_dirs):
            try:
                if not p.is_symlink() and os.path.samestat(p.stat(), original_stat):
                    p.rmdir()
            except OSError:
                pass
        raise
    finally:
        shutil.rmtree(stage)
    return {"ok": True, "version": VERSION, "status": result["status"], "output_dir": str(output),
            "html_path": str(output / "comparison.html"), "case_sha256": result["case_sha256"],
            "files_sha256": inventory, "participation_verified": False}


class ChineseParser(argparse.ArgumentParser):
    def __init__(self, *args, **kwargs):
        kwargs["add_help"] = False
        super().__init__(*args, **kwargs)
        self.add_argument("-h", "--help", action="help", help="显示帮助并退出")

    def format_help(self):
        return super().format_help().replace("usage: ", "用法：").replace(
            "positional arguments:", "位置参数：").replace("options:", "选项：")

    def error(self, message):
        print(json.dumps({"ok": False, "version": VERSION, "error": {
            "code": "invalid_arguments", "message": "命令参数缺失或无效；请查看中文使用说明与 --help。"}}, ensure_ascii=False))
        raise SystemExit(2)


def main(argv=None):
    parser = ChineseParser(description="采购报价比选复核：本地输入检查与新目录交付。")
    sub = parser.add_subparsers(dest="action", required=True)
    inspect = sub.add_parser("inspect", help="只读检查来源、输入摘要和金额")
    inspect.add_argument("--case", required=True)
    export = sub.add_parser("deliver", help="检查三份成员记录后交付到新目录")
    for name in ("case", "technical", "commercial", "review", "output-dir"):
        export.add_argument("--" + name, required=True)
    args = parser.parse_args(argv)
    try:
        result = inspect_case(Path(args.case)) if args.action == "inspect" else deliver(
            Path(args.case), Path(args.technical), Path(args.commercial), Path(args.review), Path(args.output_dir))
    except QuoteError as exc:
        result = {"ok": False, "version": VERSION, "error": {"code": exc.code, "message": str(exc)}}
    except (OSError, TypeError, KeyError, ArithmeticError):
        result = {"ok": False, "version": VERSION, "error": {"code": "invalid_input", "message": "文件操作或输入结构无效；未完成交付，请检查输入和目录权限。"}}
    print(json.dumps(result, ensure_ascii=False, indent=2))
    return 0 if result["ok"] else 1


if __name__ == "__main__":
    sys.exit(main())
