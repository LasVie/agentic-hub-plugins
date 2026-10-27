import hashlib
import io
import json
from pathlib import Path
import sys
import zipfile


def build(canonical, output):
    canonical = Path(canonical)
    output = Path(output)
    payloads = {}
    with zipfile.ZipFile(canonical) as archive:
        for name in archive.namelist():
            if name.startswith("rss-daily/rss-daily/") and not name.endswith("/"):
                relative = name[len("rss-daily/rss-daily/"):]
                if ".." in Path(relative).parts or Path(relative).is_absolute():
                    raise ValueError("归档路径不安全")
                payloads[relative] = archive.read(name)
    manifest = json.loads(payloads["manifest.json"])
    if manifest["id"] != "rss-daily" or manifest["version"] != "1.0.0":
        raise ValueError("插件身份或版本不匹配")
    buffer = io.BytesIO()
    with zipfile.ZipFile(buffer, "w", compression=zipfile.ZIP_DEFLATED, compresslevel=9) as archive:
        for relative, content in sorted(payloads.items()):
            entry = zipfile.ZipInfo("rss-daily/" + relative, (2026, 1, 1, 0, 0, 0))
            entry.compress_type = zipfile.ZIP_DEFLATED
            entry.external_attr = 0o100644 << 16
            archive.writestr(entry, content)
    content = buffer.getvalue()
    output.mkdir(parents=True, exist_ok=True)
    target = output / "rss-daily-1.0.0-workswarm.zip"
    if target.exists() and target.read_bytes() != content:
        raise ValueError("已有同版本测试包内容不同，请升级版本而不是覆盖")
    target.write_bytes(content)
    extracted = output / "extracted"
    if extracted.exists():
        raise ValueError("解压目标已存在，请使用新的验证目录")
    with zipfile.ZipFile(target) as archive:
        archive.extractall(extracted)
    for relative, expected in payloads.items():
        if (extracted / "rss-daily" / relative).read_bytes() != expected:
            raise ValueError("解压载荷校验失败：" + relative)
    record = {"version": "1.0.0", "canonical_sha256": hashlib.sha256(canonical.read_bytes()).hexdigest(),
              "workswarm_sha256": hashlib.sha256(content).hexdigest(), "payload_files": len(payloads),
              "canonical_zip": str(canonical.resolve()), "workswarm_zip": str(target.resolve()),
              "extracted_payload": str((extracted / "rss-daily").resolve()), "payload_equal": True}
    (output / "package-verification.json").write_text(json.dumps(record, ensure_ascii=False, indent=2) + "\n", encoding="utf-8")
    print(json.dumps(record, ensure_ascii=False, indent=2))


if __name__ == "__main__":
    build(*sys.argv[1:])
