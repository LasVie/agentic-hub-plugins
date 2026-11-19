"""Supported management import/readback only; never starts a model conversation."""
from __future__ import annotations
import argparse
import asyncio
import hashlib
import json
from pathlib import Path
import uuid
import zipfile

SLUG = "robot-route-review-team"


async def rpc(url, method, params):
    import websockets
    async with websockets.connect(url.replace("http", "ws") + "/ws", origin=url, max_size=16 * 1024 * 1024) as ws:
        await asyncio.wait_for(ws.recv(), 15)
        identifier = "route-management-" + uuid.uuid4().hex
        await ws.send(json.dumps({"type": "req", "id": identifier, "method": method, "params": params}))
        while True:
            r = json.loads(await asyncio.wait_for(ws.recv(), 30))
            if r.get("id") == identifier:
                if r.get("error") or r.get("ok") is False: raise RuntimeError(str(r))
                return r.get("payload", {})


def files(root):
    return {p.relative_to(root).as_posix(): hashlib.sha256(p.read_bytes()).hexdigest()
            for p in root.rglob("*") if p.is_file()}


async def main(args):
    if args.url != "http://127.0.0.1:6411": raise ValueError("This handoff targets the existing isolated 6411 instance only")
    roots = [args.data_root / "domain/.agent_teams/agent_groups/local", args.data_root / ".agent_teams/agent_groups/local"]
    existing_targets = {p.resolve() for p in roots if (p / SLUG).is_dir()}
    if len(existing_targets) > 1: raise RuntimeError("Ambiguous installed group location; inspect actual host configuration")
    group_root = next(iter(existing_targets), next((p for p in roots if p.is_dir()), None))
    if group_root is None: raise RuntimeError("Known instance group directory not found; do not guess another instance")
    old = {p.name: files(p) for p in group_root.iterdir() if p.is_dir() and p.name != SLUG}
    before = await rpc(args.url, "agent_groups.list", {"filter": "mine"})
    target = group_root / SLUG
    if target.exists():
        if not args.reuse: raise RuntimeError("Existing identity: no overwrite/uninstall permitted; inspect before explicit reuse")
    else:
        if not args.install: raise RuntimeError("No installed group; explicit --install required")
        imported = await rpc(args.url, "agent_groups.import_local", {"path": str(args.native.resolve())})
        if imported.get("id") != SLUG: raise RuntimeError("Unexpected native identity/type")
        await rpc(args.url, "agent_groups.install", {"id": SLUG})
    show = await rpc(args.url, "agent_groups.show", {"id": SLUG})
    group = show["group"]
    if group.get("version") != "1.0.0" or group.get("leaderId") != "leader" or {m["id"] for m in group["members"]} != {"leader", "map-analyst", "planner", "verifier"}:
        raise RuntimeError("Wrong actual AgentGroup roster/version")
    with zipfile.ZipFile(args.native) as z:
        expected = {n: hashlib.sha256(z.read(n)).hexdigest() for n in z.namelist() if not n.endswith("/")}
    if files(target) != expected: raise RuntimeError("Actual installation differs from the exact native ZIP")
    for name, hashes in old.items():
        if files(group_root / name) != hashes: raise RuntimeError("Unrelated installed group changed: " + name)
    after = await rpc(args.url, "agent_groups.list", {"filter": "mine"})
    result = {"url": args.url + "/", "version": "1.0.0", "group": SLUG,
              "native_sha256": hashlib.sha256(args.native.read_bytes()).hexdigest(), "members": [m["id"] for m in group["members"]],
              "installed_root": str(target), "payload_sha256": expected, "installed_equal": True,
              "preserved_other_groups": sorted(old), "management_list_before": before, "management_list_after": after,
              "gui_upload": "Automation file chooser unavailable; pending manual selection", "model_calls": 0,
              "human_testing_passed": False}
    args.record.parent.mkdir(parents=True, exist_ok=True)
    with args.record.open("x", encoding="utf-8") as f: json.dump(result, f, ensure_ascii=False, indent=2); f.write("\n")
    print(json.dumps({k:v for k,v in result.items() if k not in {"payload_sha256", "management_list_before", "management_list_after"}}, ensure_ascii=False))


if __name__ == "__main__":
    p=argparse.ArgumentParser(description=__doc__)
    p.add_argument("--url", default="http://127.0.0.1:6411")
    for name in ("native", "data-root", "record"): p.add_argument("--"+name,type=Path,required=True)
    p.add_argument("--install",action="store_true");p.add_argument("--reuse",action="store_true")
    asyncio.run(main(p.parse_args()))
