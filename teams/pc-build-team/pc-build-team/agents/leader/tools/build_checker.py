"""装机专家团的配置校验与双语 PDF 导出工具。

validate：按硬规则（不兼容即失败）和软规则（风险提示）逐条检查一套或多套配置。
export：在所有配置都没有硬失败、价格未过期时，把团队写好的中英双语 Markdown 报告转成 PDF，
并在 {{块名}} 占位处插入由已校验数据绘制的表格和图。工具不联网、不购买、不覆盖已有文件。
"""
import asyncio
import html
import os
import re
import shutil
import subprocess
import tempfile
from datetime import date
from pathlib import Path
from typing import Annotated, Literal

from openjiuwen.core.foundation.tool import Tool, ToolCard
from pydantic import BaseModel, ConfigDict, Field

MAX_PRICE_AGE_DAYS = 7
PSU_MIN_HEADROOM = 1.3  # 推荐电源额定功率 ≥ 估算整机功耗 × 1.3
BASE_SYSTEM_W = 60  # 主板、内存、风扇等基础功耗估算
DRIVE_W = 8


class Model(BaseModel):
    model_config = ConfigDict(extra="forbid", allow_inf_nan=False)


Short = Annotated[str, Field(min_length=1, max_length=200, pattern=r"\S")]


class Bi(Model):
    """一段双语文本：中文与英文含义必须一致。"""

    zh: Annotated[str, Field(min_length=1, max_length=4000, pattern=r"\S")]
    en: Annotated[str, Field(min_length=1, max_length=4000, pattern=r"\S")]


Slot = Literal["cpu", "motherboard", "ram", "gpu", "storage", "psu", "case", "cooler", "fan", "other"]


class Specs(Model):
    socket: str | None = None
    tdp_w: float | None = Field(default=None, ge=0, le=1000, description="CPU 最大功耗（W）")
    memory_types: list[Literal["DDR4", "DDR5"]] | None = None
    has_igpu: bool | None = None
    boxed_cooler: bool | None = None
    chipset: str | None = None
    form_factor: str | None = Field(default=None, description="主板：ATX/mATX/ITX/E-ATX；电源：ATX/SFX/SFX-L")
    memory_type: Literal["DDR4", "DDR5"] | None = None
    ram_slots: int | None = Field(default=None, ge=1, le=8)
    m2_slots: int | None = Field(default=None, ge=0, le=8)
    m2_slot_names: list[Short] | None = None
    dimm_slot_names: list[Short] | None = Field(default=None, max_length=8, description="主板内存插槽名称，按从靠近 CPU 起的顺序，如 DDR5_A1")
    eps8_required: int | None = Field(default=None, ge=0, le=3)
    bios_note: str | None = Field(default=None, max_length=300)
    modules: int | None = Field(default=None, ge=1, le=8)
    capacity_gb_per_module: float | None = Field(default=None, gt=0, le=512)
    speed_mts: int | None = Field(default=None, ge=1000, le=12000)
    length_mm: float | None = Field(default=None, gt=0, le=600)
    board_power_w: float | None = Field(default=None, ge=0, le=1500)
    power_connectors: dict[Literal["12v-2x6", "pcie8"], int] | None = None
    interface: Literal["m2_nvme", "m2_sata", "sata"] | None = None
    wattage_w: float | None = Field(default=None, gt=0, le=3000)
    connectors: dict[Literal["12v-2x6", "pcie8", "eps8"], int] | None = None
    supported_form_factors: list[str] | None = None
    max_gpu_length_mm: float | None = Field(default=None, gt=0, le=800)
    max_cooler_height_mm: float | None = Field(default=None, gt=0, le=300)
    radiator_mounts: list[int] | None = None
    psu_form_factors: list[str] | None = None
    depth_mm: float | None = Field(default=None, gt=0, le=1000, description="机箱深度（前后）")
    width_mm: float | None = Field(default=None, gt=0, le=600)
    height_mm: float | None = Field(default=None, gt=0, le=1000)
    cooler_type: Literal["air", "aio"] | None = None
    radiator_mm: int | None = Field(default=None, ge=80, le=480)
    sockets: list[str] | None = None


class Part(Model):
    slot: Slot
    model: Short
    qty: int = Field(default=1, ge=1, le=8)
    price: float = Field(ge=0, le=1e7, description="单价")
    currency: Annotated[str, Field(min_length=3, max_length=3)]
    shop: Short
    url: Annotated[str, Field(pattern=r"^https?://\S+$", max_length=600)]
    checked_date: date
    specs: Specs = Field(default_factory=Specs)
    note: Bi | None = None


class Build(Model):
    key: Literal["main", "budget", "performance"] = "main"
    name: Bi
    budget: float = Field(gt=0, le=1e7)
    currency: Annotated[str, Field(min_length=3, max_length=3)]
    parts: list[Part] = Field(min_length=1, max_length=40)


class Input(Model):
    action: Literal["validate", "export"] = "validate"
    builds: list[Build] = Field(min_length=1, max_length=3)
    user_budget: float | None = Field(default=None, gt=0, le=1e7,
                                      description="用户给的预算（与配置同币种）。填写后所有方案都按它检查预算，忽略各方案自填的 budget；export 必填")
    markdown_path: str | None = Field(default=None, description="export：团队写好的双语 Markdown 报告（绝对 .md 路径）")
    ram_slots_to_use: list[Short] = Field(default_factory=list, max_length=8, description="主板示意图高亮的内存插槽，用说明书名称")
    m2_boot_slot: str | None = Field(default=None, max_length=40, description="主板示意图高亮的系统盘 M.2 插槽")
    language_order: Literal["zh-en", "en-zh"] = "zh-en"
    output_path: str | None = None
    today: date | None = Field(default=None, description="校验价格时效的日期，默认今天")


# ---------- 校验 ----------

L = {
    "pass": ("通过", "Pass"), "warn": ("注意", "Warning"), "fail": ("失败", "Fail"), "unknown": ("未知", "Unknown"),
}


def _r(rule, status, zh, en, hard=True):
    return {"rule": rule, "status": status, "hard": hard, "zh": zh, "en": en}


def _one(parts, slot):
    found = [p for p in parts if p.slot == slot]
    return found[0] if found else None


def _unknown(rule, what_zh, what_en):
    return _r(rule, "unknown", f"缺少规格：{what_zh}，无法判定。", f"Missing spec: {what_en}; cannot decide.", hard=False)


def estimate_power(build: Build) -> dict:
    cpu, gpu = _one(build.parts, "cpu"), _one(build.parts, "gpu")
    drives = sum(p.qty for p in build.parts if p.slot == "storage")
    cpu_w = (cpu.specs.tdp_w or 0) if cpu else 0
    gpu_w = (gpu.specs.board_power_w or 0) * (gpu.qty if gpu else 0) if gpu else 0
    total = cpu_w + gpu_w + BASE_SYSTEM_W + DRIVE_W * drives
    return {"cpu_w": cpu_w, "gpu_w": gpu_w, "other_w": BASE_SYSTEM_W + DRIVE_W * drives,
            "estimated_w": round(total), "recommended_psu_w": round(total * PSU_MIN_HEADROOM)}


