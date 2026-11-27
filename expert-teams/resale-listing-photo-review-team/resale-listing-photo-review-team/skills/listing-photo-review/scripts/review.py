"""核对照片意见的范围、来源与交付证据。"""
import argparse
from hashlib import sha256
from html import escape
import json
from pathlib import Path
import re


VERSION = "1.0.0"
MAX_PHOTO = 8 * 1024 * 1024
MAX_JSON = 256 * 1024
REACTIONS = {"usable": "可用", "retake": "补拍", "confirm": "待确认"}
JPEG = b"\xff\xd8\xff"
PNG = b"\x89PNG\r\n\x1a\n"


def require(condition, reason):
    if not condition:
        raise ValueError(reason)


def digest(data):
    return sha256(data).hexdigest()


def unique_object(pairs):
    result = {}
    for key, value in pairs:
        require(key not in result, "JSON 存在重复字段")
        result[key] = value
    return result


def read_json(path):
    require(path.is_file() and not path.is_symlink(), "需要普通 JSON 文件")
    with path.open("rb") as stream:
        data = stream.read(MAX_JSON + 1)
    require(len(data) <= MAX_JSON, "JSON 超过 256 KiB")
    try:
        return json.loads(data.decode("utf-8-sig"), object_pairs_hook=unique_object), digest(data)
    except (json.JSONDecodeError, UnicodeError) as error:
        raise ValueError("需要有效的 UTF-8 JSON") from error


def record(value, fields):
    require(isinstance(value, dict) and set(value) == set(fields), "JSON 记录字段与说明不符")
    return value


def sequence(value, lower, upper):
    require(isinstance(value, list) and lower <= len(value) <= upper, "列表数量超出本次支持范围")
    return value


def note(value, limit=240):
    require(isinstance(value, str) and 0 < len(value.strip()) <= limit, "说明应为简短的非空文字")
    value = value.strip()
    require(not any(ord(char) < 32 for char in value), "说明中含控制字符，请改为单行文字")
    return value


def identifiers(value, allowed, maximum, minimum=0):
    values = sequence(value, minimum, maximum)
    require(all(isinstance(key, str) and key in allowed for key in values), "引用了批次外的照片编号")
    require(len(set(values)) == len(values), "照片编号重复")
    return values


def photo_ref(root, name):
    name = note(name, 180)
    parts = name.split("/")
    require(all(part not in ("", ".", "..") and "\\" not in part for part in parts), "照片必须使用目录内的相对路径")
    path = root
    for part in parts:
        path = path / part
        require(not path.is_symlink(), "照片路径含符号链接")
    suffix = path.suffix.lower()
    require(path.is_file() and suffix in (".jpg", ".jpeg", ".png"), "照片须为普通 JPEG 或 PNG 文件")
    with path.open("rb") as stream:
        data = stream.read(MAX_PHOTO + 1)
    require(0 < len(data) <= MAX_PHOTO, "单张照片不可为空或超过 8 MiB")
    require(data.startswith(PNG if suffix == ".png" else JPEG), "照片扩展名与文件头不一致")
    return {"name": name, "sha256": digest(data)}


def prepare(source, photos):
    payload, source_hash = read_json(source)
    record(payload, ("items",))
    require(photos.is_dir() and not photos.is_symlink(), "请选择普通照片目录")
    root = photos.resolve()
    known_items, seen_files = set(), {}
    items = []
    for entry in sequence(payload["items"], 1, 6):
        record(entry, ("id", "title", "photos", "checks"))
        item_id = entry["id"]
        require(isinstance(item_id, str) and re.fullmatch(r"[A-Za-z0-9_-]{1,24}", item_id), "商品编号须由 1–24 位字母、数字、下划线或连字符组成")
        require(item_id not in known_items, "商品编号重复")
        known_items.add(item_id)
        images = {}
        names = set()
        for number, name in enumerate(sequence(entry["photos"], 1, 10), start=1):
            ref = photo_ref(root, name)
            require(ref["name"] not in names, "同一商品重复填写照片路径")
            names.add(ref["name"])
            require(seen_files.setdefault(ref["sha256"], item_id) == item_id, "两个商品引用了相同照片内容，请核对归属")
            images[f"p{number:02d}"] = ref
        checks = {f"c{n:02d}": note(text) for n, text in enumerate(sequence(entry["checks"], 1, 8), start=1)}
        items.append({"id": item_id, "title": note(entry["title"], 100), "checks": checks, "photos": images})
    require(sum(len(item["photos"]) for item in items) <= 24, "本轮最多 24 张照片")
    return {"version": VERSION, "source_sha256": source_hash, "items": items}


