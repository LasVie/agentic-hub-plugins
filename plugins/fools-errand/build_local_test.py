import argparse
import hashlib
import io
import json
from pathlib import Path
import sys
import zipfile

REPOSITORY = Path(__file__).resolve().parents[2]
sys.path.insert(0, str(REPOSITORY))
from tools.asset_release import inspect_zip


def build_local_test(canonical_zip, output_directory):
    canonical_bytes = canonical_zip.read_bytes()
    metadata, expected_hashes = inspect_zip(canonical_bytes)
    prefix = f"{metadata['name']}/{metadata['name']}/"
    buffer = io.BytesIO()
    with zipfile.ZipFile(io.BytesIO(canonical_bytes)) as original:
        with zipfile.ZipFile(buffer, "w", compression=zipfile.ZIP_STORED) as native:
            for member in sorted(original.namelist()):
                if member.startswith(prefix):
                    relative = member[len(prefix):]
                    entry = zipfile.ZipInfo(f"{metadata['name']}/{relative}", (1980, 1, 1, 0, 0, 0))
                    entry.create_system = 3
                    entry.external_attr = 0o100644 << 16
                    native.writestr(entry, original.read(member))
    native_bytes = buffer.getvalue()
    with zipfile.ZipFile(io.BytesIO(native_bytes)) as native:
        actual_hashes = {
            member.split("/", 1)[1]: hashlib.sha256(native.read(member)).hexdigest()
            for member in native.namelist()
        }
    if actual_hashes != expected_hashes:
        raise ValueError("原生包与规范包的运行载荷不一致")
    output_directory.mkdir(parents=True, exist_ok=True)
    destination = output_directory / f"{metadata['name']}-{metadata['version']}-workswarm.zip"
    if destination.exists() and destination.read_bytes() != native_bytes:
        raise ValueError("已有同版本测试包内容不同，请先递增版本，不覆盖旧包")
    destination.write_bytes(native_bytes)
    record = {
        "version": metadata["version"],
        "candidate_id": "CAND-CLD-142",
        "task_id": "AH-20261027-fools-errand",
        "native_zip": str(destination),
        "native_zip_sha256": hashlib.sha256(native_bytes).hexdigest(),
        "canonical_zip": str(canonical_zip),
        "canonical_zip_sha256": hashlib.sha256(canonical_bytes).hexdigest(),
        "payloads_identical": True,
        "payload_sha256": actual_hashes,
        "user_test_completion": "Pending for this exact version and ZIP; no user confirmation claimed"
    }
    (output_directory / "local-test-artifact.json").write_text(
        json.dumps(record, ensure_ascii=False, indent=2) + "\n", encoding="utf-8"
    )
    return record


if __name__ == "__main__":
    parser = argparse.ArgumentParser(description="从规范包生成相同载荷的 WorkSwarm 原生测试包")
    parser.add_argument("canonical_zip", type=Path)
    parser.add_argument("output_directory", type=Path)
    arguments = parser.parse_args()
    result = build_local_test(arguments.canonical_zip.resolve(), arguments.output_directory.resolve())
    print(json.dumps(result, ensure_ascii=False, indent=2))