def check_build(build: Build, today: date) -> dict:
    p = build.parts
    res = []
    cpu, mb, ram, gpu = (_one(p, s) for s in ("cpu", "motherboard", "ram", "gpu"))
    psu, case, cooler = (_one(p, s) for s in ("psu", "case", "cooler"))
    storage = [x for x in p if x.slot == "storage"]

    for slot, zh in (("cpu", "处理器"), ("motherboard", "主板"), ("ram", "内存"), ("psu", "电源"), ("case", "机箱")):
        if not _one(p, slot):
            res.append(_r("required_parts", "fail", f"缺少必需配件：{zh}。", f"Missing required part: {slot}."))
    if not storage:
        res.append(_r("required_parts", "fail", "缺少存储设备。", "Missing storage."))
    for slot in ("cpu", "motherboard", "psu", "case", "cooler"):
        if sum(x.qty for x in p if x.slot == slot) > 1:
            res.append(_r("duplicate_slot", "fail", f"{slot} 只能有一个。", f"Only one {slot} is allowed."))

    if cpu and mb:
        a, b = cpu.specs.socket, mb.specs.socket
        if not a or not b:
            res.append(_unknown("cpu_socket", "处理器或主板插槽", "CPU or board socket"))
        elif a.strip().upper() != b.strip().upper():
            res.append(_r("cpu_socket", "fail", f"处理器插槽 {a} 与主板插槽 {b} 不匹配。", f"CPU socket {a} does not match board socket {b}."))
        else:
            res.append(_r("cpu_socket", "pass", f"插槽一致：{a}。", f"Socket matches: {a}."))
        if mb.specs.bios_note:
            res.append(_r("bios", "warn", f"BIOS 提示：{mb.specs.bios_note}", f"BIOS note: {mb.specs.bios_note}", hard=False))

    if ram and mb:
        a, b = ram.specs.memory_type, mb.specs.memory_type
        if not a or not b:
            res.append(_unknown("memory_type", "内存或主板内存类型", "RAM or board memory type"))
        elif a != b:
            res.append(_r("memory_type", "fail", f"内存为 {a}，主板只支持 {b}。", f"RAM is {a} but the board supports {b}."))
        else:
            res.append(_r("memory_type", "pass", f"内存类型一致：{a}。", f"Memory type matches: {a}."))
        if a and cpu and cpu.specs.memory_types and a not in cpu.specs.memory_types:
            res.append(_r("memory_type_cpu", "fail", f"处理器不支持 {a}。", f"CPU does not support {a}."))
        modules = (ram.specs.modules or 0) * ram.qty
        if modules and mb.specs.ram_slots:
            if modules > mb.specs.ram_slots:
                res.append(_r("ram_slots", "fail", f"{modules} 根内存超过主板 {mb.specs.ram_slots} 个插槽。",
                              f"{modules} modules exceed the board's {mb.specs.ram_slots} slots."))
            else:
                res.append(_r("ram_slots", "pass", f"{modules} 根内存，主板 {mb.specs.ram_slots} 个插槽。",
                              f"{modules} modules in {mb.specs.ram_slots} slots."))
        elif not modules:
            res.append(_unknown("ram_slots", "内存条数量", "module count"))
        if modules == 1:
            res.append(_r("dual_channel", "warn", "只有 1 根内存，无法组成双通道，性能会受影响。",
                          "Only one module: no dual channel, performance will suffer.", hard=False))

    if mb and case:
        ff, ok = mb.specs.form_factor, case.specs.supported_form_factors
        if not ff or not ok:
            res.append(_unknown("board_fit", "主板版型或机箱支持版型", "board form factor or case support"))
        elif ff.upper() not in {x.upper() for x in ok}:
            res.append(_r("board_fit", "fail", f"机箱不支持 {ff} 主板。", f"The case does not fit a {ff} board."))
        else:
            res.append(_r("board_fit", "pass", f"机箱支持 {ff} 主板。", f"The case fits a {ff} board."))

    if gpu and case:
        a, b = gpu.specs.length_mm, case.specs.max_gpu_length_mm
        if not a or not b:
            res.append(_unknown("gpu_length", "显卡长度或机箱显卡限长", "GPU length or case limit"))
        elif a > b:
            res.append(_r("gpu_length", "fail", f"显卡长 {a:g} mm，超过机箱限长 {b:g} mm。", f"GPU is {a:g} mm, over the case limit of {b:g} mm."))
        else:
            st = "warn" if b - a < 10 else "pass"
            res.append(_r("gpu_length", st, f"显卡 {a:g} mm，限长 {b:g} mm，余量 {b - a:g} mm。",
                          f"GPU {a:g} mm, limit {b:g} mm, {b - a:g} mm spare.", hard=st == "pass"))

    if cpu and not cooler:
        if cpu.specs.boxed_cooler:
            res.append(_r("cooler", "warn", "使用处理器原装散热器，高负载时噪音和温度偏高。",
                          "Using the boxed cooler; expect more noise and heat under load.", hard=False))
        else:
            res.append(_r("cooler", "fail", "处理器不带散热器，需要单独购买。", "The CPU has no boxed cooler; add one."))
    if cooler:
        s = cooler.specs
        if s.sockets and cpu and cpu.specs.socket:
            if cpu.specs.socket.strip().upper() not in {x.strip().upper() for x in s.sockets}:
                res.append(_r("cooler_socket", "fail", f"散热器不支持 {cpu.specs.socket} 插槽。", f"Cooler does not support {cpu.specs.socket}."))
            else:
                res.append(_r("cooler_socket", "pass", f"散热器支持 {cpu.specs.socket}。", f"Cooler supports {cpu.specs.socket}."))
        else:
            res.append(_unknown("cooler_socket", "散热器支持的插槽", "cooler socket support"))
        if s.cooler_type == "aio":
            if not s.radiator_mm or not case or not case.specs.radiator_mounts:
                res.append(_unknown("radiator_fit", "冷排尺寸或机箱冷排位", "radiator size or case mounts"))
            elif s.radiator_mm not in case.specs.radiator_mounts:
                res.append(_r("radiator_fit", "fail", f"机箱不支持 {s.radiator_mm} mm 冷排。", f"The case has no {s.radiator_mm} mm radiator mount."))
            else:
                res.append(_r("radiator_fit", "pass", f"机箱支持 {s.radiator_mm} mm 冷排。", f"The case mounts a {s.radiator_mm} mm radiator."))
        else:
            a = s.height_mm
            b = case.specs.max_cooler_height_mm if case else None
            if not a or not b:
                res.append(_unknown("cooler_height", "散热器高度或机箱限高", "cooler height or case limit"))
            elif a > b:
                res.append(_r("cooler_height", "fail", f"散热器高 {a:g} mm，超过机箱限高 {b:g} mm。", f"Cooler is {a:g} mm, over the case limit of {b:g} mm."))
            else:
                st = "warn" if b - a < 5 else "pass"
                res.append(_r("cooler_height", st, f"散热器 {a:g} mm，限高 {b:g} mm，余量 {b - a:g} mm。",
                              f"Cooler {a:g} mm, limit {b:g} mm, {b - a:g} mm spare.", hard=st == "pass"))

    if mb:
        m2 = sum(x.qty for x in storage if x.specs.interface in ("m2_nvme", "m2_sata"))
        if m2 and mb.specs.m2_slots is None:
            res.append(_unknown("m2_slots", "主板 M.2 插槽数", "board M.2 slot count"))
        elif m2 > (mb.specs.m2_slots or 0):
            res.append(_r("m2_slots", "fail", f"{m2} 块 M.2 硬盘超过主板 {mb.specs.m2_slots} 个 M.2 插槽。",
                          f"{m2} M.2 drives exceed the board's {mb.specs.m2_slots} slots."))
        elif m2:
            res.append(_r("m2_slots", "pass", f"{m2} 块 M.2 硬盘，主板 {mb.specs.m2_slots} 个插槽。", f"{m2} M.2 drives in {mb.specs.m2_slots} slots."))

    power = estimate_power(build)
    if psu:
        w, conn = psu.specs.wattage_w, psu.specs.connectors or {}
        if not w:
            res.append(_unknown("psu_wattage", "电源额定功率", "PSU wattage"))
        elif w < power["estimated_w"]:
            res.append(_r("psu_wattage", "fail", f"电源 {w:g} W 低于估算功耗 {power['estimated_w']} W。",
                          f"PSU {w:g} W is below the estimated {power['estimated_w']} W draw."))
        elif w < power["recommended_psu_w"]:
            res.append(_r("psu_wattage", "warn", f"电源 {w:g} W，建议至少 {power['recommended_psu_w']} W（留 30% 余量）。",
                          f"PSU {w:g} W; at least {power['recommended_psu_w']} W is recommended (30% headroom).", hard=False))
        else:
            res.append(_r("psu_wattage", "pass", f"电源 {w:g} W，估算功耗 {power['estimated_w']} W，余量充足。",
                          f"PSU {w:g} W against an estimated {power['estimated_w']} W; enough headroom."))
        if gpu and gpu.specs.power_connectors:
            for k, need in gpu.specs.power_connectors.items():
                need *= gpu.qty
                have = None if psu.specs.connectors is None else conn.get(k, 0)
                if have is None:
                    res.append(_unknown("psu_gpu_connectors", f"电源 {k} 接口数量", f"PSU {k} connector count"))
                elif have < need:
                    res.append(_r("psu_gpu_connectors", "fail", f"显卡需要 {need} 个 {k}，电源只有 {have} 个。", f"GPU needs {need} × {k}; the PSU has {have}."))
                else:
                    res.append(_r("psu_gpu_connectors", "pass", f"{k} 接口足够（需 {need}，有 {have}）。", f"{k} connectors OK (need {need}, have {have})."))
        elif gpu:
            res.append(_unknown("psu_gpu_connectors", "显卡供电接口", "GPU power connectors"))
        if mb and mb.specs.eps8_required is not None:
            have = None if psu.specs.connectors is None else conn.get("eps8", 0)
            if have is None:
                res.append(_unknown("psu_eps", "电源 CPU 供电（EPS 8-pin）数量", "PSU EPS 8-pin count"))
            elif have < mb.specs.eps8_required:
                res.append(_r("psu_eps", "fail", f"主板需要 {mb.specs.eps8_required} 个 CPU 8-pin，电源只有 {have} 个。",
                              f"The board needs {mb.specs.eps8_required} × EPS 8-pin; the PSU has {have}."))
            else:
                res.append(_r("psu_eps", "pass", "CPU 供电接口足够。", "EPS connectors OK."))
        if case and psu.specs.form_factor and case.specs.psu_form_factors:
            if psu.specs.form_factor.upper() not in {x.upper() for x in case.specs.psu_form_factors}:
                res.append(_r("psu_fit", "fail", f"机箱不支持 {psu.specs.form_factor} 电源。", f"The case does not take a {psu.specs.form_factor} PSU."))
            else:
                res.append(_r("psu_fit", "pass", f"机箱支持 {psu.specs.form_factor} 电源。", f"The case takes a {psu.specs.form_factor} PSU."))
    if cpu and not gpu:
        if cpu.specs.has_igpu is False:
            res.append(_r("display_output", "fail", "处理器没有核显，又没有独立显卡，无法输出画面。", "No integrated graphics and no GPU: no display output."))
        elif cpu.specs.has_igpu is None:
            res.append(_unknown("display_output", "处理器是否有核显", "whether the CPU has integrated graphics"))

    stale, cur = [], set()
    for x in p:
        age = (today - x.checked_date).days
        if age > MAX_PRICE_AGE_DAYS or age < 0:
            stale.append(x.model)
        if x.currency.upper() != build.currency.upper():
            cur.add(x.currency.upper())
    if cur:
        res.append(_r("currency", "fail", f"配件币种 {', '.join(sorted(cur))} 与预算币种 {build.currency} 不一致。",
                      f"Part currency {', '.join(sorted(cur))} differs from budget currency {build.currency}."))
    if stale:
        res.append(_r("price_age", "fail", f"价格超过 {MAX_PRICE_AGE_DAYS} 天或日期无效，需重新核价：{'、'.join(stale)}。",
                      f"Prices older than {MAX_PRICE_AGE_DAYS} days or dated in the future; recheck: {', '.join(stale)}."))
    total = round(sum(x.price * x.qty for x in p), 2)
    if total > build.budget:
        res.append(_r("budget", "warn", f"总价 {total:,.2f} 超出预算 {build.budget:,.2f}（+{(total / build.budget - 1) * 100:.1f}%）。",
                      f"Total {total:,.2f} is over the {build.budget:,.2f} budget (+{(total / build.budget - 1) * 100:.1f}%).", hard=False))
    else:
        res.append(_r("budget", "pass", f"总价 {total:,.2f}，预算 {build.budget:,.2f}。", f"Total {total:,.2f} within the {build.budget:,.2f} budget."))

    fails = [r for r in res if r["status"] == "fail"]
    return {
        "key": build.key, "name": build.name.model_dump(), "currency": build.currency.upper(),
        "total": total, "budget": build.budget, "power": power,
        "verdict": "fail" if fails else ("warn" if any(r["status"] in ("warn", "unknown") for r in res) else "pass"),
        "fail_count": len(fails), "results": res,
    }


