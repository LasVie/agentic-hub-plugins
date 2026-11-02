"""Inspect both final ZIPs and exercise the extracted, bounded numerical runtime.

Adapted from offline-optics-lab/verify_package.py. Does not install a plugin,
start a server, call a model, or substitute for browser/user acceptance testing.
"""
from datetime import datetime, timezone
import hashlib
import importlib.util
import json
import math
from pathlib import Path, PurePosixPath
import stat
import tempfile
import zipfile


ROOT = Path(__file__).resolve().parents[2]
ASSET = Path(__file__).resolve().parent
SLUG = "offline-observing-planner"
VERSION = "1.0.0"
CANONICAL_SHA256 = "64903378e0b7906a0a9b178ff2046cf66d273c9f54a7e551497a48813a099ef9"
NATIVE_SHA256 = "6e9d379e35ce0b5a7d8e2d373c5eab3668cbbd091f47895ae340997749fb9b68"
PINNED_HASHES = {
    "runtime/astronomy.py": "41248c7b1edbf9d11119528eef7455a6dc55abde9f1aab40d363015e956c1729",
    "licenses/astronomy-engine/LICENSE": "a76df666a7db8a06f599d08e07c3ff74c4b250b50b49c43353af2bd5bb34604e",
    "licenses/astronomy-engine/PYTHON_LICENSE": "b4d9dd0fd80fce3879c4cd9e3754364f74fc5ec046f33276475ba3876785c8b7",
}


def digest(data):
    return hashlib.sha256(data).hexdigest()


def archive_files(path):
    with zipfile.ZipFile(path) as archive:
        assert archive.testzip() is None, "ZIP CRC failure"
        infos = archive.infolist()
        assert len({entry.filename for entry in infos}) == len(infos), "Duplicate ZIP names"
        for entry in infos:
            name = entry.filename
            relative = PurePosixPath(name)
            assert not relative.is_absolute() and ".." not in relative.parts and "\\" not in name
            assert not entry.is_dir(), "Expected only explicitly packaged regular files"
            assert not stat.S_ISLNK(entry.external_attr >> 16), "No archived symlinks"
        return {entry.filename: archive.read(entry) for entry in infos}


