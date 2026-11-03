"""Collect actual bundled-input licenses, retain required source, and pack ZIPs."""
import hashlib
import json
import os
from pathlib import Path
import re
import shutil
import subprocess
import sys
import zipfile

REPO=Path(__file__).resolve().parents[2]
BUILD=REPO/'.research/dev-five/build'
DEFS=json.loads((REPO/'tools/dev_five_config.json').read_text())
APPROVED={'MIT','BSD-3-Clause','BSD-2-Clause','ISC','Apache-2.0','BlueOak-1.0.0','0BSD','MPL-2.0'}
def sha(p):return hashlib.sha256(p.read_bytes()).hexdigest()
def write(p,d):p.parent.mkdir(parents=True,exist_ok=True);p.write_text(json.dumps(d,ensure_ascii=False,indent=2)+'\n')
def package_root(p):
    for parent in [p.parent,*p.parents]:
        if (parent/'package.json').is_file():
            metadata=json.loads((parent/'package.json').read_text())
            if metadata.get('name') and metadata.get('version'):return parent
    raise ValueError('Package metadata missing: '+str(p))

for d in DEFS:
    if os.environ.get('DEV_FIVE_ONLY') and d['slug']!=os.environ['DEV_FIVE_ONLY']:continue
    asset_version=d.get('asset_version','1.0.2');outer=REPO/'plugins'/d['slug'];root=outer/d['slug'];evidence=outer/'build-evidence';evidence.mkdir(exist_ok=True)
    if (root/'licenses').exists():shutil.rmtree(root/'licenses')
    (root/'licenses').mkdir()
    packages={};inputs=[]
    metas=list((root/'vendor').rglob('*.inputs.json')) or list(evidence.glob('*.inputs.json'))
    for meta in metas:
        content=json.loads(meta.read_text());inputs.extend(content)
        for name in content:
            if 'node_modules/' not in name:continue
            p=(BUILD/name).resolve();pr=package_root(p);packages[str(pr)]=pr
        if meta.parent != evidence:
            shutil.copyfile(meta,evidence/meta.name);meta.unlink()
    assert not any('codemirror-formatting' in name for name in inputs),'Unreviewed formatting addon must not be distributed'
    assert not any('/sharp/' in name or 'sharp-libvips' in name for name in inputs),'Native image-codec distribution is excluded'
    if d['slug']=='visual-web-studio':packages[str(BUILD/'node_modules/grapesjs')]=BUILD/'node_modules/grapesjs'
    if d['slug']=='postgres-local-lab':packages[str(BUILD/'node_modules/@electric-sql/pglite')]=BUILD/'node_modules/@electric-sql/pglite'
    sources=[];inventory=[]
    for pr in sorted(packages.values()):
        package=json.loads((pr/'package.json').read_text());name=package['name'];version=package['version'];license=package.get('license')
        if license is None and name in {'busboy','streamsearch'} and package.get('licenses')==[{'type':'MIT','url':'http://github.com/mscdex/'+name+'/raw/master/LICENSE'}]:
            license='MIT'  # Actual Brian White MIT texts manually reviewed with the legacy manifest.
        if license not in APPROVED:raise ValueError('Unreviewed license: '+name+' '+str(license))
        slug=name.replace('@','').replace('/','--')+'--'+version;dest=root/'licenses'/slug
        dest.mkdir(parents=True,exist_ok=True)
        files=[p for p in pr.iterdir() if p.is_file() and re.search(r'license|licence|copying|copyright|notice',p.name,re.I)]
        if not files:
            files=[p for p in pr.iterdir() if p.is_file() and p.suffix.lower()=='.md' and 'permission is hereby granted' in p.read_text(errors='replace').lower()]
        if not files:raise ValueError('Full applicable license evidence absent: '+name+' '+version)
        evidence_files=[]
        for i,p in enumerate(files):
            target=dest/('LICENSE' if i==0 else p.name)
            shutil.copyfile(p,target);evidence_files.append({'path':target.relative_to(root).as_posix(),'sha256':sha(target)})
        if name=='@jmespath-community/jmespath':
            source=REPO/'.research/dev-five/@jmespath-community__jmespath-source'
            for p in source.rglob('*'):
                relative=p.relative_to(source)
                if not p.is_file() or (relative.parts[0]!='src' and p.name not in {'LICENSE','package.json','tsconfig.json','tsdown.config.ts','README.md'}):continue
                target=dest/'source'/relative;target.parent.mkdir(parents=True,exist_ok=True);shutil.copyfile(p,target)
            (dest/'SOURCE_AVAILABILITY.md').write_text('MPL-2.0 Source Code Form is supplied in source/. Fixed upstream revision f04b204f5919ad607a4945a23331810b07cc13ae at https://github.com/jmespath-community/typescript-jmespath/tree/f04b204f5919ad607a4945a23331810b07cc13ae . No upstream source edits; bundling is a build transformation. The surrounding plugin is a larger work, not a relicense of this component.\n')
        source={'url':'https://www.npmjs.com/package/'+name+'/v/'+version,'revision':version,'license_expression':license,'license_evidence':evidence_files}
        sources.append(source);inventory.append({'name':name,'version':version,'license':license,'package_sha256':sha(pr/'package.json'),'licenses':evidence_files})
    if d['slug']=='postgres-local-lab':
        target=root/'licenses/postgresql/LICENSE';target.parent.mkdir(exist_ok=True);shutil.copyfile(REPO/'.research/dev-five/POSTGRES-LICENSE',target)
        sources.append({'url':'https://github.com/electric-sql/pglite/blob/0974bdf1ab3b100a1b25ffbcb1a15ff6446db6d4/POSTGRES-LICENSE','revision':'0974bdf1ab3b100a1b25ffbcb1a15ff6446db6d4','license_expression':'PostgreSQL','license_evidence':[{'path':target.relative_to(root).as_posix(),'sha256':sha(target)}]})
    write(root/'licenses/COMPONENTS.json',inventory)
    notices=['# 第三方来源与许可\n','本包保留以下实际运行组件的完整许可与版权声明。仅组合、打包和接入中文工作台；不暗示上游作者背书。\n','构建输入与锁定版本见外层build-evidence；完整许可保存在本包licenses/。\n']
    notices.extend('- '+x['name']+'@'+x['version']+' — '+x['license']+'；'+x['licenses'][0]['path'] for x in inventory)
    if d['slug']=='api-mock-lab':notices.append('\nJMESPath采用MPL-2.0；对应可修改源码随licenses/jmespath-community--jmespath--1.4.1/source提供，许可保持MPL-2.0。未修改其源文件，打包转译不改变原许可。')
    if d['slug']=='visual-web-studio':notices.append('\nGrapesJS源码固定3b2c671c0ab50f052a219b987dea8738ea75886e；构建时排除codemirror-formatting附加件，以独立空模块替代；代码格式化功能不提供。中文界面与保存/导出为本项目新增；核心样式与中文语言文件保持原文。')
    if d['slug']=='postgres-local-lab':notices.append('\nPostgreSQL版权与许可见licenses/postgresql/LICENSE。PGlite已发布的WASM、数据及JS运行文件保持原字节，不包含另行分发的可选扩展归档。')
    if d['slug']=='bundle-insight':notices.append('\n使用官方统计采集插件与Rollup WASM进行真实构建；本项目独立实现中文交互图和对比界面，不分发上游预编译图表客户端。未包含可选fsevents监听器；不提供watch模式。')
    if d['slug']=='web3d-asset-lab':notices.append('\n仅采用glTF Transform的有界模型操作；原生Sharp/libvips及其LGPL二进制不打包。未提供的原生图像I/O入口替换为显式报错模块。彩色贴图缩放由独立浏览器Canvas与SDK实现，属于用户主动选择的有损分辨率调整。演示模型由本插件自行构造，不搬运第三方模型。')
    (root/'THIRD_PARTY_NOTICES.md').write_text('\n'.join(notices)+'\n',encoding='utf-8')
    write(outer/'provenance.json',{'mode':'ported','permission_status':'verified','sources':sources,'reused_paths':[p.relative_to(root).as_posix() for p in sorted((root/'vendor').rglob('*')) if p.is_file()],'audit_file':'SOURCE_REVIEW.md'})
    shutil.copyfile(BUILD/'package-lock.json',evidence/'npm-build.lock.json')
    write(evidence/'bundled-inputs.json',{'inputs':inputs,'formatter_excluded':not any('codemirror-formatting' in p for p in inputs),'native_image_codecs_excluded':not any('/sharp/' in p or 'sharp-libvips' in p for p in inputs)})
    review=f'''# Source and distribution review: {d['slug']}

Reviewed 2026-11-02. {d['upstream']} -> {d['name']} -> {d['slug']}. Task AH-20261102-{d['slug']}; Candidate {d['candidate_id']}; owner Song Haoran.

Mode: ported; permission_status: verified for the actual supplied components, not a repository-wide relicensing decision. Primary source: https://github.com/{d['repository']} . Exact npm packages are locked in build-evidence/npm-build.lock.json including registry integrity hashes. Each actual bundled input was mapped to its owning package; full copyright/license/notice texts were copied and hashed in the payload licenses/COMPONENTS.json and provenance.json. Source-owned adapters, Chinese UI, persistence, host integration and tests are new project work; upstream packages and compiled assets remain under their respective licenses.

## Actual reuse and exclusions
{chr(10).join(notices[-2:])}

{('For the MPL component, the full Source Code Form, original license, fixed revision and availability instructions are distributed together.' if d['slug']=='api-mock-lab' else 'This asset does not bundle the MPL component used by the mock workbench.')} No unreviewed native Sharp/libvips binaries or old formatting-addon implementation are distributed. Optional platform-specific watchers and development caches are excluded. Runtime engines come from the official npm registry; no external model, cloud account or paid service is required by these bounded workflows. No separately sourced media or sample 3D models were added beyond licensed runtime-package assets.

## Functional boundary and de-duplication
The selected scope was compared against the existing tracker before registration. This plugin adds a real, callable engine plus a persistent local workbench. Generic coding/browser tools remain capable of running user commands; this is a ready application capability, not a claim that the host could never implement it. The exact input/output limitations are in the Chinese README and Skill. No host, SDK, shared dependencies or other plugins are modified.

## Gate
Source/distribution evidence is collected; actual final ZIP extraction, runtime tests, WorkSwarm installation, agent-delegated host invocation and original screenshots are separate verification steps recorded in TEST_REPORT.md. Do not treat this audit alone as a functional-test pass.
'''
    (outer/'SOURCE_REVIEW.md').write_text(review)
    for cache in root.rglob('__pycache__'):shutil.rmtree(cache)
    subprocess.run([sys.executable,'tools/asset_release.py','check',str(outer)],cwd=REPO,check=True)
    subprocess.run([sys.executable,'tools/asset_release.py','pack',str(outer)],cwd=REPO,check=True)
    native=outer/'test-packages'/(d['slug']+'-'+asset_version+'-workswarm.zip');native.parent.mkdir(exist_ok=True)
    with zipfile.ZipFile(native,'w',zipfile.ZIP_DEFLATED,compresslevel=9) as z:
        for p in sorted(root.rglob('*')):
            if p.is_file():
                info=zipfile.ZipInfo(d['slug']+'/'+p.relative_to(root).as_posix(),date_time=(2026,11,2,0,0,0));info.compress_type=zipfile.ZIP_DEFLATED;info.external_attr=0o100644<<16;z.writestr(info,p.read_bytes())
    release=REPO/'releases/agent-plugin'/d['slug']/asset_version/(d['slug']+'-'+asset_version+'.zip')
    with zipfile.ZipFile(native) as z:native_files={n[len(d['slug'])+1:]:hashlib.sha256(z.read(n)).hexdigest() for n in z.namelist() if not n.endswith('/')}
    prefix=d['slug']+'/'+d['slug']+'/'
    with zipfile.ZipFile(release) as z:canonical_files={n[len(prefix):]:hashlib.sha256(z.read(n)).hexdigest() for n in z.namelist() if n.startswith(prefix) and not n.endswith('/')}
    assert native_files==canonical_files,'Native/canonical runtime files differ'
    write(outer/'package-verification.json',{'version':asset_version,'canonical_sha256':sha(release),'native_sha256':sha(native),'payload_files':len(native_files),'runtime_payloads_equal':native_files==canonical_files,'payload_sha256':native_files})
    print(d['slug'],sha(release),sha(native),len(inventory),'licensed packages')
