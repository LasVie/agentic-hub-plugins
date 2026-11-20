"""Check the actual WorkSwarm SDK, using fresh asset-owned negative fixtures."""
from hashlib import sha256
from importlib.metadata import version
from pathlib import Path
from tempfile import mkdtemp
import json
import shutil
import sys
from openjiuwen.agent_teams.experts import load_agent_group_package_bundle

ASSET = Path(__file__).resolve().parents[1]


def check(payload, archive):
    specs = {
        "leader": "meeting-delivery", "analyst": "meeting-intake",
        "planner": "meeting-planning", "verifier": "independent-timezone-review",
    }
    bundle = load_agent_group_package_bundle(payload)
    assert set(bundle.templates) == set(specs)
    evidence = {}
    for name, t in bundle.templates.items():
        skills = sorted(Path(s.dir).name for s in t.skills)
        sections = [p.name for p in t.prompt_sections]
        assert skills == sorted([specs[name], "meeting-evidence"]), skills
        assert "agent_group_instruction" in sections
        assert ("agent_group_leader_rules" in sections) == (name == "leader")
        evidence[name] = {"skills": skills, "prompt_sections": sections}
    root = ASSET / ".local/loader-negative"
    root.mkdir(parents=True, exist_ok=True)
    bad = []
    for case in ("wrong-member-type", "no-leader-entry", "missing-member"):
        sample = Path(mkdtemp(dir=root, prefix=case + "-")) / payload.name
        shutil.copytree(payload, sample)
        if case == "wrong-member-type":
            path = sample / "agents/analyst/manifest.json"
            data = json.loads(path.read_text())
            data["package_type"] = "plugin"
            path.write_text(json.dumps(data))
        elif case == "no-leader-entry":
            path = sample / "agents/leader/AGENT.md"
            path.rename(sample.parent / "preserved-AGENT.md")
        else:
            (sample / "agents/verifier").rename(sample.parent / "preserved-verifier")
        try:
            load_agent_group_package_bundle(sample)
        except ValueError as error:
            bad.append({"case": case, "rejected": True, "reason": str(error).replace(str(sample), "<negative-fixture>")})
        else:
            raise AssertionError(f"Loader accepted {case}")
    return {"loader": "openjiuwen.agent_teams.experts.load_agent_group_package_bundle",
            "sdk": version("openjiuwen"), "native_sha256": sha256(archive.read_bytes()).hexdigest(),
            "members": evidence, "negative_controls": bad}


if __name__ == "__main__":
    result = check(Path(sys.argv[1]), Path(sys.argv[2]))
    (ASSET / "tests/records/host-loader.json").write_text(json.dumps(result, ensure_ascii=False, indent=2) + "\n")
    print(json.dumps(result, ensure_ascii=False))
