"""Create native host test ZIPs; final marketplace delivery uses asset_release.py."""
import hashlib,json,shutil,sys,zipfile
from pathlib import Path
R=Path(__file__).resolve().parents[1]
slugs=('dsh-vault','dsh-pianist','dsh-simulated-life')
for slug in slugs:
 p=R/'plugins'/slug/slug
 for cache in p.rglob('__pycache__'):shutil.rmtree(cache)
 out=R/'dist'/slug/'1.0.0';out.mkdir(parents=True,exist_ok=True)
 archive=out/(slug+'-1.0.0-workswarm.zip')
 with zipfile.ZipFile(archive,'w',compression=zipfile.ZIP_DEFLATED,compresslevel=9) as z:
  for f in sorted(p.rglob('*')):
   if not f.is_file():continue
   info=zipfile.ZipInfo(f.relative_to(p).as_posix(),date_time=(1980,1,1,0,0,0));info.compress_type=zipfile.ZIP_DEFLATED;info.external_attr=0o100644<<16
   z.writestr(info,f.read_bytes())
 extracted=R/'dist'/'extracted'/slug
 if extracted.exists():shutil.rmtree(extracted)
 extracted.mkdir(parents=True)
 with zipfile.ZipFile(archive) as z:z.extractall(extracted)
 print(json.dumps({'slug':slug,'path':str(archive),'sha256':hashlib.sha256(archive.read_bytes()).hexdigest(),'bytes':archive.stat().st_size}))
