"""Read-only checks of the isolated WorkSwarm instance; never sends model requests."""
import argparse
import asyncio
import datetime
import hashlib
import json
import urllib.request
import uuid
from pathlib import Path

from websockets.legacy.client import connect


async def rpc(ws, method, params=None):
    ident = "molecule-check-" + uuid.uuid4().hex
    await ws.send(json.dumps({"type": "req", "id": ident, "method": method, "params": params or {}}))
    while True:
        result = json.loads(await asyncio.wait_for(ws.recv(), 30))
        if result.get("id") == ident:
            return result


def inventory(root):
    return {str(p.relative_to(root)): hashlib.sha256(p.read_bytes()).hexdigest()
            for p in root.rglob("*") if p.is_file() and "__pycache__" not in p.parts and p.suffix != ".pyc"}


async def main(args):
    result = {"checked_at": datetime.datetime.now(datetime.timezone.utc).isoformat(),
              "instance": str(args.instance.resolve()), "model_requests_sent": 0, "websockets": []}
    with urllib.request.urlopen(f"http://127.0.0.1:{args.frontend}/", timeout=10) as response:
        result["frontend"] = {"status": response.status, "html": "<html" in response.read().decode().lower()}
    for port in (args.backend, args.frontend):
        async with connect(f"ws://127.0.0.1:{port}/ws?user_id=molecule-build-health", open_timeout=10) as ws:
            pong = await ws.ping()
            await asyncio.wait_for(pong, 5)
            config = await rpc(ws, "config.get")
            catalog = await rpc(ws, "plugin_packages.list", {"filter": "local"})
            assert config.get("ok") and catalog.get("ok")
            # Never persist config values, tokens, or model credentials.
            result["websockets"].append({"port": port, "ping_pong": True,
                                         "backend_config_ok": True, "extensions_catalog_ok": True})
            result["catalog"] = catalog["payload"]
    config_path = args.instance / "data/config/config.yaml"
    result["host_config_sha256"] = hashlib.sha256(config_path.read_bytes()).hexdigest()
    result["plugin_files"] = inventory(args.instance / "data/agent/workspace/plugins/plugin_packages/local")
    args.output.write_text(json.dumps(result, ensure_ascii=False, indent=2) + "\n")
    print(json.dumps({k: v for k, v in result.items() if k not in ("plugin_files", "catalog")}, indent=2))
    print("Existing plugin files fingerprinted:", len(result["plugin_files"]))


if __name__ == "__main__":
    parser = argparse.ArgumentParser()
    parser.add_argument("--instance", type=Path, required=True)
    parser.add_argument("--frontend", type=int, required=True)
    parser.add_argument("--backend", type=int, required=True)
    parser.add_argument("--output", type=Path, required=True)
    asyncio.run(main(parser.parse_args()))