# ---------- 图表（SVG，全部由校验后的数据绘制） ----------

PALETTE = ["#1f4e79", "#2e86ab", "#59a5d8", "#84c0e7", "#f6ae2d", "#f26419", "#86bbd8", "#33658a", "#758e4f", "#9a8c98"]
SLOT_ZH = {"cpu": "处理器", "motherboard": "主板", "ram": "内存", "gpu": "显卡", "storage": "存储", "psu": "电源",
           "case": "机箱", "cooler": "散热器", "fan": "风扇", "other": "其他"}
SLOT_EN = {"cpu": "CPU", "motherboard": "Motherboard", "ram": "Memory", "gpu": "GPU", "storage": "Storage", "psu": "PSU",
           "case": "Case", "cooler": "Cooler", "fan": "Fans", "other": "Other"}


def e(x) -> str:
    return html.escape(str(x), quote=True)


def _tw(text: str, fs: float) -> float:
    """估算文字宽度（像素）：中日韩字符约 1 个字号宽，其余约 0.6 个字号宽。"""
    return sum(fs if ord(ch) > 0x2E80 else fs * 0.6 for ch in str(text))


def _t(x, y, text, fs=11, maxw=None, anchor="start", **attrs) -> str:
    """输出一段 SVG 文字；估算宽度超过 maxw 时用 textLength 压缩，保证不越界、不丢字。"""
    extra = "".join(f' {k.replace("_", "-")}="{v}"' for k, v in attrs.items())
    fit = ""
    if maxw is not None and _tw(text, fs) > maxw:
        fit = f' textLength="{maxw:.0f}" lengthAdjust="spacingAndGlyphs"'
    return f'<text x="{x:.1f}" y="{y:.1f}" font-size="{fs}" text-anchor="{anchor}"{fit}{extra}>{e(text)}</text>'


def svg_budget(build: Build, total: float) -> str:
    by = {}
    for x in build.parts:
        by[x.slot] = by.get(x.slot, 0) + x.price * x.qty
    W, H, bar = 760, 120, 28
    scale = max(total, build.budget)
    out = [f'<svg viewBox="0 0 {W} {H}" width="100%" xmlns="http://www.w3.org/2000/svg" font-size="11">']
    x0 = 10
    for i, (slot, v) in enumerate(sorted(by.items(), key=lambda t: -t[1])):
        w = (W - 20) * v / scale
        c = PALETTE[i % len(PALETTE)]
        out.append(f'<rect x="{x0:.1f}" y="20" width="{w:.1f}" height="{bar}" fill="{c}"/>')
        if w > 52:
            out.append(_t(x0 + 4, 38, f"{SLOT_ZH[slot]} {v / total * 100:.0f}%", 11, w - 8, fill="#fff"))
        x0 += w
    bx = 10 + (W - 20) * build.budget / scale
    out.append(f'<line x1="{bx:.1f}" y1="12" x2="{bx:.1f}" y2="56" stroke="#c0392b" stroke-width="2" stroke-dasharray="4 3"/>')
    out.append(_t(min(bx, W - 4), 72, f"预算 Budget {build.budget:,.0f}", 11, anchor="end" if bx > W - 160 else "start", fill="#c0392b"))
    lx, ly = 10, 96
    for i, (slot, v) in enumerate(sorted(by.items(), key=lambda t: -t[1])):
        out.append(f'<rect x="{lx}" y="{ly - 9}" width="10" height="10" fill="{PALETTE[i % len(PALETTE)]}"/>'
                   + _t(lx + 14, ly, f"{SLOT_ZH[slot]} {SLOT_EN[slot]}", 11, 110))
        lx += 128
        if lx > W - 120:
            lx, ly = 10, ly + 16
    out.append("</svg>")
    return "".join(out)


