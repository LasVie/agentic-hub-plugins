"""Finite FIFO SimPy adapter. Runs only in an isolated child interpreter."""
from __future__ import annotations

import csv
from decimal import Decimal, InvalidOperation
import io
import json
from pathlib import Path
import sys

sys.dont_write_bytecode = True
ROOT = Path(__file__).resolve().parents[1]
# This path belongs only to this -I worker; the host never imports SimPy.
sys.path.insert(0, str(ROOT / "vendor"))
import simpy

VERSION = "1.0.1"
MAX_BYTES = 256 * 1024


def strict_json(data):
    def pairs(items):
        result = {}
        for key, value in items:
            if key in result:
                raise ValueError("JSON 包含重复字段。")
            result[key] = value
        return result

    def constant(_):
        raise ValueError("JSON 不能包含 NaN 或无穷大。")

    return json.loads(data, object_pairs_hook=pairs, parse_constant=constant)


def exact_keys(value, keys, label):
    if not isinstance(value, dict) or set(value) != set(keys):
        raise ValueError(label + "字段不完整或包含不支持的字段。")


def text(value, maximum, label):
    if (not isinstance(value, str) or not value.strip() or len(value) > maximum
            or any(ord(c) < 32 or 127 <= ord(c) < 160 for c in value)):
        raise ValueError(f"{label}必须是非空文本，最多 {maximum} 字，且不含控制字符。")
    return value


def ticks(value, *, positive=False):
    if type(value) not in (float, int):
        raise ValueError("到达和服务时间必须是数值，单位分钟。")
    try:
        number = Decimal(str(value))
        scaled = number * 1000
        if (not number.is_finite() or number < (Decimal('0.001') if positive else 0)
                or number > 100000 or scaled != scaled.to_integral_value()):
            raise ValueError("时间须在 0 至 100000 分钟内，精度最多三位小数；服务时间至少 0.001 分钟。")
        return int(scaled)
    except InvalidOperation:
        raise ValueError("时间数值无效。") from None


def validate(project):
    exact_keys(project, ["schema", "name", "units", "capacities", "jobs"], "场景")
    if project["schema"] != "queue-capacity-workbench/v1" or project["units"] != "minutes":
        raise ValueError("仅支持 queue-capacity-workbench/v1，units 必须为 minutes。")
    text(project["name"], 80, "场景名称")
    capacities = project["capacities"]
    if (not isinstance(capacities, list) or not 1 <= len(capacities) <= 8
            or any(type(c) is not int or not 1 <= c <= 32 for c in capacities)
            or len(set(capacities)) != len(capacities)):
        raise ValueError("capacities 须包含 1 至 8 个不重复的整数，每个介于 1 和 32。")
    jobs = project["jobs"]
    if not isinstance(jobs, list) or not 1 <= len(jobs) <= 500:
        raise ValueError("场景须包含 1 至 500 个作业。")
    normalized, identifiers = [], set()
    for index, job in enumerate(jobs):
        exact_keys(job, ["id", "arrival", "service"], "作业")
        identifier = text(job["id"], 40, "作业标识")
        if identifier in identifiers:
            raise ValueError("作业标识不能重复。")
        identifiers.add(identifier)
        normalized.append({"id": identifier, "arrival": ticks(job["arrival"]),
                           "service": ticks(job["service"], positive=True), "index": index})
    if sum(j["service"] for j in normalized) > 500000000:
        raise ValueError("服务时间总和不得超过 500000 分钟。")
    return normalized


def minutes(value):
    return value / 1000


