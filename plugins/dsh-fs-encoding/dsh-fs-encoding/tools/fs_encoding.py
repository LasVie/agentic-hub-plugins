"""WorkSwarm port of MIT-licensed dsh-fs-encoding 1.5.2.

Copyright (c) 2026 dsh-fs-encoding contributors. Modified to expose explicit
Python/OpenJiuwen tools; see ../licenses/dsh-fs-encoding/LICENSE.
"""
# 中文化修改：2026-10-22，翻译工具说明和可读提示；保留参数、错误码及文件处理算法。
from __future__ import annotations

import hashlib
import base64
import json
import os
import re
import tempfile
from pathlib import Path
from typing import Any, AsyncIterator, Dict

from openjiuwen.core.foundation.tool import Tool, ToolCard

ALIASES = {
    "utf8": "utf-8", "utf8bom": "utf-8-sig", "utf16le": "utf-16-le",
    "utf16be": "utf-16-be", "utf32le": "utf-32-le", "utf32be": "utf-32-be",
    "gbk": "gbk", "cp936": "gbk", "big5": "big5", "shiftjis": "shift_jis",
    "sjis": "shift_jis", "euckr": "euc_kr", **{f"windows125{i}": f"cp125{i}" for i in range(9)},
}
BOMS = [(b"\x00\x00\xfe\xff", "utf-32-be"), (b"\xff\xfe\x00\x00", "utf-32-le"),
        (b"\xef\xbb\xbf", "utf-8-sig"), (b"\xfe\xff", "utf-16-be"), (b"\xff\xfe", "utf-16-le")]
_KNOWN: dict[str, str] = {}
_UNDO_DIR = Path(tempfile.gettempdir()) / "workswarm-dsh-fs-encoding-undo"


def _undo_path(path: Path) -> Path:
    return _UNDO_DIR / f"{hashlib.sha256(str(path).encode()).hexdigest()}.json"


def _save_undo(path: Path, before: bytes, after: bytes) -> None:
    _UNDO_DIR.mkdir(mode=0o700, parents=True, exist_ok=True)
    os.chmod(_UNDO_DIR, 0o700)
    record = {"path": str(path), "before": base64.b64encode(before).decode("ascii"), "after_sha256": _digest(after)}
    target = _undo_path(path)
    temporary = target.with_suffix(".tmp")
    temporary.write_text(json.dumps(record, separators=(",", ":")), encoding="utf-8")
    os.chmod(temporary, 0o600)
    temporary.replace(target)


def _encoding(raw: str) -> str:
    key = re.sub(r"[^a-z0-9]", "", raw.lower())
    if key not in ALIASES:
        raise ValueError("不支持该编码；请使用 utf8/utf8bom、utf16le/be、utf32le/be、gbk、big5、shift_jis、euc_kr 或 windows-1250..1258")
    return ALIASES[key]


def _decode(data: bytes, hint: str | None) -> tuple[str, str, bytes]:
    if hint:
        enc = _encoding(hint)
        bom = next((mark for mark, name in BOMS if name == enc and data.startswith(mark)), b"")
        payload = data[len(bom):] if bom and enc != "utf-8-sig" else data
        return payload.decode(enc, "strict"), enc, bom
    for mark, enc in BOMS:
        if data.startswith(mark):
            payload = data if enc == "utf-8-sig" else data[len(mark):]
            return payload.decode(enc, "strict"), enc, mark
    try:
        return data.decode("utf-8", "strict"), "utf-8", b""
    except UnicodeDecodeError as exc:
        raise ValueError("文件编码不明确；请指定 encoding 后重试") from exc


def _line_ending(text: str) -> str:
    counts = {"\r\n": text.count("\r\n"), "\n": text.count("\n") - text.count("\r\n"), "\r": text.count("\r") - text.count("\r\n")}
    return max(counts, key=counts.get) if any(counts.values()) else "\n"


def _encode(text: str, enc: str, bom: bytes, ending: str) -> bytes:
    normalized = text.replace("\r\n", "\n").replace("\r", "\n").replace("\n", ending)
    codec = "utf-8" if enc == "utf-8-sig" else enc
    payload = normalized.encode(codec, "strict")
    return bom + payload


def _load(path: Path, hint: str | None = None) -> tuple[bytes, str, str, bytes, str]:
    data = path.read_bytes()
    text, enc, bom = _decode(data, hint)
    return data, text, enc, bom, _line_ending(text)


def _digest(data: bytes) -> str:
    return hashlib.sha256(data).hexdigest()


def _error(code: str, message: str) -> Dict[str, Any]:
    return {"ok": False, "error": {"code": code, "message": message}}


