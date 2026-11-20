"""Load the exact extracted AgentGroup using the target WorkSwarm SDK."""

from hashlib import sha256
from importlib.metadata import version
import json
import os
from pathlib import Path
import shutil
import sys
from tempfile import mkdtemp

from host_order import ASSET, PRIVATE, SHARED


def check(payload, native):
    from openjiuwen.agent_teams.experts import load_agent_group_package_bundle

    bundle = load_agent_group_package_bundle(payload)
    assert set(bundle.templates) == set(PRIVATE)
    members = {}
    for name, template in bundle.templates.items():
        skills = sorted(Path(skill.dir).name for skill in template.skills)
        sections = [section.name for section in template.prompt_sections]
        assert skills == sorted((PRIVATE[name], SHARED))
        assert "agent_group_instruction" in sections
        assert ("agent_group_leader_rules" in sections) == (name == "leader")
        members[name] = {"skills": skills, "prompt_sections": sections}
    scratch = Path(mkdtemp(prefix="loader-negative-", dir=ASSET / ".local"))
    sample = scratch / payload.name
    shutil.copytree(payload, sample)
    (sample / "agents/verifier").rename(scratch / "preserved-verifier")
    try:
        load_agent_group_package_bundle(sample)
    except ValueError as error:
        reason = str(error).replace(str(sample), "<fixture>")
    else:
        raise AssertionError("Missing verifier was accepted")
    return {"sdk": version("openjiuwen"), "native_sha256": sha256(native.read_bytes()).hexdigest(),
            "members": members, "missing_verifier_rejected": reason}


if __name__ == "__main__":
    payload, native = (Path(arg).resolve() for arg in sys.argv[1:])
    os.chdir(ASSET / ".local")
    result = check(payload, native)
    (ASSET / "tests/records/host-loader.json").write_text(json.dumps(result, ensure_ascii=False, indent=2) + "\n")
    print(json.dumps(result, ensure_ascii=False))