def checked_batch(batch_path, source, photos):
    batch, batch_hash = read_json(batch_path)
    require(batch == prepare(source, photos), "商品说明或原照片已变化，请用新目录重新核对")
    return batch, batch_hash


def normalize_answer(batch, answer):
    record(answer, ("items",))
    by_id = record(answer["items"], (item["id"] for item in batch["items"]))
    normalized = {}
    for item in batch["items"]:
        raw = record(by_id[item["id"]], ("covers", "photos", "checks"))
        photo_keys = item["photos"]
        statuses = record(raw["photos"], photo_keys)
        require(all(isinstance(status, str) and status in REACTIONS for status in statuses.values()), "请给每张照片填写可用、补拍或待确认状态")
        usable = {key for key, status in statuses.items() if status == "usable"}
        covers = identifiers(raw["covers"], usable, len(usable))
        checks = {}
        for key, result in record(raw["checks"], item["checks"]).items():
            record(result, ("status", "photos", "note"))
            status = result["status"]
            require(isinstance(status, str) and status in ("supported", "retake", "confirm"), "核对项状态须为支持、补拍或待确认")
            positive = status == "supported"
            refs = identifiers(result["photos"], usable, len(usable) if positive else 0, 1 if positive else 0)
            checks[key] = {"status": status, "photos": refs, "note": note(result["note"])}
        normalized[item["id"]] = {"covers": covers, "photos": statuses, "checks": checks}
    return {"items": normalized}


def role_review(path, role, batch, batch_hash):
    receipt, receipt_hash = read_json(path)
    record(receipt, ("version", "role", "batch_sha256", "review"))
    require(receipt["version"] == VERSION and receipt["role"] == role and receipt["batch_sha256"] == batch_hash,
            "意见与当前批次或指定角色不符")
    require(receipt["review"] == normalize_answer(batch, receipt["review"]), "意见文件内容未规范化")
    return receipt["review"]["items"], receipt_hash


def select_item(item, evidence, verification):
    photos = item["photos"]
    issues, order = [], []
    covers = [key for key in verification["covers"] if key in evidence["covers"]]
    if covers:
        order.append(covers[0])
    else:
        issues.append({"check": "主图", "status": "confirm", "notes": ["请确认同一商品的清晰完整主图，必要时补拍全景。"]})
    for code, label in item["checks"].items():
        first, second = evidence["checks"][code], verification["checks"][code]
        supported = [key for key in second["photos"] if key in first["photos"]]
        if supported:
            order.append(supported[0])
            continue
        status = "confirm" if "confirm" in (first["status"], second["status"]) or first["status"] == second["status"] == "supported" else "retake"
        issues.append({"check": label, "status": status, "notes": list(dict.fromkeys((first["note"], second["note"])))})
    # Continue to use only one original when frames are exact byte duplicates.
    seen_hashes = set()
    filenames = []
    for key in order:
        ref = photos[key]
        if ref["sha256"] not in seen_hashes:
            filenames.append(ref["name"])
            seen_hashes.add(ref["sha256"])
    status = "ready" if not issues else "hold"
    return {"id": item["id"], "title": item["title"], "status": status,
            "cover": filenames[0] if status == "ready" else None,
            "order": filenames if status == "ready" else [], "issues": issues}


