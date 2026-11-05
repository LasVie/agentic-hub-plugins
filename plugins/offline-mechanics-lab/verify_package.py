"""Check the exact canonical/native archives; extract verified payload for tests."""
from datetime import datetime, timezone
import hashlib
import json
from pathlib import Path, PurePosixPath
import stat
import zipfile

ASSET = Path(__file__).resolve().parent
ROOT = ASSET.parents[1]
SLUG = "offline-mechanics-lab"
VERSION = "1.0.0"
CANONICAL = "b69f0177931df25d7103aede52ac8e2177cc5e8e5ff252d36ac48edd724f758b"
NATIVE = "e850a5458ea3fb7ef22b31bdfd79f68482f6144ed17508e1d86e4fa4bdf69319"
UPSTREAM = {
    "assets/vendor/matter.js": "016f108075a42e8bb8f75c43cf5b6d9f07b1d88857975ed9d96b0ede921416ce",
    "licenses/matter-js/LICENSE": "ed182087be5b26734aa6d4789743de3a97417950e8c1e3ff2e3d19c6462720d3",
}
sha = lambda data: hashlib.sha256(data).hexdigest()


def read_zip(path, expected):
    assert sha(path.read_bytes()) == expected
    with zipfile.ZipFile(path) as z:
        assert z.testzip() is None
        assert len(z.namelist()) == len(set(z.namelist()))
        for info in z.infolist():
            p = PurePosixPath(info.filename)
            assert not p.is_absolute() and ".." not in p.parts and "\\" not in info.filename
            assert not info.is_dir() and not stat.S_ISLNK(info.external_attr >> 16)
        return {name: z.read(name) for name in z.namelist()}


def main():
    canonical = ROOT / f"releases/agent-plugin/{SLUG}/{VERSION}/{SLUG}-{VERSION}.zip"
    native = ASSET / f"test-packages/{SLUG}-{VERSION}-workswarm.zip"
    wrapped, files = read_zip(canonical, CANONICAL), read_zip(native, NATIVE)
    prefix = f"{SLUG}/{SLUG}/"
    assert wrapped == {f"{SLUG}/plugin.yaml": wrapped[f"{SLUG}/plugin.yaml"], **{prefix+k:v for k,v in files.items()}}
    source = {p.relative_to(ASSET / SLUG).as_posix(): p.read_bytes() for p in (ASSET / SLUG).rglob("*") if p.is_file() and "__pycache__" not in p.parts}
    assert source == files
    for name, data in files.items():
        assert not {"tests", "dist", "__pycache__", ".git", "node_modules"}.intersection(PurePosixPath(name).parts)
        assert not name.endswith((".pyc", ".log", ".png", ".zip"))
        data.decode("utf-8")
    manifest = json.loads(files["manifest.json"])
    assert manifest["id"] == SLUG and manifest["version"] == VERSION and manifest["package_type"] == "plugin"
    assert manifest["name"] == "离线力学实验室"
    assert len(manifest["tools"]) == 1 and len(manifest["skills"]) == 1
    for tool in manifest["tools"]:
        assert f"class {tool['class']}" in files[tool["file"]].decode()
    for skill in manifest["skills"]:
        assert skill["dir"] + "/SKILL.md" in files
    wrapper = wrapped[f"{SLUG}/plugin.yaml"].decode()
    for text in (f"name: {SLUG}\n", f"version: {VERSION}\n", "type: agent-plugin\n", "display_name: 离线力学实验室\n"):
        assert text in wrapper
    for name, expected in UPSTREAM.items():
        assert sha(files[name]) == expected
        assert b"Permission is hereby granted, free of charge" in files[name]
    provenance = json.loads((ASSET / "provenance.json").read_text())
    assert provenance["mode"] == "ported" and provenance["permission_status"] == "verified"
    assert provenance["reused_paths"] == ["assets/vendor/matter.js"]
    source_record = provenance["sources"][0]
    assert source_record["revision"] == "8a67787735585f02c4b46eabf7b9fcc1c7c321da"
    for evidence in source_record["license_evidence"]:
        assert sha(files[evidence["path"]]) == evidence["sha256"]
    assert source_record["revision"] in files["THIRD_PARTY_NOTICES.md"].decode()
    for name in ("README.md", "skills/mechanics-lab/SKILL.md", "assets/index.html"):
        assert "离线力学实验室" in files[name].decode()
    hashes = {n:sha(v) for n,v in sorted(files.items())}
    artifact = json.loads(canonical.with_name("artifact.json").read_text())
    assert artifact["sha256"] == CANONICAL and artifact["payload_sha256"] == hashes
    extracted = ROOT / f"dist/{SLUG}/{VERSION}/verified-payload"
    for name, data in files.items():
        target = extracted / name
        if target.exists():
            assert target.read_bytes() == data, "Refusing to overwrite differing extracted payload"
        else:
            target.parent.mkdir(parents=True, exist_ok=True)
            target.write_bytes(data)
    report = {"verified_at":datetime.now(timezone.utc).isoformat(),"plugin_id":SLUG,"version":VERSION,
              "canonical_sha256":CANONICAL,"workswarm_sha256":NATIVE,"payload_files":len(files),
              "source_canonical_native_equal":True,"declared_paths_verified":True,"license_hashes_verified":True,
              "utf8_verified":True,"artifact_payload_hashes_verified":True,"payload_sha256":hashes,"passed":True,
              "scope":"Archive/source equality and extracted payload inspection only; functional/browser/host tests are separate."}
    (ASSET / "package-verification.json").write_text(json.dumps(report,ensure_ascii=False,indent=2)+"\n")
    print(json.dumps({k:v for k,v in report.items() if k!="payload_sha256"},ensure_ascii=False,indent=2))


if __name__ == "__main__":
    main()