def svg_power(power: dict, psu_w: float | None) -> str:
    W, H = 760, 110
    top = max(psu_w or 0, power["recommended_psu_w"], power["estimated_w"]) * 1.1
    sx = (W - 20) / top
    out = [f'<svg viewBox="0 0 {W} {H}" width="100%" xmlns="http://www.w3.org/2000/svg" font-size="11">']
    x = 10
    for v, c, zh, en in ((power["cpu_w"], "#1f4e79", "处理器", "CPU"), (power["gpu_w"], "#2e86ab", "显卡", "GPU"),
                         (power["other_w"], "#84c0e7", "其他", "Other")):
        if v:
            out.append(f'<rect x="{x:.1f}" y="24" width="{v * sx:.1f}" height="26" fill="{c}"/>')
            if v * sx > 70:
                out.append(_t(x + 4, 41, f"{zh} {en} {v:g} W", 11, v * sx - 8, fill="#fff"))
            x += v * sx
    rx = 10 + power["recommended_psu_w"] * sx
    out.append(f'<rect x="{x:.1f}" y="24" width="{max(rx - x, 0):.1f}" height="26" fill="#f6ae2d" opacity="0.35"/>')
    out.append(_t(10, 16, f'估算功耗 Estimated draw {power["estimated_w"]} W · 建议电源 Recommended ≥ {power["recommended_psu_w"]} W', 11, W - 20))
    if psu_w:
        px = 10 + psu_w * sx
        col = "#27ae60" if psu_w >= power["recommended_psu_w"] else ("#f39c12" if psu_w >= power["estimated_w"] else "#c0392b")
        out.append(f'<line x1="{px:.1f}" y1="18" x2="{px:.1f}" y2="62" stroke="{col}" stroke-width="3"/>'
                   + _t(px, 78, f"电源额定 PSU rating {psu_w:g} W", 11, anchor="end" if px > W - 170 else "start", fill=col))
    for t in range(0, int(top) + 1, 200 if top > 900 else 100):
        out.append(_t(10 + t * sx, 100, t, 9, anchor="end" if 10 + t * sx > W - 30 else "start", fill="#888"))
    out.append("</svg>")
    return "".join(out)


def svg_clearance(rows: list[tuple[str, float, float]]) -> str:
    if not rows:
        return ""
    W = 760
    H = 26 + 34 * len(rows)
    sx = (W - 230 - max(_tw(f"{u:g} / {m:g} mm", 11) for _, u, m in rows) - 10) / max(r[2] for r in rows)
    out = [f'<svg viewBox="0 0 {W} {H}" width="100%" xmlns="http://www.w3.org/2000/svg" font-size="11">']
    for i, (label, used, limit) in enumerate(rows):
        y = 14 + 34 * i
        col = "#c0392b" if used > limit else ("#f39c12" if limit - used < 10 else "#27ae60")
        out.append(_t(0, y + 15, label, 11, 214) +
                   f'<rect x="220" y="{y + 2}" width="{limit * sx:.1f}" height="20" fill="#eef2f6" stroke="#9aa9b8"/>'
                   f'<rect x="220" y="{y + 6}" width="{min(used, limit * 1.08) * sx:.1f}" height="12" fill="{col}"/>'
                   f'<text x="{224 + limit * sx:.1f}" y="{y + 16}" fill="#555">{used:g} / {limit:g} mm</text>')
    out.append("</svg>")
    return "".join(out)


def svg_case_fit(build: Build) -> str:
    """机箱侧视示意（按比例）：机箱深度 × 高度，显卡长度与散热器高度按实测尺寸绘制。"""
    case, gpu, cooler, mb = (_one(build.parts, s) for s in ("case", "gpu", "cooler", "motherboard"))
    if not case or not case.specs.depth_mm or not case.specs.height_mm:
        return ""
    d, h = case.specs.depth_mm, case.specs.height_mm
    W = 760
    s = min((W - 40) / d, 300 / h)
    cw, ch = d * s, h * s
    out = [f'<svg viewBox="0 0 {W} {ch + 60:.0f}" width="100%" xmlns="http://www.w3.org/2000/svg" font-size="11">',
           f'<rect x="20" y="20" width="{cw:.1f}" height="{ch:.1f}" fill="#f7f9fb" stroke="#33658a" stroke-width="2"/>',
           _t(20, 14, f"机箱侧视（按比例）Case side view, to scale · {d:g} × {h:g} mm", 11, W - 40)]
    board_h = {"ATX": 305, "E-ATX": 330, "MATX": 244, "ITX": 170}.get((mb.specs.form_factor or "").upper() if mb else "", 305)
    board_w = {"ATX": 244, "E-ATX": 272, "MATX": 244, "ITX": 170}.get((mb.specs.form_factor or "").upper() if mb else "", 244)
    bx, by = 20 + cw - 30 - board_w * s, 30
    out.append(f'<rect x="{bx:.1f}" y="{by}" width="{board_w * s:.1f}" height="{board_h * s:.1f}" fill="#dfe8f1" stroke="#7a93ad"/>'
               f'<text x="{bx + 4:.1f}" y="{by + 14}" fill="#33658a">主板 Board</text>')
    if gpu and gpu.specs.length_mm:
        gl = gpu.specs.length_mm * s
        gx = 20 + cw - 30 - gl
        gy = by + 120 * s
        out.append(f'<rect x="{gx:.1f}" y="{gy:.1f}" width="{gl:.1f}" height="{max(14, 40 * s):.1f}" fill="#2e86ab" opacity="0.85"/>'
                   + _t(gx + 4, gy + 12, f"显卡 GPU {gpu.specs.length_mm:g} mm", 11, gl - 8, fill="#fff"))
        if case.specs.max_gpu_length_mm:
            lx = 20 + cw - 30 - case.specs.max_gpu_length_mm * s
            out.append(f'<line x1="{lx:.1f}" y1="{gy - 6:.1f}" x2="{lx:.1f}" y2="{gy + 40 * s + 8:.1f}" stroke="#c0392b" stroke-dasharray="4 3"/>'
                       + _t(lx + 3, gy + 40 * s + 20, f"限长 Limit {case.specs.max_gpu_length_mm:g}", 11, fill="#c0392b"))
    if cooler and cooler.specs.cooler_type != "aio" and cooler.specs.height_mm and case.specs.width_mm:
        ch2 = cooler.specs.height_mm
        out.append(_t(20, ch + 40, f'散热器高 Cooler height {ch2:g} mm · 机箱限高 Case limit '
                      f'{case.specs.max_cooler_height_mm or "?"} mm · 机箱宽 Case width {case.specs.width_mm:g} mm', 11, W - 40))
    out.append("</svg>")
    return "".join(out)