def simulate(jobs, capacity):
    env = simpy.Environment()
    resource = simpy.Resource(env, capacity=capacity)
    servers = list(range(1, capacity + 1))
    events, records, waiting, active, completed = [], {}, set(), set(), set()

    def emit(kind, identifier, server=None):
        events.append({"seq": len(events) + 1, "time": minutes(env.now), "kind": kind,
                       "job_id": identifier, "server": server,
                       "waiting": len(waiting), "active": len(active), "completed": len(completed)})

    def process(job):
        yield env.timeout(job["arrival"])
        identifier = job["id"]
        waiting.add(identifier)
        emit("arrival", identifier)
        with resource.request() as request:
            yield request
            server = min(servers)
            servers.remove(server)
            waiting.remove(identifier)
            active.add(identifier)
            start = env.now
            emit("start", identifier, server)
            yield env.timeout(job["service"])
            active.remove(identifier)
            completed.add(identifier)
            servers.append(server)
            emit("finish", identifier, server)
            records[identifier] = {"id": identifier, "arrival": minutes(job["arrival"]),
                                   "service": minutes(job["service"]), "start": minutes(start),
                                   "finish": minutes(env.now), "wait": minutes(start - job["arrival"]),
                                   "server": server}

    # Preserve source order for equal arrivals. Finite processes drain completely;
    # a numeric run(until=...) would silently omit boundary-time events.
    for job in sorted(jobs, key=lambda j: (j["arrival"], j["index"])):
        env.process(process(job))
    env.run()
    rows = [records[j["id"]] for j in jobs]
    horizon = minutes(env.now)
    # Positive wait intervals [arrival, start); group equal timestamps so
    # zero-duration request/grant transitions do not inflate max_queue.
    changes = {}
    for row in rows:
        if row["wait"] > 0:
            changes[row["arrival"]] = changes.get(row["arrival"], 0) + 1
            changes[row["start"]] = changes.get(row["start"], 0) - 1
    queued = peak = 0
    for when in sorted(changes):
        queued += changes[when]
        peak = max(peak, queued)
    waits = [r["wait"] for r in rows]
    metrics = {"jobs": len(rows), "mean_wait": sum(waits) / len(rows), "max_wait": max(waits),
               "completion_time": horizon, "max_queue": peak,
               "mean_queue": sum(waits) / horizon,
               "utilization": sum(j["service"] for j in jobs) / (env.now * capacity)}
    return {"capacity": capacity, "metrics": metrics, "jobs": rows, "events": events}


def csv_cell(value):
    # Preserve data in JSON; spreadsheet exports must not execute a formula.
    if isinstance(value, str) and value.lstrip().startswith(("=", "+", "-", "@")):
        return "'" + value
    return value


def calculate(project):
    jobs = validate(project)
    runs = [simulate(jobs, c) for c in project["capacities"]]
    stream = io.StringIO(newline="")
    writer = csv.writer(stream)
    writer.writerow(["容量", "作业标识", "到达分钟", "服务分钟", "开始分钟", "结束分钟", "等待分钟", "服务台"])
    for run in runs:
        for row in run["jobs"]:
            writer.writerow([run["capacity"], csv_cell(row["id"]), row["arrival"], row["service"],
                             row["start"], row["finish"], row["wait"], row["server"]])
    return {"ok": True, "version": VERSION, "engine": "SimPy " + simpy.__version__,
            "message": "计算完成。全部作业已处理，结果可回放、比较和导出。",
            "project": project, "runs": runs, "csv": stream.getvalue()}


def main():
    # Deny worker network even if a later adapter change accidentally adds it.
    def audit(event, _args):
        if event.startswith("socket."):
            raise RuntimeError("计算进程不允许访问网络。")
    sys.addaudithook(audit)
    try:
        data = sys.stdin.buffer.read(MAX_BYTES + 1)
        if len(data) > MAX_BYTES:
            raise ValueError("场景超过 256 KiB 上限。")
        result = calculate(strict_json(data.decode("utf-8")))
    except (ValueError, TypeError, UnicodeError, RecursionError):
        error = sys.exception()
        # Parser errors can quote untrusted content; expose a fixed Chinese message.
        message = str(error) if type(error) is ValueError and not isinstance(error, json.JSONDecodeError) else "场景 JSON 无效，请检查格式与数值。"
        result = {"ok": False, "version": VERSION, "error": message}
    except Exception:
        result = {"ok": False, "version": VERSION, "error": "本地排队引擎未完成计算，请检查插件完整性。"}
    sys.stdout.write(json.dumps(result, ensure_ascii=False, allow_nan=False))


if __name__ == "__main__":
    main()
