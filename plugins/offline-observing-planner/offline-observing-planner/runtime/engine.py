"""离线观星规划台：严格限定输入的观测坐标与事件计算。

This adapter is independently authored for the plugin. The sibling astronomy.py
is the unmodified, MIT-licensed Astronomy Engine 2.1.19; see bundled notices.
Run this module in the plugin's deadline-controlled subprocess, never a model.
"""
from __future__ import annotations

import datetime as dt
import importlib.util
import json
import math
from pathlib import Path
import re
import sys

VERSION = "1.0.0"
ENGINE_VERSION = "2.1.19"
BODY_NAMES = {
    "Sun": "太阳", "Moon": "月球", "Mercury": "水星", "Venus": "金星",
    "Mars": "火星", "Jupiter": "木星", "Saturn": "土星",
}
UTC = dt.timezone.utc
MIN_TIME = dt.datetime(2000, 1, 1, tzinfo=UTC)
MAX_TIME = dt.datetime(2100, 12, 31, 23, 59, 59, tzinfo=UTC)
_ASTRO = None


class PlanError(ValueError):
    def __init__(self, code: str, message: str):
        super().__init__(message)
        self.code = code


def _astronomy():
    global _ASTRO
    if _ASTRO is None:
        spec = importlib.util.spec_from_file_location(
            "_observing_planner_astronomy", Path(__file__).with_name("astronomy.py")
        )
        if spec is None or spec.loader is None:
            raise PlanError("engine_unavailable", "随包数值引擎不可用，请重新安装完整插件。")
        module = importlib.util.module_from_spec(spec)
        spec.loader.exec_module(module)
        _ASTRO = module
    return _ASTRO


def _number(value, name, low, high, *, integer=False):
    if type(value) not in (int, float):
        raise PlanError("invalid_input", f"{name}必须是有限数值，不能是文本或布尔值。")
    if not low <= value <= high or not math.isfinite(value) or (integer and int(value) != value):
        qualifier = "整数" if integer else "数值"
        raise PlanError("out_of_range", f"{name}必须是 {low} 到 {high} 之间的{qualifier}。")
    return int(value) if integer else float(value)


def validate_request(request):
    """Normalize without invoking the numerical engine; no silent coercion."""
    if not isinstance(request, dict):
        raise PlanError("invalid_input", "规划参数必须是 JSON 对象。")
    allowed = {"latitude", "longitude", "elevation_m", "start_utc", "duration_hours",
               "step_minutes", "bodies", "display_offset_minutes"}
    if set(request) - allowed:
        raise PlanError("unknown_field", "含不支持的参数；仅接受位置、UTC 时间、时长、采样步长、天体和显示时差。")
    for required in ("latitude", "longitude", "start_utc"):
        if required not in request:
            raise PlanError("missing_field", f"缺少必填参数：{required}。")
    text = request["start_utc"]
    if not isinstance(text, str) or not re.fullmatch(r"\d{4}-\d{2}-\d{2}T\d{2}:\d{2}:\d{2}Z", text):
        raise PlanError("invalid_time", "起始时间必须明确使用 UTC，格式为 YYYY-MM-DDTHH:MM:SSZ。")
    try:
        start = dt.datetime.strptime(text, "%Y-%m-%dT%H:%M:%SZ").replace(tzinfo=UTC)
    except ValueError:
        raise PlanError("invalid_time", "起始时间包含无效的日期或时刻；不接受闰秒。") from None
    if start < MIN_TIME or start > MAX_TIME:
        raise PlanError("out_of_range", "整个规划区间必须位于 2000-01-01 至 2100-12-31 UTC 之间。")
    duration = _number(request.get("duration_hours", 24), "规划时长（小时）", 1 / 3600, 24)
    seconds = duration * 3600
    if not math.isclose(seconds, round(seconds), rel_tol=0, abs_tol=1e-6):
        raise PlanError("invalid_duration", "规划时长须对应整数秒，且至少为 1 秒。")
    end = start + dt.timedelta(seconds=round(seconds))
    if start < MIN_TIME or end > MAX_TIME:
        raise PlanError("out_of_range", "整个规划区间必须位于 2000-01-01 至 2100-12-31 UTC 之间。")
    bodies = request.get("bodies", list(BODY_NAMES))
    if (not isinstance(bodies, list) or not 1 <= len(bodies) <= 7
            or any(not isinstance(b, str) or b not in BODY_NAMES for b in bodies)
            or len(set(bodies)) != len(bodies)):
        raise PlanError("invalid_bodies", "天体必须是不重复的列表，选自 Sun、Moon、Mercury、Venus、Mars、Jupiter、Saturn。")
    normalized = {
        "latitude": _number(request["latitude"], "纬度", -80, 80),
        "longitude": _number(request["longitude"], "经度（东正西负）", -180, 180),
        "elevation_m": _number(request.get("elevation_m", 0), "海拔（米）", -500, 10000),
        "start_utc": text,
        "duration_hours": round(seconds) / 3600,
        "step_minutes": _number(request.get("step_minutes", 30), "采样步长（分钟）", 5, 60, integer=True),
        "bodies": list(bodies),
        "display_offset_minutes": _number(request.get("display_offset_minutes", 0), "固定显示时差（分钟）", -840, 840, integer=True),
    }
    return normalized, start, end