def svg_board_map(build: Build, ram_slots: list[str], m2_boot: str | None) -> str:
    """主板示意图：按版型画标准布局，标出建议使用的内存插槽与系统盘 M.2 插槽（非实物比例）。"""
    mb = _one(build.parts, "motherboard")
    if not mb:
        return ""
    ff = (mb.specs.form_factor or "ATX").upper()
    W, H = {"ITX": (330, 330), "MATX": (400, 400)}.get(ff, (400, 500))
    X0, Y0 = 12, 12
    def bx(fx): return X0 + W * fx
    def by(fy): return Y0 + H * fy

    n = len(mb.specs.dimm_slot_names or []) or mb.specs.ram_slots or (2 if ff == "ITX" else 4)
    dimms = list(mb.specs.dimm_slot_names or [])[:n] or (
        ["A1", "B1"] if n == 2 else ["A1", "A2", "B1", "B2"][:n] if n <= 4 else [f"DIMM{i + 1}" for i in range(n)])
    dimm_on, dimm_ok = _match_slots(ram_slots, dimms)
    m2s = list(mb.specs.m2_slot_names or [f"M2_{i + 1}" for i in range(mb.specs.m2_slots or 1)])[:4]
    m2_on, m2_ok = _match_slots([m2_boot] if m2_boot else [], m2s)
    eps = next((p.specs.eps8_required for p in build.parts if p.slot in ("cpu", "motherboard") and p.specs.eps8_required), None)
    gpu = _one(build.parts, "gpu")
    gpu_conn = ", ".join(f"{k} ×{v}" for k, v in (gpu.specs.power_connectors or {}).items() if v) if gpu else ""

    HI, PCB, SLOT, DARK = "#f6ae2d", "#3f6f5a", "#8a9a92", "#1d2a24"
    o = [f'<svg viewBox="0 0 {W + 410} {max(H, 470) + 24}" width="100%" xmlns="http://www.w3.org/2000/svg" '
         f'font-family="Noto Sans CJK SC, Microsoft YaHei, sans-serif" font-size="11">',
         f'<rect x="{X0}" y="{Y0}" width="{W}" height="{H}" rx="8" fill="{PCB}" stroke="{DARK}" stroke-width="2"/>']
    for fx, fy in ((0.04, 0.04), (0.96, 0.04), (0.04, 0.96), (0.96, 0.96), (0.55, 0.04), (0.55, 0.96)):
        o.append(f'<circle cx="{bx(fx):.0f}" cy="{by(fy):.0f}" r="5" fill="#d8dcd9" stroke="{DARK}"/>')
    # 后置 I/O
    o.append(f'<rect x="{bx(0.0):.0f}" y="{by(0.07):.0f}" width="{W * 0.12:.0f}" height="{H * 0.36:.0f}" fill="#b9c0c4" stroke="{DARK}"/>'
             f'<text x="{bx(0.06):.0f}" y="{by(0.25):.0f}" text-anchor="middle" font-size="9" transform="rotate(-90 {bx(0.06):.0f} {by(0.25):.0f})">I/O 后置接口</text>')
    # EPS
    o.append(f'<rect x="{bx(0.16):.0f}" y="{by(0.03):.0f}" width="{W * 0.12:.0f}" height="{H * 0.035:.0f}" fill="{DARK}"/>'
             f'<text x="{bx(0.16):.0f}" y="{by(0.10):.0f}" fill="#fff" font-size="9">EPS 8-pin</text>')
    # CPU 插槽
    sx, sy, ss = bx(0.22), by(0.14), W * 0.28
    o.append(f'<rect x="{sx:.0f}" y="{sy:.0f}" width="{ss:.0f}" height="{ss:.0f}" rx="3" fill="#cfd5d8" stroke="{DARK}" stroke-width="2"/>'
             f'<rect x="{sx + ss * 0.15:.0f}" y="{sy + ss * 0.15:.0f}" width="{ss * 0.7:.0f}" height="{ss * 0.7:.0f}" fill="#e9ecee" stroke="#777"/>'
             f'<path d="M{sx + ss * 0.17:.0f} {sy + ss * 0.83:.0f} l10 0 l-10 -10 z" fill="{HI}"/>'
             f'<text x="{sx + ss / 2:.0f}" y="{sy + ss / 2 + 4:.0f}" text-anchor="middle" font-weight="bold">CPU {e(mb.specs.socket or "")}</text>'
             f'<rect x="{sx + ss + 3:.0f}" y="{sy:.0f}" width="4" height="{ss:.0f}" fill="#777"/>')
    # CPU_FAN
    o.append(f'<rect x="{bx(0.53):.0f}" y="{by(0.17):.0f}" width="{W * 0.06:.0f}" height="{H * 0.025:.0f}" fill="#fff"/>'
             f'<text x="{bx(0.53):.0f}" y="{by(0.16):.0f}" fill="#fff" font-size="8">CPU_FAN</text>')
    # 内存插槽
    dx0 = bx(0.64)
    for i, nm in enumerate(dimms):
        x = dx0 + i * W * 0.045
        on = i in dimm_on
        o.append(f'<rect x="{x:.0f}" y="{by(0.08):.0f}" width="{W * 0.022:.0f}" height="{H * 0.4:.0f}" fill="{HI if on else SLOT}" stroke="{DARK}"/>'
                 f'<rect x="{x - 1:.0f}" y="{by(0.075):.0f}" width="{W * 0.022 + 2:.0f}" height="4" fill="#eee"/>'
                 f'<rect x="{x - 1:.0f}" y="{by(0.48) - 2:.0f}" width="{W * 0.022 + 2:.0f}" height="4" fill="#eee"/>'
                 f'<text x="{x + W * 0.011:.0f}" y="{by(0.52):.0f}" text-anchor="middle" fill="#fff" font-size="8" '
                 f'transform="rotate(60 {x + W * 0.011:.0f} {by(0.52):.0f})">{e(nm)}</text>')
    # 24-pin
    o.append(f'<rect x="{bx(0.93):.0f}" y="{by(0.16):.0f}" width="{W * 0.04:.0f}" height="{H * 0.22:.0f}" fill="{DARK}"/>'
             f'<text x="{bx(0.91):.0f}" y="{by(0.27):.0f}" fill="#fff" font-size="9" text-anchor="middle" transform="rotate(-90 {bx(0.91):.0f} {by(0.27):.0f})">ATX 24-pin</text>')
    # M.2 与 PCIe：第一条 M.2 在显卡插槽上方，其余在下方
    pcie_y = by(0.66)
    m2y = [by(0.58)] + [by(0.76 + i * 0.07) for i in range(len(m2s) - 1)]
    for i, (nm, y) in enumerate(zip(m2s, m2y)):
        on = i in m2_on
        o.append(f'<rect x="{bx(0.2):.0f}" y="{y:.0f}" width="{W * 0.3:.0f}" height="{H * 0.035:.0f}" fill="{HI if on else SLOT}" stroke="{DARK}"/>'
                 f'<circle cx="{bx(0.2) + W * 0.3 + 6:.0f}" cy="{y + H * 0.0175:.0f}" r="3" fill="#ddd"/>'
                 + _t(bx(0.2) + W * 0.3 + 14, y + H * 0.03, nm, 11, W * 0.42 if i == 0 else W * 0.13, fill="#fff", font_weight="bold" if on else "normal"))
    o.append(f'<rect x="{bx(0.14):.0f}" y="{pcie_y:.0f}" width="{W * 0.62:.0f}" height="{H * 0.03:.0f}" fill="{DARK}"/>'
             f'<rect x="{bx(0.76):.0f}" y="{pcie_y - 2:.0f}" width="8" height="{H * 0.03 + 4:.0f}" fill="#eee"/>'
             f'<text x="{bx(0.14):.0f}" y="{pcie_y - 4:.0f}" fill="#fff" font-size="9">PCIe x16 (GPU)</text>')
    # 芯片组、SATA、底部插针
    o.append(f'<rect x="{bx(0.66):.0f}" y="{by(0.74):.0f}" width="{W * 0.14:.0f}" height="{W * 0.14:.0f}" fill="#9aa5ab" stroke="{DARK}"/>'
             + _t(bx(0.73), by(0.74) + W * 0.08, mb.specs.chipset or "Chipset", 9, W * 0.13, anchor="middle") +
             f'<rect x="{bx(0.9):.0f}" y="{by(0.72):.0f}" width="{W * 0.06:.0f}" height="{H * 0.12:.0f}" fill="#2c4a73"/>'
             f'<text x="{bx(0.88):.0f}" y="{by(0.78):.0f}" fill="#fff" font-size="8" text-anchor="middle" transform="rotate(-90 {bx(0.88):.0f} {by(0.78):.0f})">SATA</text>')
    for fx, lab in ((0.08, "F_AUDIO"), (0.42, "F_USB"), (0.74, "F_PANEL")):
        o.append(f'<rect x="{bx(fx):.0f}" y="{by(0.91):.0f}" width="{W * 0.1:.0f}" height="{H * 0.025:.0f}" fill="#fff"/>'
                 f'<text x="{bx(fx):.0f}" y="{by(0.89):.0f}" fill="#fff" font-size="8">{lab}</text>')

    # 编号标注（按装机顺序）
    first = lambda idx, names: ", ".join(names[i] for i in sorted(idx)) if idx else None
    ram_txt = first(dimm_on, dimms)
    m2_txt = first(m2_on, m2s)
    callouts = [
        ((sx + ss * 0.5, sy - 2), f"装 CPU：对准金色三角，放下后扣好压杆", "Install CPU: align the gold triangle, then close the lever"),
        ((dx0 + W * 0.02, by(0.04)),
         f"内存插入 {ram_txt}" if ram_txt else "内存插槽：以主板说明书为准",
         f"RAM into {ram_txt}" if ram_txt else "RAM slots: follow the board manual"),
        ((bx(0.2) + W * 0.15, m2y[0] - 2),
         f"系统盘装入 {m2_txt}，先拆 M.2 散热片和贴膜" if m2_txt else "系统盘 M.2 插槽：以说明书为准",
         f"Boot SSD into {m2_txt}; remove heatsink and film first" if m2_txt else "Boot M.2 slot: follow the manual"),
        ((bx(0.56), by(0.24)), "散热器风扇线接 CPU_FAN", "Cooler fan cable to CPU_FAN"),
        ((bx(0.22), by(0.045)), f"CPU 供电 EPS 8-pin{' ×' + str(eps) if eps else ''}，插到底", f"CPU power EPS 8-pin{' ×' + str(eps) if eps else ''}, push fully in"),
        ((bx(0.95), by(0.14)), "主板 24-pin 供电", "Board 24-pin power"),
        ((bx(0.6), pcie_y + H * 0.015), f"显卡插入 PCIe x16，听到卡扣声" + (f"；接 {gpu_conn}" if gpu_conn else ""),
         "GPU into PCIe x16 until it clicks" + (f"; connect {gpu_conn}" if gpu_conn else "")),
        ((bx(0.79), by(0.92)), "前面板开关/指示灯线接 F_PANEL", "Front panel switch/LED wires to F_PANEL"),
    ]
    lx, ly = W + 40, 26
    for k, ((cx, cy), zh, en) in enumerate(callouts, 1):
        o.append(f'<circle cx="{cx:.0f}" cy="{cy:.0f}" r="9" fill="#c0392b" stroke="#fff" stroke-width="1.5"/>'
                 f'<text x="{cx:.0f}" y="{cy + 4:.0f}" text-anchor="middle" fill="#fff" font-size="10" font-weight="bold">{k}</text>'
                 f'<circle cx="{lx + 9}" cy="{ly + 4}" r="9" fill="#c0392b"/>'
                 f'<text x="{lx + 9}" y="{ly + 8}" text-anchor="middle" fill="#fff" font-size="10" font-weight="bold">{k}</text>'
                 + _t(lx + 26, ly + 4, zh, 11, 340) + _t(lx + 26, ly + 19, en, 10, 340, fill="#555"))
        ly += 44
    ly += 4
    o.append(f'<rect x="{lx}" y="{ly}" width="12" height="12" fill="{HI}"/><text x="{lx + 18}" y="{ly + 10}">建议使用 · Use this slot</text>'
             f'<rect x="{lx + 190}" y="{ly}" width="12" height="12" fill="{SLOT}"/><text x="{lx + 208}" y="{ly + 10}">空置 · Leave empty</text>')
    ly += 30
    if (ram_slots and not dimm_ok) or (m2_boot and not m2_ok):
        o.append(f'<text x="{lx}" y="{ly}" fill="#c0392b" font-weight="bold">插槽名称未能与主板规格对上，请以说明书为准</text>'
                 f'<text x="{lx}" y="{ly + 15}" fill="#c0392b" font-weight="bold" font-size="10">Slot names not matched to the board spec; check the manual</text>')
        ly += 34
    o.append(f'<text x="{lx}" y="{ly}" fill="#c0392b">示意图，非实物比例；接口位置为常见布局</text>'
             f'<text x="{lx}" y="{ly + 15}" fill="#c0392b" font-size="10">Schematic, not to scale; connector positions are typical</text></svg>')
    return "".join(o)


