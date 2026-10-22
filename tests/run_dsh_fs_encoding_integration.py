#!/usr/bin/env python3
from __future__ import annotations
import asyncio, importlib.util, tempfile
from pathlib import Path

FILE=Path(__file__).parents[1]/"plugins/dsh-fs-encoding/dsh-fs-encoding/tools/fs_encoding.py"
spec=importlib.util.spec_from_file_location("fs_encoding",FILE); assert spec and spec.loader
mod=importlib.util.module_from_spec(spec); spec.loader.exec_module(mod)

def fresh_module(name):
  new_spec=importlib.util.spec_from_file_location(name,FILE); assert new_spec and new_spec.loader
  loaded=importlib.util.module_from_spec(new_spec); new_spec.loader.exec_module(loaded); return loaded

async def main():
  with tempfile.TemporaryDirectory(prefix="fs-encoding-") as raw:
    root=Path(raw); gbk=root/"legacy.txt"; original="配置=开启\r\n名称=测试\r\n".encode("gbk"); gbk.write_bytes(original)
    ambiguous=await mod.EncodingReadTool().invoke({"file_path":str(gbk)}); assert not ambiguous["ok"]
    read=await mod.EncodingReadTool().invoke({"file_path":str(gbk),"encoding":"gbk"}); assert read["ok"] and read["line_ending"]=="CRLF"
    full=await mod.EncodingWriteTool().invoke({"file_path":str(gbk),"content":"配置=开启\n名称=新测试\n","write":True}); assert full["ok"] and b"\r\n" in gbk.read_bytes() and gbk.read_bytes().decode("gbk").startswith("配置=开启")
    await mod.EncodingUndoTool().invoke({"file_path":str(gbk)}); assert gbk.read_bytes()==original
    preview=await mod.EncodingEditTool().invoke({"file_path":str(gbk),"encoding":"gbk","old_string":"开启","new_string":"关闭","write":False}); assert preview["ok"] and gbk.read_bytes()==original
    bad=await mod.EncodingEditTool().invoke({"file_path":str(gbk),"encoding":"gbk","old_string":"开启","new_string":"😀","write":True}); assert not bad["ok"] and gbk.read_bytes()==original
    good=await mod.EncodingEditTool().invoke({"file_path":str(gbk),"encoding":"gbk","old_string":"开启","new_string":"关闭","write":True}); assert good["ok"] and b"\r\n" in gbk.read_bytes()
    grep=await mod.EncodingGrepTool().invoke({"pattern":"关闭","file_paths":[str(gbk)],"encoding":"gbk"}); assert grep["hits"][0]["line"]==1
    undo=await fresh_module("fs_encoding_undo").EncodingUndoTool().invoke({"file_path":str(gbk)}); assert undo["ok"] and gbk.read_bytes()==original
    await mod.EncodingEditTool().invoke({"file_path":str(gbk),"encoding":"gbk","old_string":"开启","new_string":"关闭","write":True})
    gbk.write_bytes(gbk.read_bytes()+b"X")
    stale=await fresh_module("fs_encoding_stale").EncodingUndoTool().invoke({"file_path":str(gbk)}); assert stale["error"]["code"]=="STALE_UNDO" and gbk.read_bytes().endswith(b"X")
    mod._undo_path(gbk).unlink(missing_ok=True)
    bom=root/"bom.txt"; bom.write_bytes(b"\xef\xbb\xbfhello\r\n")
    result=await mod.EncodingWriteTool().invoke({"file_path":str(bom),"content":"changed\n","write":True}); assert result["ok"] and bom.read_bytes().startswith(b"\xef\xbb\xbf") and b"\r\n" in bom.read_bytes()
    utf16=root/"u16.txt"; utf16.write_bytes(b"\xff\xfe"+"hello\r\n".encode("utf-16-le")); check=await mod.EncodingReadTool().invoke({"file_path":str(utf16)}); assert check["encoding"]=="utf-16-le" and check["bom"]
  print("dsh-fs-encoding integration: PASS")
if __name__=="__main__": asyncio.run(main())