class EncodingReadTool(Tool):
    def __init__(self) -> None:
        super().__init__(ToolCard(id="encoding_read", name="encoding_read", description="安全读取旧编码文本文件。", input_params={"type":"object","properties":{"file_path":{"type":"string"},"encoding":{"type":"string"},"offset":{"type":"integer","minimum":1,"default":1},"limit":{"type":"integer","minimum":1,"default":200}},"required":["file_path"]}, idempotent=True))
    async def invoke(self, inputs: Dict[str, Any], **kwargs: Any) -> Dict[str, Any]:
        if not inputs.get("file_path"): return _error("INVALID_INPUT", "必须提供 file_path")
        path = Path(str(inputs["file_path"])).expanduser().resolve()
        if not path.is_file(): return _error("NOT_FOUND", str(path))
        try: data, text, enc, bom, ending = _load(path, inputs.get("encoding"))
        except (ValueError, UnicodeError) as exc: return _error("ENCODING_REQUIRED", "处理失败：" + str(exc))
        _KNOWN[str(path)] = enc
        lines = text.replace("\r\n", "\n").replace("\r", "\n").split("\n")
        offset, limit = int(inputs.get("offset", 1)), int(inputs.get("limit", 200))
        return {"ok":True,"path":str(path),"encoding":enc,"bom":bool(bom),"line_ending":{"\r\n":"CRLF","\r":"CR"}.get(ending,"LF"),"sha256":_digest(data),"total_lines":len(lines),"lines":[{"number":i+offset,"text":v} for i,v in enumerate(lines[offset-1:offset-1+limit])]}
    async def stream(self, inputs: Dict[str, Any], **kwargs: Any) -> AsyncIterator[Dict[str, Any]]: yield await self.invoke(inputs, **kwargs)


class EncodingWriteTool(Tool):
    def __init__(self) -> None:
        super().__init__(ToolCard(id="encoding_write", name="encoding_write", description="预览或完整写入文本，保留现有文件编码。", input_params={"type":"object","properties":{"file_path":{"type":"string"},"content":{"type":"string"},"encoding":{"type":"string"},"write":{"type":"boolean","default":False}},"required":["file_path","content"]}, parallel_safe=False))
    async def invoke(self, inputs: Dict[str, Any], **kwargs: Any) -> Dict[str, Any]:
        if not inputs.get("file_path") or "content" not in inputs: return _error("INVALID_INPUT", "必须提供 file_path 和 content")
        path = Path(str(inputs["file_path"])).expanduser().resolve(); exists = path.is_file()
        try:
            if exists:
                known = _KNOWN.get(str(path))
                hint = inputs.get("encoding") or known
                before, _old, enc, bom, ending = _load(path, hint)
                if known and inputs.get("encoding") and enc != known:
                    return _error("ENCODING_MISMATCH", f"文件先前按 {known} 读取，拒绝改用 {enc}")
                _KNOWN[str(path)] = enc
            else:
                before=b""; enc=_encoding(str(inputs.get("encoding","utf8"))); bom=next((m for m,n in BOMS if n==enc),b""); ending="\r\n" if "\r\n" in str(inputs["content"]) else "\n"
            after=_encode(str(inputs["content"]),enc,bom,ending)
        except (ValueError, UnicodeError) as exc: return _error("UNREPRESENTABLE_OR_UNKNOWN", "处理失败：" + str(exc))
        written=bool(inputs.get("write",False))
        if written:
            path.parent.mkdir(parents=True,exist_ok=True); path.write_bytes(after)
            if exists: _save_undo(path, before, after)
            _KNOWN[str(path)] = enc
        return {"ok":True,"operation":"update" if exists else "create","encoding":enc,"bom":bool(bom),"written":written,"before_sha256":_digest(before) if exists else None,"after_sha256":_digest(after),"bytes":len(after)}
    async def stream(self, inputs: Dict[str, Any], **kwargs: Any) -> AsyncIterator[Dict[str, Any]]: yield await self.invoke(inputs, **kwargs)


