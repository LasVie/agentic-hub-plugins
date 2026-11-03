"""Generate the five independent, native WorkSwarm plugin payloads."""
import json
from pathlib import Path
import shutil

REPO=Path(__file__).resolve().parents[2]
SOURCE=Path(__file__).resolve().parent
DEFS=json.loads((REPO/'tools/dev_five_config.json').read_text())

CONTENT={
'api-mock-lab':('mock', '''<p class="intro">把接口定义变成真正可访问的本地HTTP服务。前端可以直接连接这里的地址，验证成功、异常和慢响应。</p>
<div class="grid"><section><h2>接口定义</h2><div class="toolbar"><button id="demo">载入商品示例</button><button id="save">保存定义</button><button id="export">导出定义</button></div><label for="definition">接口JSON</label><textarea id="definition" rows="14" placeholder="请先载入示例，或粘贴接口定义"></textarea><div class="toolbar"><label>响应场景 <select id="scenario"><option value="normal">正常响应</option><option value="slow">慢响应 · 350ms</option><option value="error">服务异常 · 503</option></select></label><button id="start" class="primary">启动接口服务</button><button id="stop" class="danger">停止服务</button></div><p>运行地址：<strong id="mock-url">未启动</strong>　接口数：<span id="route-count">—</span></p></section>
<section><h2>真实请求验证</h2><div class="toolbar"><select id="method" aria-label="请求方法"><option>GET</option><option>POST</option><option>PUT</option><option>DELETE</option></select><input id="request-path" aria-label="请求路径" value="/api/products"><button id="probe" class="primary">发送真实请求</button></div><div id="metrics" class="metrics"></div><pre id="response">接口服务启动后，在此查看实际HTTP响应。</pre><h3>本轮请求记录</h3><div id="history" class="results"></div></section>
<section class="wide"><h2>导入接口规范</h2><p class="muted">首版支持 Swagger 2.0 / OpenAPI 3.0，提取各接口的首个响应；外部引用、代理、动态模板、回调和文件响应不会执行。模拟结果不能证明真实后端通过。</p><textarea id="openapi" rows="4" placeholder="粘贴JSON或YAML规范"></textarea><div class="toolbar"><button id="import-api">导入规范</button></div></section></div>'''),
'visual-web-studio':('site', '''<p class="intro">用真实的可视化编辑器制作静态网页。双击修改文字，选中区块调整样式；工程JSON保留可继续编辑的组件结构。</p><section><div class="toolbar"><button id="sample" class="primary">载入示例页面</button><button id="add-card">添加功能卡片</button><label>预览设备 <select id="device"><option>桌面</option><option>手机</option></select></label><button id="save" class="primary">保存工程</button><button id="load">重新载入</button><button id="export-html">导出HTML</button><button id="export-json">导出工程</button></div><div class="toolbar"><label>示例主标题 <input id="new-title" value="让每个想法都有自己的页面"></label><button id="apply-title">应用标题</button></div><div id="editor"></div><p class="muted">最后保存：<span id="saved">尚未保存</span>。首版面向静态HTML/CSS模板；不承诺任意React应用的双向还原，不自动发布网站。未集成来源缺少完整许可证据的旧代码格式化附加件。</p></section>'''),
'postgres-local-lab':('pg', '''<p class="intro">真实的PostgreSQL WASM引擎，数据保存在当前插件专用目录。每个项目独立；无需Docker、云数据库账户或数据库服务器。</p><section><div class="toolbar"><label>数据库项目 <input id="project" value="demo" maxlength="48"></label><button id="sample">载入商品示例</button><button id="schema">查看数据表</button><button id="export">导出数据库快照</button></div><label for="sql">SQL语句</label><textarea id="sql" rows="6">SELECT id, name, price, metadata->>'stock' AS stock FROM demo_products ORDER BY price DESC;</textarea><div class="toolbar"><button id="run" class="primary">执行SQL</button><span class="muted">仅操作当前项目；写入语句会真实修改该项目的数据。</span></div></section><div id="metrics" class="metrics"></div><div class="grid"><section><h2>实际查询结果</h2><div id="rows" class="results"><p class="empty">载入示例或执行查询后显示结果</p></div></section><section><h2>字段与执行信息</h2><pre id="details">暂无执行记录</pre></section></div><p class="muted">每次操作有15秒子进程时限；界面最多显示300行。首版不模拟生产并发、复制或任意PostgreSQL扩展。</p>'''),
'bundle-insight':('bundle', '''<p class="intro">读取实际构建统计，定位模块体积与引入关系。可在独立示例上完成真实Rollup构建，也可导入你的Vite/Rollup Visualizer raw-data文件。</p><section><div class="toolbar"><label>快照名称 <input id="name" value="baseline" maxlength="48"></label><label><input id="large" type="checkbox">扩大示例数据</label><button id="build" class="primary">真实构建示例</button><button id="export">导出交互报告</button></div><div class="toolbar"><input id="stats-file" type="file" accept=".json" aria-label="构建统计文件"><button id="import">导入构建统计</button><span class="muted">示例仅用于演示引擎，不代表你的项目已构建。</span></div></section><div id="metrics" class="metrics"></div><div class="grid"><section class="wide"><h2>交互式模块体积图</h2><iframe id="graph" class="preview" title="构建模块交互图"></iframe></section><section><h2>模块明细</h2><div id="modules" class="results"></div></section><section><h2>快照比较</h2><div class="toolbar"><label>之前 <select id="before"></select></label><label>之后 <select id="after"></select></label><button id="load">载入快照</button><button id="compare">比较变化</button></div><div id="changes" class="results"></div></section></div><p class="muted">首版不执行用户项目的配置脚本；接入现有项目请按README生成raw-data统计。压缩统计是逐模块估计，不等同于HTTP传输字节。</p>'''),
'web3d-asset-lab':('gltf', '''<p class="intro">处理已有网页GLB资产，通过真实glTF Transform引擎去重、焊接和清理资源。两侧模型均可用鼠标旋转、缩放。</p><section><div class="toolbar"><button id="demo">载入演示模型</button><input id="model-file" type="file" accept=".glb" aria-label="GLB模型文件"><button id="import">导入本地GLB</button><button id="optimize" class="primary">执行模型优化</button><button id="resize-textures">缩小彩色贴图 · 有损</button><button id="load">恢复已保存模型</button><button id="export">导出优化GLB</button><button id="export-report">导出报告</button></div></section><div id="metrics" class="metrics"></div><div class="grid"><section><h2>优化前 · 原始文件</h2><div id="before-view" class="model-view"></div></section><section><h2>优化后 · 实际成品</h2><div id="after-view" class="model-view"></div></section><section class="wide"><h2>引擎结果</h2><pre id="report">载入模型后查看资源数量与实际字节。</pre></section></div><p class="muted">首版仅支持25 MiB以内、资源完全内嵌的标准GLB；不加载外部资源，不处理必须依赖额外解码器的扩展。保存原始文件；不承诺固定压缩率或任意模型完全无损。</p>''')}

