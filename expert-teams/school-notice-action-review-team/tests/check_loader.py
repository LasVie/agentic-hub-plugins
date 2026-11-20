"""Load the exact native group with the current target WorkSwarm SDK."""
from hashlib import sha256
from importlib.metadata import version
import json
import os
from pathlib import Path
import shutil
import sys
from tempfile import mkdtemp
from host_notices import ASSET, PRIVATE, SHARED


def check(payload, native):
    from openjiuwen.agent_teams.experts import load_agent_group_package_bundle

    bundle = load_agent_group_package_bundle(payload)
    assert set(bundle.templates) == set(PRIVATE)
    roles = {}
    for name,t in bundle.templates.items():
        skills = sorted(Path(s.dir).name for s in t.skills)
        sections = [p.name for p in t.prompt_sections]
        assert skills == sorted([PRIVATE[name],SHARED])
        assert "agent_group_instruction" in sections
        assert ("agent_group_leader_rules" in sections) == (name == "leader")
        roles[name] = {"skills":skills,"prompt_sections":sections}
    scratch = Path(mkdtemp(prefix="missing-verifier-", dir=ASSET/".local"))
    fixture = scratch/payload.name
    shutil.copytree(payload,fixture)
    (fixture/"agents/verifier").rename(scratch/"preserved-verifier")
    try:
        load_agent_group_package_bundle(fixture)
    except ValueError as e:
        reason = str(e).replace(str(fixture),"<fixture>")
    else:
        raise RuntimeError("Missing verifier accepted")
    return {"sdk":version("openjiuwen"),"native_sha256":sha256(native.read_bytes()).hexdigest(),
            "members":roles,"missing_verifier_rejected":reason}


if __name__ == "__main__":
    native_dir,native_zip = (Path(arg).resolve() for arg in sys.argv[1:])
    os.chdir(ASSET/".local")
    result = check(native_dir,native_zip)
    (ASSET/"tests/records/host-loader.json").write_text(json.dumps(result,ensure_ascii=False,indent=2)+"\n")
    print(json.dumps(result,ensure_ascii=False))