class EncodingEditTool(Tool):
    def __init__(self) -> None:
        super().__init__(ToolCard(id="encoding_edit", name="encoding_edit", description="预览或执行文字替换，保留文件原编码。", input_params={"type":"object","properties":{"file_path":{"type":"string"},"old_string":{"type":"string"},"new_string":{"type":"string"},"encoding":{"type":"string"},"replace_all":{"type":"boolean","default":False},"write":{"type":"boolean","default":False}},"required":["file_path","old_string","new_string"]}, parallel_safe=False))
    async def invoke(self, inputs: Dict[str, Any], **kwargs: Any) -> Dict[str, Any]:
        path=Path(str(inputs.get("file_path",""))).expanduser().resolve()
        if not path.is_file(): return _error("NOT_FOUND",str(path))
        try: before,text,enc,bom,ending=_load(path,inputs.get("encoding"))
        except (ValueError,UnicodeError) as exc: return _error("ENCODING_REQUIRED","处理失败：" + str(exc))
        old,new=str(inputs.get("old_string","")),str(inputs.get("new_string","")); count=text.count(old)
        if not old or count==0: return _error("EDIT_NOT_FOUND","未找到 old_string")
        if count>1 and not inputs.get("replace_all",False): return _error("AMBIGUOUS_EDIT",f"old_string 出现 {count} 次，请指定是否全部替换")
        updated=text.replace(old,new) if inputs.get("replace_all",False) else text.replace(old,new,1)
        try: after=_encode(updated,enc,bom,ending)
        except UnicodeError as exc: return _error("UNREPRESENTABLE","处理失败：" + str(exc))
        written=bool(inputs.get("write",False))
        if written: path.write_bytes(after); _save_undo(path, before, after)
        return {"ok":True,"matches":count,"encoding":enc,"written":written,"before_sha256":_digest(before),"after_sha256":_digest(after)}
    async def stream(self, inputs: Dict[str, Any], **kwargs: Any) -> AsyncIterator[Dict[str, Any]]: yield await self.invoke(inputs, **kwargs)


class EncodingGrepTool(Tool):
    def __init__(self) -> None:
        super().__init__(ToolCard(id="encoding_grep", name="encoding_grep", description="在明确指定的旧编码文件中搜索文本。", input_params={"type":"object","properties":{"pattern":{"type":"string"},"file_paths":{"type":"array","items":{"type":"string"}},"encoding":{"type":"string"},"regex":{"type":"boolean","default":False}},"required":["pattern","file_paths"]}, idempotent=True))
    async def invoke(self, inputs: Dict[str, Any], **kwargs: Any) -> Dict[str, Any]:
        hits=[]; failures=[]; pattern=str(inputs.get("pattern","")); rx=re.compile(pattern) if inputs.get("regex",False) else None
        for raw in inputs.get("file_paths",[]):
            path=Path(str(raw)).expanduser().resolve()
            try: _data,text,enc,_bom,_ending=_load(path,inputs.get("encoding"))
            except Exception as exc: failures.append({"path":str(path),"error":"读取失败：" + str(exc)}); continue
            for number,line in enumerate(text.replace("\r\n","\n").replace("\r","\n").split("\n"),1):
                if (rx.search(line) if rx else pattern in line): hits.append({"path":str(path),"line":number,"text":line,"encoding":enc})
        return {"ok":True,"hits":hits,"failures":failures}
    async def stream(self, inputs: Dict[str, Any], **kwargs: Any) -> AsyncIterator[Dict[str, Any]]: yield await self.invoke(inputs, **kwargs)


class EncodingUndoTool(Tool):
    def __init__(self) -> None:
        super().__init__(ToolCard(id="encoding_undo", name="encoding_undo", description="撤销该文件最近一次且未被外部覆盖的工具修改。", input_params={"type":"object","properties":{"file_path":{"type":"string"}},"required":["file_path"]}, parallel_safe=False))
    async def invoke(self, inputs: Dict[str, Any], **kwargs: Any) -> Dict[str, Any]:
        path=Path(str(inputs.get("file_path",""))).expanduser().resolve(); record_path=_undo_path(path)
        if not record_path.is_file(): return _error("NO_UNDO","没有可用的撤销记录")
        try:
            record=json.loads(record_path.read_text(encoding="utf-8"))
            before=base64.b64decode(record["before"], validate=True)
        except (OSError, ValueError, KeyError, json.JSONDecodeError) as exc:
            return _error("INVALID_UNDO","处理失败：" + str(exc))
        if record.get("path") != str(path): return _error("INVALID_UNDO","撤销记录的文件路径不匹配")
        current=path.read_bytes() if path.is_file() else b""
        if _digest(current)!=record.get("after_sha256"): return _error("STALE_UNDO","记录修改后文件已被外部更改，拒绝撤销")
        path.write_bytes(before); record_path.unlink()
        return {"ok":True,"restored_sha256":_digest(before),"bytes":len(before)}
    async def stream(self, inputs: Dict[str, Any], **kwargs: Any) -> AsyncIterator[Dict[str, Any]]: yield await self.invoke(inputs, **kwargs)