def _stamp(value, offset):
    if value.tzinfo is None:
        value = value.replace(tzinfo=UTC)
    value = value.astimezone(UTC)
    # Milliseconds retain useful event precision without implying exact prediction.
    timespec = "milliseconds" if value.microsecond else "seconds"
    return {
        "utc": value.isoformat(timespec=timespec).replace("+00:00", "Z"),
        "display": value.astimezone(dt.timezone(dt.timedelta(minutes=offset))).isoformat(timespec=timespec),
    }


def _finite(value):
    if not math.isfinite(value):
        raise PlanError("numerical_error", "引擎返回非有限数值，本次结果无效。")
    return value


def _position(astro, body, time, observer, stamp):
    eq = astro.Equator(body, time, observer, ofdate=True, aberration=True)
    horizontal = astro.Horizon(time, observer, eq.ra, eq.dec, astro.Refraction.Airless)
    return {**stamp, "altitude_deg": _finite(horizontal.altitude),
            "azimuth_deg": _finite(horizontal.azimuth),
            "ra_hours": _finite(eq.ra), "dec_deg": _finite(eq.dec)}


def _events(astro, search, start, end, offset):
    """Collect events only in [start,end), with bounded searches and forward progress."""
    found = []
    cursor = start
    for _ in range(4):
        if cursor >= end:
            return found
        result = search(astro.Time.Parse(cursor.strftime("%Y-%m-%dT%H:%M:%SZ")),
                        (end - cursor).total_seconds() / 86400)
        if result is None:
            return found
        when = result.Utc().replace(tzinfo=UTC)
        if when < cursor - dt.timedelta(milliseconds=100):
            raise PlanError("event_search_error", "事件搜索未向前推进，本次规划已停止。")
        if when >= end:
            return found
        if when >= start:
            found.append(_stamp(when, offset))
        # Round up to the next whole second, beyond this root, for Parse's format.
        cursor = (when + dt.timedelta(seconds=1)).replace(microsecond=0)
    raise PlanError("event_search_error", "事件数量超出本插件的有界搜索范围，本次规划已停止。")