def _slot_key(name: str) -> str:
    k = "".join(ch for ch in name.upper() if ch.isalnum())
    for p in ("DDR5", "DDR4", "DIMM"):
        if k.startswith(p) and len(k) > len(p):
            k = k[len(p):]
    return k


def _match_slots(wanted: list[str], names: list[str]) -> tuple[set[int], bool]:
    """把建议插槽名与主板插槽名对应：先精确匹配（忽略大小写、下划线、DDR5_/DIMM 前缀），再接受唯一的前缀匹配（如 A 对 A1）。"""
    keys = [_slot_key(n) for n in names]
    hit, ok = set(), True
    for w in wanted:
        wk = _slot_key(w)
        exact = [i for i, k in enumerate(keys) if k == wk]
        pref = [i for i, k in enumerate(keys) if k.startswith(wk) or wk.startswith(k)]
        if exact:
            hit.add(exact[0])
        elif len(pref) == 1:
            hit.add(pref[0])
        else:
            ok = False
    return hit, ok


def svg_variants(checked: list[dict]) -> str:
    if len(checked) < 2:
        return ""
    W, H = 760, 40 + 40 * len(checked)
    lab = [f'{c["currency"]} {c["total"]:,.0f} · {c["power"]["estimated_w"]} W' for c in checked]
    lw = max(_tw(t, 11) for t in lab) + 12
    sx = (W - 240 - lw) / max(c["total"] for c in checked)
    out = [f'<svg viewBox="0 0 {W} {H}" width="100%" xmlns="http://www.w3.org/2000/svg" font-size="11">']
    for i, c in enumerate(checked):
        y = 12 + 40 * i
        out.append(_t(0, y + 12, c["name"]["zh"], 11, 228) + _t(0, y + 26, c["name"]["en"], 10, 228, fill="#666")
                   + f'<rect x="240" y="{y}" width="{c["total"] * sx:.1f}" height="22" fill="{PALETTE[i % len(PALETTE)]}"/>'
                   + _t(246 + c["total"] * sx, y + 15, lab[i], 11))
    out.append("</svg>")
    return "".join(out)


# ---------- HTML / PDF ----------

CSS = """
@page { size: A4; margin: 16mm 14mm 16mm 14mm; }
body { font-family: "Noto Sans CJK SC", "Noto Sans SC", "Microsoft YaHei", "PingFang SC", sans-serif; color: #1d2733; font-size: 10.5pt; line-height: 1.5; }
h1 { font-size: 22pt; margin: 0 0 4pt; color: #1f4e79; }
h2 { font-size: 14pt; color: #1f4e79; border-bottom: 2px solid #1f4e79; padding-bottom: 3pt; margin: 18pt 0 8pt; page-break-after: avoid; }
h3 { font-size: 11.5pt; margin: 12pt 0 4pt; color: #33658a; page-break-after: avoid; }
.sec { page-break-before: always; }
.p2 { color: #5b6b7b; font-size: 9.5pt; margin-top: 1pt; }
.pair { margin: 4pt 0 8pt; }
.pair p { margin: 0; }
table { width: 100%; border-collapse: collapse; font-size: 9pt; margin: 6pt 0; }
th { background: #1f4e79; color: #fff; text-align: left; padding: 4pt; }
td { border-bottom: 1px solid #dde3ea; padding: 3.5pt 4pt; vertical-align: top; }
tr { page-break-inside: avoid; }
thead { display: table-header-group; }
h1, h2, h3, h4 { break-after: avoid; }
.num { text-align: right; white-space: nowrap; }
.tot td { font-weight: bold; border-top: 2px solid #1f4e79; }
.badge { display: inline-block; padding: 1pt 6pt; border-radius: 8pt; font-size: 8.5pt; color: #fff; white-space: nowrap; }
.pass { background: #27ae60; } .warn { background: #f39c12; } .fail { background: #c0392b; } .unknown { background: #7f8c8d; }
.kpi { display: inline-block; width: 31%; margin-right: 2%; vertical-align: top; border: 1px solid #dde3ea; border-radius: 6pt; padding: 8pt; box-sizing: border-box; }
.kpi b { display: block; font-size: 16pt; color: #1f4e79; }
.fig { margin: 6pt 0 12pt; page-break-inside: avoid; }
ol li, ul li { margin-bottom: 4pt; page-break-inside: avoid; }
a { color: #1f4e79; word-break: break-all; }
.small { font-size: 8.5pt; color: #5b6b7b; }
blockquote { border-left: 3px solid #9aa9b8; margin: 6pt 0; padding: 2pt 10pt; color: #44515e; }
code { background: #eef2f6; padding: 0 3pt; border-radius: 3pt; font-size: 9.5pt; }
.kpis { margin: 6pt 0 10pt; }
.disc { border-left: 3px solid #f39c12; background: #fff8ec; padding: 6pt 8pt; font-size: 9pt; }
"""


