"""Optional dev check: compares jma_tools.decode_png with Pillow on real rainy tiles (Pillow is used only here, never in the package).
Run with the SDK venv python:  python real_tile_check.py <dir containing PIL>   (needs rain somewhere in Japan right now)
"""
import json,urllib.request,io,math,sys,asyncio
sys.path.append(sys.argv[1])
from PIL import Image
import os
sys.path.insert(0, os.environ.get('JAPAN_RAIN_ALERT_PAYLOAD', os.path.join(os.path.dirname(os.path.abspath(__file__)), '..', 'japan-rain-alert')) + '/tools')
import jma_tools as J
def get(u,j=False):
    r=urllib.request.urlopen(urllib.request.Request(u,headers={"User-Agent":"check"}),timeout=20).read(); return json.loads(r) if j else r
nowc=get("https://www.jma.go.jp/bosai/jmatile/data/nowc/targetTimes_N1.json",True)[0]
tpl=f"https://www.jma.go.jp/bosai/jmatile/data/nowc/{nowc['basetime']}/none/{nowc['validtime']}/surf/hrpns/{{z}}/{{x}}/{{y}}.png"
for z,x,y in ((6,56,24),(6,57,24),(6,56,25)):
    b=get(tpl.format(z=z,x=x,y=y)); w,h,rgba=J.decode_png(b); ref=Image.open(io.BytesIO(b)).convert('RGBA')
    print(f'tile z{z}/{x}/{y}: mine==Pillow:',(w,h)==ref.size and rgba==ref.tobytes(), '| non-transparent px:',sum(1 for i in range(3,len(rgba),4) if rgba[i]))
b=get(tpl.format(z=6,x=56,y=24)); im=Image.open(io.BytesIO(b)).convert('RGBA'); n=2**6
for want in ((33,140,255),(160,210,255),(242,242,255)):
    pts=[(px,py) for py in range(256) for px in range(256) if im.getpixel((px,py))[:3]==want and im.getpixel((px,py))[3]>0]
    if not pts: print('no pixel of',want); continue
    px,py=pts[len(pts)//2]; xt=56+(px+.5)/256; yt=24+(py+.5)/256
    lon=xt/n*360-180; lat=math.degrees(math.atan(math.sinh(math.pi*(1-2*yt/n))))
    tx,ty,qx,qy=J.tile_pixel_xy(lat,lon,10); i10=Image.open(io.BytesIO(get(tpl.format(z=10,x=tx,y=ty)))).convert('RGBA')
    cnt={}
    for dx in (-1,0,1):
        for dy in (-1,0,1):
            p=i10.getpixel((min(max(qx+dx,0),255),min(max(qy+dy,0),255)))
            if p[3]>0: cnt[p[:3]]=cnt.get(p[:3],0)+1
    r=asyncio.run(J.call_tool('site_rain_risk',{'place':f'{lat:.5f},{lon:.5f}'}))
    print(f'z6 colour {want} at ({lat:.4f},{lon:.4f}): independent z10 3x3 = {cnt} | tool = {r["data"]["analysis_rainfall"]["rate_zh"] if r["ok"] else r["error"]}')