def main():
    canonical = ROOT / f"releases/agent-plugin/{SLUG}/{VERSION}/{SLUG}-{VERSION}.zip"
    native = ASSET / f"test-packages/{SLUG}-{VERSION}-workswarm.zip"
    assert digest(canonical.read_bytes()) == CANONICAL_SHA256
    assert digest(native.read_bytes()) == NATIVE_SHA256
    canonical_archive, native_files = archive_files(canonical), archive_files(native)
    prefix = f"{SLUG}/{SLUG}/"
    canonical_files = {name[len(prefix):]: value for name, value in canonical_archive.items()
                       if name.startswith(prefix)}
    assert set(canonical_archive) == {f"{SLUG}/plugin.yaml", *(prefix + name for name in canonical_files)}
    assert canonical_files == native_files, "Canonical/native payload differs"
    local_files = {path.relative_to(ASSET / SLUG).as_posix(): path.read_bytes()
                   for path in (ASSET / SLUG).rglob("*") if path.is_file()}
    assert local_files == native_files, "Source/native payload differs"
    forbidden_parts = {"__pycache__", ".git", ".DS_Store", "node_modules", "tests", "test-packages", ".research", "dist"}
    for name, value in native_files.items():
        assert not forbidden_parts.intersection(PurePosixPath(name).parts), name
        assert not name.endswith((".pyc", ".pyo", ".zip", ".log", ".png", ".jpg", ".jpeg")), name
        value.decode("utf-8")

    manifest = json.loads(native_files["manifest.json"])
    assert manifest["id"] == SLUG and manifest["version"] == VERSION
    assert manifest["name"] == manifest["display_name"]["zh"] == "离线观星规划台"
    assert len(manifest["tools"]) == 2 and len(manifest["skills"]) == 1
    for tool in manifest["tools"]:
        assert tool["file"] in native_files
        assert f"class {tool['class']}" in native_files[tool["file"]].decode()
    for skill in manifest["skills"]:
        assert skill["dir"] + "/SKILL.md" in native_files
    for path in ("assets/index.html", "assets/app.js", "assets/style.css", "runtime/lab.py", "runtime/engine.py"):
        assert path in native_files
    wrapper = canonical_archive[f"{SLUG}/plugin.yaml"].decode("utf-8")
    assert f"name: {SLUG}\n" in wrapper and f"version: {VERSION}\n" in wrapper
    assert "display_name: 离线观星规划台\n" in wrapper and "type: agent-plugin\n" in wrapper

    provenance = json.loads((ASSET / "provenance.json").read_text())
    assert provenance["mode"] == "ported" and provenance["permission_status"] == "verified"
    source, = provenance["sources"]
    assert source["url"] == "https://github.com/cosinekitty/astronomy"
    assert source["revision"] == "865d3da7d8112bbc7911238052c6af4aaf877181"
    assert source["version"] == "2.1.19" and source["license_expression"] == "MIT"
    assert provenance["reused_paths"] == ["runtime/astronomy.py"]
    assert {item["path"]: item["sha256"] for item in source["license_evidence"]} == PINNED_HASHES
    for path, expected in PINNED_HASHES.items():
        assert digest(native_files[path]) == expected, path
    for path in PINNED_HASHES:
        assert b"Permission is hereby granted, free of charge" in native_files[path]
    notices = native_files["THIRD_PARTY_NOTICES.md"].decode()
    assert "Astronomy Engine 2.1.19" in notices and source["revision"] in notices
    assert "licenses.txt" in native_files["assets/index.html"].decode()
    for path in ("README.md", "skills/observing-planner/SKILL.md", "assets/index.html"):
        assert "离线观星规划台" in native_files[path].decode()

    request = {"latitude": 1.3521, "longitude": 103.8198, "elevation_m": 15,
               "start_utc": "2026-10-30T12:00:00Z", "duration_hours": 24,
               "step_minutes": 30, "bodies": ["Sun", "Moon", "Mercury", "Venus", "Mars", "Jupiter", "Saturn"],
               "display_offset_minutes": 480}
    with tempfile.TemporaryDirectory(prefix="observing-extracted-package-") as temporary:
        payload = Path(temporary)
        for name, data in native_files.items():
            path = payload / name
            path.parent.mkdir(parents=True, exist_ok=True)
            path.write_bytes(data)
        spec = importlib.util.spec_from_file_location("archived_observing_lab", payload / "runtime/lab.py")
        lab = importlib.util.module_from_spec(spec)
        spec.loader.exec_module(lab)
        actual = lab.engine_call({"request": request})
        assert actual["ok"] and actual["version"] == VERSION and actual["engine_version"] == "2.1.19", actual
        assert len(actual["times"]) == 49
        assert [body["id"] for body in actual["bodies"]] == request["bodies"]
        for body in actual["bodies"]:
            assert len(body["track"]) == 49
            for sample in body["track"]:
                assert all(math.isfinite(sample[key]) for key in ("altitude_deg", "azimuth_deg", "ra_hours", "dec_deg"))
                assert -90 <= sample["altitude_deg"] <= 90 and 0 <= sample["azimuth_deg"] < 360
        shifted = lab.engine_call({"request": {**request, "start_utc": "2026-10-30T18:00:00Z"}})
        assert shifted["ok"] and shifted["version"] == VERSION
        moon_before = actual["bodies"][1]["track"][0]["altitude_deg"]
        moon_after = shifted["bodies"][1]["track"][0]["altitude_deg"]
        assert abs(moon_after - moon_before) > 1
        errors = {}
        for name, replacement, expected_code in (
            ("invalid_latitude", {"latitude": 90}, "out_of_range"),
            ("invalid_utc", {"start_utc": "2026-10-30T12:00:00"}, "invalid_time"),
        ):
            invalid = lab.engine_call({"request": {**request, **replacement}})
            assert invalid["ok"] is False and invalid["version"] == VERSION and "bodies" not in invalid
            assert invalid["error"]["code"] == expected_code
            assert any("\u4e00" <= character <= "\u9fff" for character in invalid["error"]["message"])
            errors[name] = invalid["error"]

    artifact = json.loads(canonical.with_name("artifact.json").read_text())
    file_hashes = {name: digest(data) for name, data in sorted(native_files.items())}
    assert artifact["sha256"] == CANONICAL_SHA256 and artifact["payload_sha256"] == file_hashes
    assert artifact["name"] == SLUG and artifact["version"] == VERSION and artifact["zip"] == canonical.name
    assert artifact["provenance_mode"] == "ported"
    report = {
        "verified_at": datetime.now(timezone.utc).isoformat(),
        "plugin_id": SLUG, "version": VERSION,
        "canonical_zip": str(canonical.relative_to(ROOT)), "canonical_sha256": CANONICAL_SHA256,
        "native_zip": str(native.relative_to(ROOT)), "native_sha256": NATIVE_SHA256,
        "payload_identical": True, "source_payload_identical": True, "payload_files": len(native_files),
        "files_sha256": file_hashes, "artifact_payload_hashes_verified": True,
        "declared_paths_verified": True, "license_and_module_hashes_verified": True,
        "upstream_revision": source["revision"], "utf8_files_verified": True, "forbidden_junk_absent": True,
        "extracted_baseline": {"request": request, "sample_count": len(actual["times"]),
                               "first_positions": {body["id"]: body["track"][0] for body in actual["bodies"]}},
        "shifted_time_moon": {"baseline_altitude_deg": moon_before, "shifted_altitude_deg": moon_after,
                              "changed_by_more_than_one_degree": True},
        "extracted_chinese_errors": errors, "passed": True,
        "scope": "ZIP/source equality, declared paths, licensing/provenance, UTF-8, artifact hashes and extracted real engine_call functionality. Not an independent accuracy reference, browser test, WorkSwarm chat/model invocation or manual user acceptance test.",
    }
    (ASSET / "package-verification.json").write_text(json.dumps(report, ensure_ascii=False, indent=2) + "\n", encoding="utf-8")
    print(json.dumps({key: value for key, value in report.items() if key not in {"files_sha256", "extracted_baseline"}}, ensure_ascii=False, indent=2))


if __name__ == "__main__":
    main()