def _h(zh: str, en: str, order: str) -> str:
    return f"{zh} · {en}" if order == "zh-en" else f"{en} · {zh}"


def _parts_table(build: Build, order: str) -> str:
    rows = []
    for x in build.parts:
        spec = []
        s = x.specs
        for k in ("socket", "chipset", "form_factor", "memory_type", "speed_mts", "capacity_gb_per_module", "modules",
                  "length_mm", "board_power_w", "tdp_w", "wattage_w", "interface", "height_mm", "radiator_mm"):
            v = getattr(s, k)
            if v is not None:
                spec.append(f"{k.replace('_', ' ')}: {v:g}" if isinstance(v, float) else f"{k.replace('_', ' ')}: {v}")
        slot = _h(SLOT_ZH[x.slot], SLOT_EN[x.slot], order)
        rows.append(f"<tr><td>{e(slot)}</td><td><b>{e(x.model)}</b>{'' if x.qty == 1 else f' × {x.qty}'}"
                    f'<div class="small">{e(" · ".join(spec))}</div></td>'
                    f'<td class="num">{e(x.currency.upper())} {x.price * x.qty:,.2f}</td>'
                    f'<td>{e(x.shop)}<div class="small"><a href="{e(x.url)}">{e(x.url)}</a></div></td>'
                    f'<td class="num">{x.checked_date.isoformat()}</td></tr>')
    total = sum(x.price * x.qty for x in build.parts)
    return ("<table><thead><tr>"
            f"<th>{_h('类别', 'Slot', order)}</th><th>{_h('型号与规格', 'Model & specs', order)}</th>"
            f"<th>{_h('价格', 'Price', order)}</th><th>{_h('商店与链接', 'Shop & link', order)}</th><th>{_h('核价日期', 'Checked', order)}</th></tr></thead><tbody>"
            + "".join(rows)
            + f'<tr class="tot"><td colspan="2">{_h("合计", "Total", order)}</td><td class="num">{e(build.currency.upper())} {total:,.2f}</td>'
              f'<td colspan="2">{_h("预算", "Budget", order)} {build.budget:,.2f}</td></tr></tbody></table>')


def _results_table(chk: dict, order: str) -> str:
    a = 0 if order == "zh-en" else 1
    rows = "".join(
        f'<tr><td><span class="badge {r["status"]}">{e(L[r["status"]][a])} {e(L[r["status"]][1 - a])}</span></td>'
        f'<td>{e(r["zh"] if a == 0 else r["en"])}<div class="p2">{e(r["en"] if a == 0 else r["zh"])}</div></td></tr>'
        for r in sorted(chk["results"], key=lambda r: ["fail", "unknown", "warn", "pass"].index(r["status"])))
    return f"<table><thead><tr><th style='width:22%'>{_h('结果', 'Result', order)}</th><th>{_h('说明', 'Detail', order)}</th></tr></thead><tbody>{rows}</tbody></table>"


BLOCK_HELP = {
    "kpis": "结论、总价/预算、估算功耗三个指标",
    "budget_chart": "主方案预算分配图",
    "parts:main": "主方案配件清单（parts:budget、parts:performance 同理）",
    "compat": "主方案兼容性检查结果（compat:budget、compat:performance 同理）",
    "power_chart": "功耗与电源余量图",
    "clearance_chart": "显卡长度、散热器高度余量图",
    "case_fit": "机箱侧视示意图（按比例）",
    "variants_chart": "三套方案总价与功耗对比图",
    "board_map": "主板示意图（插槽、供电与前面板接口，带编号装机标注）",
}
MAX_MD_CHARS = 200_000
_PLACEHOLDER = re.compile(r"^[ \t]*\{\{\s*([a-z_]+(?::[a-z]+)?)\s*\}\}[ \t]*$", re.M)


def _blocks(data: Input, checked: list[dict]) -> tuple[dict[str, str], list[str]]:
    """生成可放进 Markdown 的 HTML 块；返回 (块, 必须出现的块名)。"""
    o = data.language_order
    main = next(b for b in data.builds if b.key == "main")
    mchk = next(c for c in checked if c["key"] == "main")
    psu = _one(main.parts, "psu")
    case, gpu, cooler = (_one(main.parts, s) for s in ("case", "gpu", "cooler"))
    clear = []
    if gpu and case and gpu.specs.length_mm and case.specs.max_gpu_length_mm:
        clear.append(("显卡长度 GPU length", gpu.specs.length_mm, case.specs.max_gpu_length_mm))
    if cooler and cooler.specs.cooler_type != "aio" and cooler.specs.height_mm and case and case.specs.max_cooler_height_mm:
        clear.append(("散热器高度 Cooler height", cooler.specs.height_mm, case.specs.max_cooler_height_mm))
    verdict = {"pass": ("全部通过", "All checks passed"), "warn": ("通过（有提示）", "Passed with warnings")}[mchk["verdict"]]
    vz, ve = verdict if o == "zh-en" else verdict[::-1]
    fig = lambda svg: f"<div class='fig'>{svg}</div>" if svg else ""
    b = {
        "kpis": (f"<div class='kpis'><div class='kpi'>{_h('结论', 'Verdict', o)}<b>{e(vz)}</b><span class='small'>{e(ve)}</span></div>"
                 f"<div class='kpi'>{_h('总价 / 预算', 'Total / Budget', o)}<b>{e(main.currency.upper())} {mchk['total']:,.0f}</b>"
                 f"<span class='small'>/ {main.budget:,.0f}</span></div>"
                 f"<div class='kpi'>{_h('估算功耗', 'Est. draw', o)}<b>{mchk['power']['estimated_w']} W</b>"
                 f"<span class='small'>{_h('电源', 'PSU', o)} {f'{psu.specs.wattage_w:g}' if psu and psu.specs.wattage_w else '?'} W</span></div></div>"),
        "budget_chart": fig(svg_budget(main, mchk["total"])),
        "power_chart": fig(svg_power(mchk["power"], psu.specs.wattage_w if psu else None)),
        "clearance_chart": fig(svg_clearance(clear)),
        "case_fit": fig(svg_case_fit(main)),
        "variants_chart": fig(svg_variants(checked)),
        "board_map": fig(svg_board_map(main, data.ram_slots_to_use, data.m2_boot_slot)),
    }
    for bd, chk in zip(data.builds, checked):
        b[f"parts:{bd.key}"] = _parts_table(bd, o)
        b[f"compat:{bd.key}"] = _results_table(chk, o)
    b["compat"] = b["compat:main"]
    required = ["kpis", "parts:main", "compat", "budget_chart", "power_chart", "board_map"]
    required += [k for k in ("clearance_chart", "case_fit", "variants_chart") if b[k]]
    required += [f"parts:{bd.key}" for bd in data.builds if bd.key != "main"]
    return b, required


