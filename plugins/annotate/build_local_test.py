import argparse
import hashlib
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
    output_directory.mkdir(parents=True, exist_ok=True)
    destination = output_directory / f"{metadata['name']}-{metadata['version']}-workswarm.zip"
    with zipfile.ZipFile(canonical_zip) as original:
        with zipfile.ZipFile(destination, "w", compression=zipfile.ZIP_STORED) as native:
            for member in sorted(original.namelist()):
                if not member.startswith(prefix):
                    continue
                relative = member[len(prefix):]
                info = zipfile.ZipInfo(f"{metadata['name']}/{relative}", (1980, 1, 1, 0, 0, 0))
                info.create_system = 3
                info.external_attr = 0o100644 << 16
                native.writestr(info, original.read(member))
    with zipfile.ZipFile(destination) as native:
        actual_hashes = {
            member.split("/", 1)[1]: hashlib.sha256(native.read(member)).hexdigest()
            for member in native.namelist()
        }
    if actual_hashes != expected_hashes:
        raise ValueError("Native and canonical payload hashes differ")
    record = {
        "version": metadata["version"],
        "candidate_id": "CAND-CLD-264",
        "task_id": "AH-20261022-annotate",
        "native_zip": str(destination),
        "native_zip_sha256": hashlib.sha256(destination.read_bytes()).hexdigest(),
        "canonical_zip": str(canonical_zip),
        "canonical_zip_sha256": hashlib.sha256(canonical_bytes).hexdigest(),
        "payloads_identical": True,
        "payload_sha256": actual_hashes,
        "user_test_completion": "Pending; no confirmation has been given for either ZIP"
    }
    (output_directory / "local-test-artifact.json").write_text(json.dumps(record, ensure_ascii=False, indent=2) + "\n", encoding="utf-8")
    return record


if __name__ == "__main__":
    parser = argparse.ArgumentParser()
    parser.add_argument("canonical_zip", type=Path)
    parser.add_argument("output_directory", type=Path)
    arguments = parser.parse_args()
    result = build_local_test(arguments.canonical_zip.resolve(), arguments.output_directory.resolve())
    print(json.dumps({key: value for key, value in result.items() if key != "payload_sha256"}, ensure_ascii=False, indent=2))