def compute_plan(request):
    """Return actual engine results; callers must impose a killable wall deadline."""
    try:
        req, start, end = validate_request(request)
        astro = _astronomy()
        observer = astro.Observer(req["latitude"], req["longitude"], req["elevation_m"])
        step = dt.timedelta(minutes=req["step_minutes"])
        moments = [start]
        while moments[-1] + step < end:
            moments.append(moments[-1] + step)
        moments.append(end)
        stamps = [_stamp(t, req["display_offset_minutes"]) for t in moments]
        times = [astro.Time.Parse(t.strftime("%Y-%m-%dT%H:%M:%SZ")) for t in moments]
        tracks = {}
        for name in dict.fromkeys([*req["bodies"], "Sun"]):
            body = getattr(astro.Body, name)
            tracks[name] = [_position(astro, body, t, observer, stamp) for t, stamp in zip(times, stamps)]
        result_bodies = []
        for name in req["bodies"]:
            body = getattr(astro.Body, name)
            event_values = {}
            for key, direction in (("rise", astro.Direction.Rise), ("set", astro.Direction.Set)):
                event_values[key] = _events(astro, lambda t, days, b=body, d=direction:
                    astro.SearchRiseSet(b, observer, d, t, days, metersAboveGround=0),
                    start, end, req["display_offset_minutes"])
            any_event = bool(event_values["rise"] or event_values["set"])
            result_bodies.append({"id": name, "name": BODY_NAMES[name], "track": tracks[name],
                "rise_set": {**event_values, "status": "events" if any_event else "no_event_in_interval",
                    "message": "已列出区间内的升落事件。" if any_event else "本区间没有升落事件；不能据此断言永不升起、永不落下或可见。"}})
        twilight = []
        for kind, name, altitude in (("civil", "民用曙暮光", -6), ("nautical", "航海曙暮光", -12),
                                     ("astronomical", "天文曙暮光", -18)):
            events = {}
            for key, direction in (("dawn", astro.Direction.Rise), ("dusk", astro.Direction.Set)):
                events[key] = _events(astro, lambda t, days, d=direction, a=altitude:
                    astro.SearchAltitude(astro.Body.Sun, observer, d, t, days, a),
                    start, end, req["display_offset_minutes"])
            any_event = bool(events["dawn"] or events["dusk"])
            twilight.append({"kind": kind, "name": name, "altitude_deg": altitude, **events,
                "status": "events" if any_event else "no_event_in_interval",
                "message": "已列出区间内的太阳中心高度穿越事件。" if any_event else "本区间未出现该高度的曙暮光边界。"})
        return {"ok": True, "version": VERSION, "engine_version": ENGINE_VERSION,
            "request": req, "times": stamps, "bodies": result_bodies, "sun_track": tracks["Sun"], "twilight": twilight,
            "conventions": {
                "coordinates": "曲线为地心历表经观测者视差、光行时和光行差修正后的站心、当日赤道坐标转地平坐标；高度为不含大气折射的天体中心高度。方位角自北向东增加。",
                "rise_set": "升落使用引擎的标准大气折射与地平线模型；太阳、月球按上边缘，行星按中心。与无折射曲线的 0° 交点并非同一约定；实际大气与地形会改变时刻。",
                "twilight": "曙暮光为太阳中心无折射高度穿越 -6°、-12°、-18° 的时刻；曲线阴影只依据采样值。",
                "time": "输入与计算采用 UTC。显示时差是用户指定的固定偏移，不推断时区或夏令时。轨迹含结束采样点；事件区间为起点包含、终点不包含。",
            },
            "warnings": [
                "仅用于有限范围内的观测规划，不保证可见性，也不用于导航、望远镜控制或太阳观测安全判断。",
                "未考虑天气、光污染、山体遮挡和实际折射；不提供恒星、卫星或食象预测。",
                "远期时间尺度与闰秒预测存在不确定性：2100-12-30 的月球核对样例与 JPL 相差约 1.4 角分，主要来自时间尺度假设差异；不保证所有日期均达到 1 角分精度。",
                "图中采样点之间的连线不是额外数值求解；接近天顶时方位角可能迅速变化。",
            ]}
    except PlanError as exc:
        return {"ok": False, "version": VERSION, "error": {"code": exc.code, "message": str(exc)}}
    except Exception:
        return {"ok": False, "version": VERSION, "error": {
            "code": "numerical_error", "message": "数值计算未完成；请检查输入或缩短区间。未返回替代或缓存结果。"}}


def main():
    try:
        data = sys.stdin.buffer.read(32769)
        if len(data) > 32768:
            raise PlanError("input_too_large", "规划参数超过 32 KiB 上限。")
        request = json.loads(data.decode("utf-8"))
        if isinstance(request, dict) and request.get("action") == "validate" and set(request) == {"action", "request"}:
            normalized, _, _ = validate_request(request["request"])
            output = {"ok": True, "version": VERSION, "request": normalized}
        else:
            output = compute_plan(request)
    except PlanError as exc:
        output = {"ok": False, "version": VERSION, "error": {"code": exc.code, "message": str(exc)}}
    except (ValueError, UnicodeError):
        output = {"ok": False, "version": VERSION, "error": {"code": "invalid_json", "message": "输入不是有效的 UTF-8 JSON 规划参数。"}}
    print(json.dumps(output, ensure_ascii=False, allow_nan=False, separators=(",", ":")))


if __name__ == "__main__":
    main()
