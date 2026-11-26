"""Exercise the extracted local confirmation page and feed its plan into the real CLI."""
import argparse
import base64
from itertools import count
import json
from pathlib import Path
import subprocess
import time
from urllib.request import urlopen

from websockets.sync.client import connect


def wait_until(read, description):
    until = time.monotonic() + 12
    while time.monotonic() < until:
        value = read()
        if value:
            return value
        time.sleep(0.08)
    raise AssertionError(description)


class BrowserSession:
    def __init__(self, socket):
        self.socket, self.sequence = socket, count(1)

    def call(self, method, **params):
        number = next(self.sequence)
        self.socket.send(json.dumps({"id":number,"method":method,"params":params}))
        while True:
            reply=json.loads(self.socket.recv(timeout=8))
            if reply.get("id")==number:
                if "error" in reply:
                    raise RuntimeError(reply["error"])
                return reply.get("result",{})

    def dom(self, js):
        value=self.call("Runtime.evaluate",expression=js,returnByValue=True,awaitPromise=True)
        if "exceptionDetails" in value:
            raise RuntimeError(value["exceptionDetails"]["text"])
        return value["result"].get("value")

    def choose_files(self, selector, files):
        doc=self.call("DOM.getDocument")["root"]["nodeId"]
        node=self.call("DOM.querySelector",nodeId=doc,selector=selector)["nodeId"]
        self.call("DOM.setFileInputFiles",nodeId=node,files=[str(f) for f in files])

    def drag(self, start, end):
        self.dom('document.querySelector("canvas").scrollIntoView({block:"center"})')
        rect=self.dom('(()=>{const c=document.querySelector("canvas"),r=c.getBoundingClientRect();return [r.left,r.top,r.width/c.width,r.height/c.height]})()')
        xa,ya=[rect[i]+p*rect[i+2] for i,p in enumerate(start)]
        xb,yb=[rect[i]+p*rect[i+2] for i,p in enumerate(end)]
        self.call("Input.dispatchMouseEvent",type="mousePressed",x=xa,y=ya,button="left",buttons=1,clickCount=1)
        self.call("Input.dispatchMouseEvent",type="mouseMoved",x=xb,y=yb,buttons=1,button="left")
        self.call("Input.dispatchMouseEvent",type="mouseReleased",x=xb,y=yb,button="left",buttons=0,clickCount=1)


def main():
    parser=argparse.ArgumentParser(description=__doc__)
    for field in ("payload","runtime","tool","record"):
        parser.add_argument("--"+field, required=True,type=Path)
    args=parser.parse_args()
    root=Path(__file__).resolve().parents[1]
    src=root/"tests/fixtures/screenshots"
    args.runtime.mkdir()
    scan=args.runtime/"scan.json"
    subprocess.run([str(args.tool),"scan",str(src),str(scan),"email"],check=True)
    bins="/Applications/Google Chrome.app/Contents/MacOS/Google Chrome"
    flags=["--headless","--disable-gpu","--no-first-run","--disable-background-networking","--disable-component-update",
           "--disable-sync","--no-default-browser-check","--host-resolver-rules=MAP * ~NOTFOUND, EXCLUDE localhost",
           "--window-size=1200,1200","--remote-debugging-port=0",f"--user-data-dir={args.runtime/'profile'}","about:blank"]
    page=(args.payload/"skills/screenshot-review/confirm.html").as_uri()
    with (args.runtime/"chrome.log").open("wb") as log:
        proc=subprocess.Popen([bins,*flags],stdout=log,stderr=subprocess.STDOUT)
        try:
            portfile=args.runtime/"profile/DevToolsActivePort"
            def get_port():
                try:
                    return int(portfile.read_text().splitlines()[0])
                except (OSError,ValueError,IndexError):
                    return None
            port=wait_until(get_port,"isolated Chrome endpoint missing")
            with urlopen(f"http://127.0.0.1:{port}/json/list",timeout=5) as response:
                tab=next(t for t in json.load(response) if t["type"]=="page")
            with connect(tab["webSocketDebuggerUrl"], max_size=10*1024*1024) as socket:
                browser=BrowserSession(socket)
                browser.call("Browser.setDownloadBehavior",behavior="allow",downloadPath=str(args.runtime))
                browser.call("Page.navigate",url=page)
                wait_until(lambda:browser.dom('Boolean(document.getElementById("scan"))'),"confirmation HTML missing")
                browser.choose_files("#scan",[scan])
                wait_until(lambda:browser.dom('!document.getElementById("photos").disabled'),"scan did not load")
                browser.choose_files("#photos",sorted(src.glob("*.png")))
                wait_until(lambda:browser.dom('document.getElementById("status").textContent.includes("已核对 2 张")'),"images failed hash check")
                browser.dom('(()=>{const s=document.getElementById("choice");s.value="image-02";s.dispatchEvent(new Event("change"));return true})()')
                wait_until(lambda:browser.dom('document.querySelector("canvas").width===840 && !document.getElementById("checked").disabled'),"image not ready")
                browser.dom('document.getElementById("mode").value="keep"')
                browser.drag((57,250),(750,315))
                browser.dom('document.getElementById("checked").click()')
                assert browser.dom('document.getElementById("checked").checked')
                browser.call("Runtime.evaluate",expression='document.getElementById("save").click()',userGesture=True)
                wait_until(lambda:(args.runtime/"approval.json").is_file(),"approval download missing")
                capture=browser.call("Page.captureScreenshot",format="png")
                (args.runtime/"confirmation-ui.png").write_bytes(base64.b64decode(capture["data"]))
        finally:
            proc.terminate()
            proc.wait(timeout=8)
    plan=args.runtime/"approval.json"
    approval=json.loads(plan.read_bytes())
    assert [x["disposition"] for x in approval["images"]]==["held","approved"]
    assert approval["images"][1]["masks"] and len(approval["images"][1]["keep"])==1
    candidate,audit,delivery=[args.runtime/n for n in ("candidate","audit.json","delivery")]
    shared=[str(x) for x in (src,scan,plan,candidate)]
    for phase, extras in [("render",[]),("verify",[audit]),("deliver",[audit,delivery])]:
        subprocess.run([str(args.tool),phase,*shared,*map(str,extras)],check=True)
    result=json.loads((delivery/"manifest.json").read_bytes())
    result.update(browser_confirmation_page="passed",source="exact extracted package",held_without_approval=True,
                  actual_protected_box_drawn=True,vision_suggested_mask_applied=True,synthetic_only=True)
    args.record.write_text(json.dumps(result,ensure_ascii=False,indent=2)+"\n",encoding="utf-8")
    print("Browser and native CLI verified one exported PNG and one held screenshot.")


if __name__=="__main__":
    main()
