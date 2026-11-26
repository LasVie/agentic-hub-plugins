"""Build declarative standard-MCP source; this development script is not shipped."""
import json
from pathlib import Path

root=Path(__file__).resolve().parents[1]
payload=root/'asana'
source=(root/'tests/standard-mcp.cjs').read_text()
entry=source.split('module.exports=')[0]+'start();\n'
config={'mcpServers':{'asana':{'command':'node','args':['-e',entry],
    'env':{'ASANA_PERSONAL_TOKEN':'${ASANA_PERSONAL_TOKEN}'},'timeout_s':45}}}
(payload/'mcp.json').write_text(json.dumps(config,ensure_ascii=False,indent=2)+'\n')
manifest=json.loads((payload/'manifest.json').read_text())
manifest.update(version='1.1.0',integration={'type':'stdio-mcp','file':'mcp.json'})
(payload/'manifest.json').write_text(json.dumps(manifest,ensure_ascii=False,indent=2)+'\n')
asset=json.loads((root/'asset.json').read_text())
asset['version']='1.1.0'
(root/'asset.json').write_text(json.dumps(asset,ensure_ascii=False,indent=2)+'\n')
for name in ('connector.py','http_client.py'):(payload/name).unlink(missing_ok=True)
print('Prepared Asana1.1.0 standard MCP source without a Python runtime or external npm dependency.')