def dump(path,data):
    path.parent.mkdir(parents=True,exist_ok=True)
    path.write_text(json.dumps(data,ensure_ascii=False,indent=2)+'\n',encoding='utf-8')

for d in DEFS:
    slug=d['slug'];version=d.get('asset_version','1.0.2');outer=REPO/'plugins'/slug;root=outer/slug
    for folder in ['runtime','tools','web','skills/'+slug,'licenses']:(root/folder).mkdir(parents=True,exist_ok=True)
    for source,dest in [('launcher.py','runtime/launcher.py'),('service.cjs','runtime/service.cjs'),('common.js','web/common.js'),('style.css','web/style.css')]:shutil.copyfile(SOURCE/source,root/dest)
    kind,body=CONTENT[slug]
    shutil.copyfile(SOURCE/(kind+'-handler.cjs'),root/'runtime/handler.cjs')
    shutil.copyfile(SOURCE/(kind+'-app.js'),root/'web/app.js')
    if kind=='pg':shutil.copyfile(SOURCE/'pg-worker.cjs',root/'runtime/pg-worker.cjs')
    config={**d,'version':version,'upstream_version':d['version']}
    dump(root/'runtime/config.json',config)
    extra='<link rel="stylesheet" href="/vendor/grapes.css">' if kind=='site' else ''
    script='<script type="module">import grapesjs from "/vendor/grapes.mjs"; window.grapesjs=grapesjs; await import("/web/app.js");</script>' if kind=='site' else '<script type="module" src="/web/app.js"></script>'
    (root/'web/index.html').write_text(f'<!doctype html><html lang="zh-CN"><head><meta charset="utf-8"><meta name="viewport" content="width=device-width,initial-scale=1"><title>{d["name"]}</title><link rel="stylesheet" href="/web/style.css">{extra}</head><body><header><div><div class="eyebrow">本地开发工具 · 真实引擎</div><h1 id="title">{d["name"]}</h1></div><span class="pill" id="version">v{version}</span></header><main class="layout"><div id="message" class="notice" hidden></div>{body}<p class="footer">专用工作目录：<span id="workspace" class="filename"></span> · 数据仅保存在本机</p></main>{script}</body></html>',encoding='utf-8')
    native_id=slug.replace('-','_')
    tools=f'''"""{d['name']}的两个原生WorkSwarm工具。"""
import importlib.util
from pathlib import Path
import sys
from openjiuwen.core.foundation.tool import Tool, ToolCard
spec=importlib.util.spec_from_file_location("{native_id}_runtime",Path(__file__).resolve().parents[1]/"runtime/launcher.py")
runtime=importlib.util.module_from_spec(spec);sys.modules[spec.name]=runtime;spec.loader.exec_module(runtime)
COMMON={{"workspace":{{"type":"string","description":"用户选择的已存在专用工作目录绝对路径；插件只在其.{slug}子目录保存数据。"}},"confirmed":{{"type":"boolean","description":"用户明确授权启动、关闭、执行或写入后设为true。"}}}}
class WorkbenchTool(Tool):
 def __init__(self):
  super().__init__(ToolCard(id="{native_id}_workbench",name="{native_id}_workbench",description="为{d['name']}启动、查询或关闭专用本机中文工作台。返回真实访问地址；不修改宿主或其他插件。",input_params={{"type":"object","required":["workspace","action"],"additionalProperties":False,"properties":{{**COMMON,"action":{{"type":"string","enum":["start","status","stop"]}}}}}}))
 async def invoke(self,inputs,**kwargs):return await runtime.invoke(inputs)
 async def stream(self,inputs,**kwargs):yield await self.invoke(inputs,**kwargs)
class EngineTool(Tool):
 def __init__(self):
  super().__init__(ToolCard(id="{native_id}_operate",name="{native_id}_operate",description="调用{d['name']}的真实引擎操作。工作台需先启动。operation和arguments见本插件Skill；依据实际ok/result答复，不能猜测执行结果。",input_params={{"type":"object","required":["workspace","operation","arguments","confirmed"],"additionalProperties":False,"properties":{{**COMMON,"operation":{{"type":"string","description":"本插件Skill列出的操作名称"}},"arguments":{{"type":"object","description":"操作参数对象；不得传入不受支持的宿主命令"}}}}}}))
 async def invoke(self,inputs,**kwargs):return runtime.compact_result(await runtime.invoke({{"workspace":inputs.get("workspace"),"confirmed":inputs.get("confirmed"),"action":"operate","params":{{**inputs.get("arguments",{{}}),"op":inputs.get("operation")}}}}))
 async def stream(self,inputs,**kwargs):yield await self.invoke(inputs,**kwargs)
'''
    (root/'tools/workbench_tools.py').write_text(tools,encoding='utf-8')
    dump(root/'manifest.json',{'id':slug,'version':version,'package_type':'plugin','name':d['name'],'description':d['name']+'：提供独立本机工作台、真实引擎执行和可保存导出的成果。','display_name':{'zh':d['name'],'en':d['name']},'display_description':{'zh':d['name']+'，通过原生工具打开和执行操作。','en':d['name']+'，通过原生工具打开和执行操作。'},'category':'Engineering','source':'local','tags':[{'zh':'开发工具','en':'开发工具'},{'zh':'本地工作台','en':'本地工作台'}],'default_init_input':{'zh':'请打开'+d['name']+'，先确认当前任务的专用工作目录，然后调用插件原生工具启动。','en':'请打开'+d['name']+'，先确认当前任务的专用工作目录，然后调用插件原生工具启动。'},'skills':[{'dir':'skills/'+slug,'mode':'all'}],'tools':[{'file':'tools/workbench_tools.py','class':'WorkbenchTool','display_name':{'zh':'工作台控制','en':'工作台控制'},'display_description':{'zh':'打开、查询或关闭当前插件的中文本机工作台','en':'打开、查询或关闭当前插件的中文本机工作台'}},{'file':'tools/workbench_tools.py','class':'EngineTool','display_name':{'zh':'真实引擎操作','en':'真实引擎操作'},'display_description':{'zh':'执行当前插件的真实引擎操作并返回实际结果','en':'执行当前插件的真实引擎操作并返回实际结果'}}]})
    dump(outer/'asset.json',{'type':'agent-plugin','name':slug,'version':version,'display_name':d['name'],'description':d['name']+'：中文本地工作台与真实引擎工具，保存、恢复并导出实际成果。','publisher':'Song Haoran','category':'软件开发','tags':['开发工具','本地运行'],'functional_tags':['Software Development','Local Interactive Workbench'],'scope':'macOS，宿主SDK、Node.js22+和支持WebGL的桌面浏览器；运行数据在专用工作目录。其他平台未经本轮验证。','candidate_id':d['candidate_id'],'task_id':'AH-20261102-'+slug})
    operations={
    'mock':'demo {}；save {spec:{name,routes:[{method:"get",path:"/api/products",status:200,body:{...}}]}}；start {scenario:"normal"|"slow"|"error"}；probe {method:"GET",path:"/api/products"}；stop {}；import-openapi {source:"规范文本"}。响应模板/文件/代理/回调禁用。',
    'site':'load {}；save {project:GrapesJS工程JSON,html:"实际页面HTML",css:"实际CSS"}。通常先打开工作台让用户在可视化画布编辑，调用load可核对真实保存内容；不要伪造工程树。',
    'pg':'sample {project:"demo"}；query {project:"demo",sql:"SELECT * FROM demo_products"}；schema {project:"demo"}；export {project:"demo"}。query会真实执行写入；只使用授权的独立数据库。',
    'bundle':'build-demo {name:"baseline",large:false}；import {name:"build1",data:真实raw-data JSON}；load {name:"build1"}；compare {before:"baseline",after:"build1"}。示例构建不代表用户项目已测试。',
    'gltf':'demo {}；import {data:完整GLB的base64}；optimize {}；load {}。只处理本机内嵌资源GLB；压缩率、几何数量等必须读取实际返回结果。'}[kind]
    (root/'skills'/slug/'SKILL.md').write_text(f'''---
name: {slug}
description: 使用{d['name']}的真实原生工具和本机中文工作台，保存、恢复并导出实际成果。
---
# {d['name']}
默认使用简体中文。此插件包含真实运行代码，不可用生成的示例文字代替执行。
1. 使用用户授权的已存在专用目录；缺失时先确定目录，禁止使用敏感配置或其他人的工作目录。
2. 调用 `{native_id}_workbench`，action=start、workspace为绝对路径；用户明确要求打开即为本次启动授权，设置confirmed=true。返回ok=true后给出实际url。
3. 用 `{native_id}_operate`，传workspace、confirmed、operation、arguments，读取实际结果；失败时如实说明，不得写“已通过”。
4. 操作：{operations}
5. 交互界面、保存数据与工具共享同一专用目录。重新对话时先status，再load；服务记录属于另一安装时不得接管，换用新目录。
6. 不修改宿主、SDK、其他插件或用户全局依赖。不自动上传云端，不自动发布站点，不调用外部模型。关闭仅调用本插件workbench的stop。
''',encoding='utf-8')
    (root/'README.md').write_text(f'''# {d['name']} {version}

上游：{d['upstream']} → {d['name']} → `{slug}`。

## 安装与打开
在WorkSwarm「扩展」导入本插件原生伴随ZIP并安装；Hub格式ZIP位于仓库releases目录。两种包装的内层运行文件完全一致。
在新任务中选择本插件，指定一个已存在的专用工作目录，要求“打开{d['name']}”。原生工具返回本机链接；在浏览器操作中文工作台。

需要宿主SDK与Node.js22+。macOS优先使用PATH中的Node，或WorkSwarm应用自带Node；可用JIUWEN_NODE_BINARY指定已有可执行文件。不自动安装或修改系统依赖。

## 真实操作
{operations}

## 保存与边界
数据仅保存到用户选择目录下的`.{slug}`。使用界面的保存/导出操作获取真实文件；不要把聊天中的说明当作执行证据。关闭后数据保留，可由同一安装重新打开。保存记录不兼容另一安装目录时应使用新工作目录。

本轮验证以实际TEST_REPORT为准。首版支持范围见中文界面；不承诺未测试的平台、格式或扩展。此插件不执行Agentic Hub发布。

## 许可
完整第三方许可、固定来源、组件范围见`THIRD_PARTY_NOTICES.md`和`licenses/`；原作者声明保留原文。
''',encoding='utf-8')
    if kind=='bundle':
        with (root/'README.md').open('a',encoding='utf-8') as f:
            f.write('''
## 接入已有 Vite / Rollup 项目
在你自己的项目分支中安装统计插件，保留已有配置，并将以下统计插件加到 plugins 数组末尾。工作台不会替你执行项目配置。

```sh
npm install --save-dev rollup-plugin-visualizer@7.1.1
```

```js
import { visualizer } from 'rollup-plugin-visualizer';
// 在已有 Vite / Rollup 的 plugins 数组末尾添加：
visualizer({ filename: 'bundle-stats.json', template: 'raw-data', gzipSize: true, brotliSize: true })
```

使用项目原有构建命令生成 bundle-stats.json，再在本工作台选择该文件，填写快照名并点击“导入构建统计”。构建前后分别导入不同快照名，比较同一统计口径的变化。支持 Visualizer 7.1.1 生成的含 tree、nodeParts、nodeMetas 的 raw-data，最多10 MiB、5000个模块。统计可包含项目模块路径，导入前按团队要求处理敏感路径。
''')
    print('Generated',slug)