def render_html(data: Input, checked: list[dict], today: date, md_text: str) -> str:
    """把团队写的 Markdown 转成 HTML，并在 {{块名}} 占位处插入由已校验数据生成的表格和图；
    没放进正文的必备块统一附在文末，保证 PDF 里不缺校验结果和图。Markdown 中的原始 HTML 不会被执行。"""
    from markdown_it import MarkdownIt

    o = data.language_order
    blocks, required = _blocks(data, checked)
    used, tokens = [], {}

    def sub(m):
        name = m.group(1)
        if name not in blocks:
            raise ValueError(f"未知占位符 {{{{{name}}}}}。可用：" + "、".join(sorted(blocks)))
        used.append(name)
        tok = f"PCBLOCK{len(tokens):03d}X"
        tokens[tok] = blocks[name]
        return f"\n{tok}\n"

    body = _PLACEHOLDER.sub(sub, md_text)
    left = re.findall(r"\{\{[^}\n]*\}\}", body)
    if left:
        raise ValueError("占位符必须单独占一行，例如 {{board_map}}；有问题的：" + "、".join(left[:5]))
    missing = [k for k in required if k not in used]
    if missing:
        body += f"\n\n## {_h('附录：校验结果与图表', 'Appendix: checks and diagrams', o)}\n\n"
        for k in missing:
            tok = f"PCBLOCK{len(tokens):03d}X"
            tokens[tok] = blocks[k]
            body += f"{tok}\n\n"
    md = MarkdownIt("commonmark", {"html": False, "linkify": False, "typographer": False}).enable("table")
    html_body = md.render(body)
    for tok, frag in tokens.items():
        html_body = html_body.replace(f"<p>{tok}</p>", frag).replace(tok, frag)
    oldest = min(x.checked_date for bd in data.builds for x in bd.parts)
    foot = (f"<p class='disc'>{e('价格为核价日期的快照，仅供参考，不代表库存或最低价。功耗为按额定功耗的估算值；兼容性检查基于所列规格，不能替代厂商兼容列表。')}"
            f"<br>{e('Prices are snapshots from the checked date, not a guarantee of stock or lowest price. Power is estimated from rated figures; checks rely on the listed specs and do not replace vendor compatibility lists.')}</p>"
            f"<p class='disc'>{e('装机前关闭电源并拔掉电源线，触摸接地金属释放静电；不要拆开电源内部，不要自行改装线材。')}"
            f"<br>{e('Switch off and unplug before you start, and touch grounded metal to discharge static. Never open the PSU or modify its cables.')}</p>"
            f"<p class='small'>{_h('生成日期', 'Generated', o)} {today.isoformat()} · {_h('价格核对于', 'Prices checked from', o)} {oldest.isoformat()}</p>")
    csp = "default-src 'none'; style-src 'unsafe-inline'; img-src data:"
    return (f"<!DOCTYPE html><html><head><meta charset='utf-8'><meta http-equiv='Content-Security-Policy' content=\"{csp}\">"
            f"<style>{CSS}</style></head><body>{html_body}{foot}</body></html>")


def _browser() -> str | None:
    env = os.environ.get("PC_BUILD_CHROME")
    if env and Path(env).exists():
        return env
    for name in ("chromium", "chromium-browser", "google-chrome", "google-chrome-stable", "microsoft-edge", "msedge"):
        p = shutil.which(name)
        if p:
            return p
    for p in sorted(Path.home().glob(".cache/ms-playwright/chromium*/chrome-linux*/chrome")):
        return str(p)
    return None


def html_to_pdf(page: str, output: Path) -> str:
    with tempfile.TemporaryDirectory(prefix="pc_build_") as tmp:
        src, out = Path(tmp) / "report.html", Path(tmp) / "report.pdf"
        src.write_text(page, encoding="utf-8")
        browser, engine = _browser(), None
        if browser:
            cmd = [browser, "--headless=new", "--disable-gpu", "--no-pdf-header-footer", f"--user-data-dir={tmp}/profile",
                   f"--print-to-pdf={out}", src.as_uri()]
            subprocess.run(cmd, capture_output=True, timeout=180)
            engine = "chrome"
        if not out.exists() or out.stat().st_size == 0:
            soffice = shutil.which("soffice") or shutil.which("libreoffice")
            if not soffice:
                raise OSError("没有找到可用的 PDF 渲染器：请安装 Chrome/Chromium 或 LibreOffice。")
            subprocess.run([soffice, "--headless", "--convert-to", "pdf:writer_web_pdf_Export", "--outdir", tmp, str(src)],
                           capture_output=True, timeout=180)
            engine = "libreoffice"
        if not out.exists() or out.stat().st_size == 0:
            raise OSError("PDF 渲染失败，请检查 Chrome/LibreOffice 是否能正常运行。")
        output.parent.mkdir(parents=True, exist_ok=True)
        with output.open("xb") as fh:
            fh.write(out.read_bytes())
    return engine


def run(data: Input) -> dict:
    today = data.today or date.today()
    keys = [b.key for b in data.builds]
    if len(set(keys)) != len(keys):
        raise ValueError("每套配置的 key 必须唯一（main / budget / performance）。")
    if "main" not in keys:
        raise ValueError("必须包含 key 为 main 的主方案。")
    notes = []
    if data.user_budget is not None:
        changed = [b.key for b in data.builds if b.budget != data.user_budget]
        if changed:
            notes.append(f"方案 {', '.join(changed)} 自填的 budget 已改为用户预算 {data.user_budget:,.2f}。"
                         f" / Builds {', '.join(changed)}: budget replaced by the user's budget {data.user_budget:,.2f}.")
        data = data.model_copy(update={"builds": [b.model_copy(update={"budget": data.user_budget}) for b in data.builds]})
    checked = [check_build(b, today) for b in data.builds]
    result = {"today": today.isoformat(), "builds": checked, "notes": notes,
              "can_export": all(c["fail_count"] == 0 for c in checked),
              "basis": "规则检查基于提交的规格与价格；未联网核实，不能替代厂商兼容列表。"}
    if data.action == "validate":
        return result
    if not result["can_export"]:
        raise ValueError("存在硬性失败（fail），不能导出。请先修正配置：" + "；".join(
            f"[{c['key']}] {r['zh']}" for c in checked for r in c["results"] if r["status"] == "fail"))
    if data.user_budget is None:
        raise ValueError("export 需要 user_budget：用户给出的预算金额，不能用方案总价代替。")
    if not data.markdown_path:
        raise ValueError("export 需要 markdown_path：团队写好的中英双语 Markdown 报告（绝对 .md 路径）。")
    md_file = Path(data.markdown_path).expanduser()
    if not md_file.is_absolute() or md_file.suffix.lower() != ".md" or not md_file.is_file():
        raise ValueError("markdown_path 必须是已存在的绝对 .md 文件路径。")
    md_text = md_file.read_text(encoding="utf-8")
    if len(md_text) > MAX_MD_CHARS:
        raise ValueError(f"Markdown 太长（{len(md_text)} 字符，上限 {MAX_MD_CHARS}）。")
    if not re.search(r"[\u4e00-\u9fff]", md_text) or not re.search(r"[A-Za-z]{3,}", md_text):
        raise ValueError("Markdown 必须是中英双语：同时包含中文和英文内容。")
    if not re.search(r"https?://", md_text):
        raise ValueError("Markdown 必须包含资料来源链接（价格与规格页）。")
    if not data.output_path:
        raise ValueError("export 必须提供 output_path。")
    output = Path(data.output_path).expanduser()
    if not output.is_absolute() or output.suffix.lower() != ".pdf":
        raise ValueError("output_path 必须是绝对 .pdf 文件路径。")
    if output.exists():
        raise ValueError("目标文件已存在，请换一个文件名；不会覆盖已有文件。")
    engine = html_to_pdf(render_html(data, checked, today, md_text), output)
    return {**result, "markdown_path": str(md_file), "output_path": str(output), "bytes": output.stat().st_size, "renderer": engine}


class BuildCheckerTool(Tool):
    def __init__(self):
        super().__init__(ToolCard(
            id="build_checker",
            name="build_checker",
            description=("装机配置校验与双语 PDF 导出。validate：对主方案和备选方案逐条检查插槽、内存、版型、显卡长度、散热器高度、"
                         "冷排、M.2、电源功率与接口、价格时效和预算，返回通过/注意/失败/未知。export：所有方案无失败、价格未过期、"
                         "把团队写的中英双语 Markdown（markdown_path）转成 PDF：在单独一行写 {{kpis}}、{{budget_chart}}、{{parts:main}}、"
                         "{{compat}}、{{power_chart}}、{{clearance_chart}}、{{case_fit}}、{{variants_chart}}、{{parts:budget}}、"
                         "{{parts:performance}}、{{board_map}} 等占位符即插入校验过的表格和图，没放的必备项会附在文末。"
                         "export 必须带 user_budget（用户预算，会替换各方案自填的 budget）。需绝对 .pdf output_path，不覆盖已有文件。"),
            input_params=Input.model_json_schema(),
        ))

    async def invoke(self, inputs, **kwargs):
        try:
            return {"success": True, **await asyncio.to_thread(run, Input.model_validate(inputs))}
        except (ValueError, OSError, subprocess.SubprocessError) as exc:
            return {"success": False, "error": str(exc)}

    async def stream(self, inputs, **kwargs):
        yield await self.invoke(inputs, **kwargs)