def render(report):
    sections = []
    for item in report["items"]:
        title = escape(item["title"])
        if item["status"] == "ready":
            pictures = "".join(f"<li>{escape(name)}</li>" for name in item["order"])
            summary = f"<p>照片复核通过 · 第一张为主图</p><ol>{pictures}</ol>"
        else:
            problems = "".join(
                f"<li><strong>{REACTIONS[issue['status']]} · {escape(issue['check'])}</strong>"
                f"<p>{escape(' / '.join(issue['notes']))}</p></li>" for issue in item["issues"]
            )
            summary = f"<p>暂缓 · 完成下列事项后重跑</p><ul>{problems}</ul>"
        sections.append(f"<section><h2>{title}</h2>{summary}</section>")
    return """<!doctype html><html lang="zh-CN"><meta charset="utf-8">
<meta name="viewport" content="width=device-width,initial-scale=1">
<title>二手商品照片上架清单</title>
<style>
body{font:16px/1.6 system-ui,sans-serif;background:#edf3f3;color:#17353e;margin:0}
main{max-width:760px;margin:auto;padding:24px}
section{background:#fff;border:1px solid #bed0d2;border-radius:12px;margin:16px 0;padding:16px 22px}
h2{margin:0} p{margin:.45rem 0} li{overflow-wrap:anywhere}
a{color:#185754}
</style><main><h1>二手商品照片上架清单</h1>""" + "".join(sections) + """
<p>请自行核实商品状况并发布。<a href="report.json">查看逐项 JSON</a></p></main></html>
"""


def write_files(out, files):
    require(out.parent.is_dir(), "请先选择已存在的输出父目录")
    require(not out.exists() and not out.is_symlink(), "输出目录已存在，请换用新目录")
    out.mkdir()
    for name, value in files.items():
        with (out / name).open("x", encoding="utf-8") as stream:
            stream.write(value if isinstance(value, str) else json.dumps(value, ensure_ascii=False, indent=2) + "\n")


class ChineseParser(argparse.ArgumentParser):
    def error(self, message):
        self.exit(2, "参数无效，请用 --help 查看用法。\n")


def parser():
    p = ChineseParser(add_help=False, usage="review.py {prepare,seal,deliver} [参数]")
    p._optionals.title = "选项"
    p.add_argument("-h", "--help", action="help", help="显示帮助")
    p.add_argument("stage", choices=("prepare", "seal", "deliver"), metavar="阶段")
    p.add_argument("--source", type=Path, required=True, help="商品说明 JSON")
    p.add_argument("--photos", type=Path, required=True, help="授权照片目录")
    p.add_argument("--out", type=Path, required=True, help="待创建的输出目录")
    p.add_argument("--batch", type=Path, help="批次 JSON")
    p.add_argument("--role", choices=("evidence", "verifier"), help="提交意见的角色")
    p.add_argument("--answer", type=Path, help="逐项意见 JSON")
    p.add_argument("--evidence", type=Path, help="整理员封存意见")
    p.add_argument("--verify", type=Path, help="复核员封存意见")
    return p


def run(args):
    if args.stage == "prepare":
        files = {"batch.json": prepare(args.source, args.photos)}
    else:
        require(args.batch is not None, "请提供 --batch")
        batch, batch_hash = checked_batch(args.batch, args.source, args.photos)
        if args.stage == "seal":
            require(args.role and args.answer is not None, "请提供 --role 和 --answer")
            answer = normalize_answer(batch, read_json(args.answer)[0])
            files = {"review.json": {"version": VERSION, "role": args.role, "batch_sha256": batch_hash, "review": answer}}
        else:
            require(args.evidence is not None and args.verify is not None, "请提供两份封存意见")
            evidence, evidence_hash = role_review(args.evidence, "evidence", batch, batch_hash)
            review, review_hash = role_review(args.verify, "verifier", batch, batch_hash)
            items = [select_item(item, evidence[item["id"]], review[item["id"]]) for item in batch["items"]]
            report = {"version": VERSION, "batch_sha256": batch_hash, "evidence_sha256": evidence_hash,
                      "verification_sha256": review_hash, "items": items}
            files = {"checklist.html": render(report), "report.json": report}
    write_files(args.out, files)
    print(f"已保存 {len(files)} 份文件。")


if __name__ == "__main__":
    p = parser()
    try:
        run(p.parse_args())
    except (OSError, ValueError) as error:
        p.exit(2, f"无法完成照片复核阶段：{error}\n")
