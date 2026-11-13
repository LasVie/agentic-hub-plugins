"""Read-only Drive API commands."""
import os
from datetime import date
from pathlib import Path
import re
import tempfile

SLUG = "google-drive"
LABEL = "Google 云端硬盘连接器"
SCOPE = "https://www.googleapis.com/auth/drive.readonly"
BASE = "https://www.googleapis.com/drive/v3"
MAX_DOWNLOAD = 25 * 1024 * 1024
NATIVE = "application/vnd.google-apps."
MIMES = {
    "docs": NATIVE + "document", "sheets": NATIVE + "spreadsheet",
    "slides": NATIVE + "presentation", "folder": NATIVE + "folder",
    "pdf": "application/pdf", "text": "text/plain",
}
EXPORTS = {
    MIMES["docs"]: {"pdf": "application/pdf", "docx": "application/vnd.openxmlformats-officedocument.wordprocessingml.document", "txt": "text/plain"},
    MIMES["sheets"]: {"pdf": "application/pdf", "xlsx": "application/vnd.openxmlformats-officedocument.spreadsheetml.sheet"},
    MIMES["slides"]: {"pdf": "application/pdf", "pptx": "application/vnd.openxmlformats-officedocument.presentationml.presentation"},
}
FIELDS = "id,name,mimeType,modifiedTime,webViewLink,size,parents,driveId,capabilities(canDownload),shortcutDetails"


def quote(value):
    return "'" + value.replace("\\", "\\\\").replace("'", "\\'") + "'"


def search(api, args):
    from google_api import invalid, opaque, text

    clauses = ["trashed = false"]
    if args.name:
        clauses.append("name contains " + quote(text(args.name, "名称", 256)))
    if args.kind:
        clauses.append("mimeType = " + quote(MIMES[args.kind]))
    if args.folder:
        folder = args.folder
        match = re.fullmatch(r"https://drive\.google\.com/drive/(?:u/[0-9]+/)?folders/([A-Za-z0-9_-]+)(?:[?#].*)?", folder)
        if match:
            folder = match[1]
        clauses.append(quote(opaque(folder, "目录标识")) + " in parents")
    if args.modified_since:
        try:
            day = date.fromisoformat(args.modified_since)
            if args.modified_since != day.isoformat():
                raise ValueError
        except ValueError:
            raise invalid("修改日期须使用 YYYY-MM-DD。") from None
        clauses.append("modifiedTime >= " + quote(day.isoformat() + "T00:00:00Z"))
    if not 1 <= args.limit <= 100:
        raise invalid("结果数量须为 1 到 100。")
    params = {"q": " and ".join(clauses), "pageSize": args.limit, "fields": f"nextPageToken,incompleteSearch,files({FIELDS})",
              "orderBy": "modifiedTime desc", "spaces": "drive", "supportsAllDrives": "true", "includeItemsFromAllDrives": "true"}
    if args.drive:
        params.update(corpora="drive", driveId=opaque(args.drive, "共享云端硬盘标识"))
    if args.page_token:
        params["pageToken"] = text(args.page_token, "分页标记", 2048)
    result = api.json("GET", "/files", params=params)
    return {"files": result.get("files", []), "next_page_token": result.get("nextPageToken"),
            "incomplete_search": result.get("incompleteSearch", False)}


def details(api, value):
    from google_api import file_id

    return api.json("GET", f"/files/{file_id(value, 'files')}", params={"fields": FIELDS, "supportsAllDrives": "true"})


def download(api, args):
    from google_api import Error, file_id, invalid

    ident = file_id(args.file, "files")
    target = args.output.expanduser()
    if target.exists() or target.is_symlink() or not target.parent.is_dir():
        raise invalid("请指定现有目录下的新文件路径。")
    metadata = details(api, ident)
    mime = metadata["mimeType"]
    if metadata.get("capabilities", {}).get("canDownload") is False:
        raise Error("access_denied", "Google 不允许当前账号下载此文件。")
    route = f"/files/{ident}"
    params = {"alt": "media", "supportsAllDrives": "true"}
    cap = MAX_DOWNLOAD
    if mime.startswith(NATIVE):
        export_mime = EXPORTS.get(mime, {}).get(args.format)
        if not export_mime:
            raise invalid("原生文件须指定支持的导出格式。目录和快捷方式不能下载。")
        route += "/export"
        params = {"mimeType": export_mime}
        cap = 10 * 1024 * 1024
    elif args.format:
        raise invalid("普通文件直接下载，无需指定导出格式。")
    elif int(metadata.get("size", 0)) > cap:
        raise Error("file_too_large", "文件超过 25 MiB 的下载上限。")

    temporary = None
    size = 0
    try:
        with api.response("GET", route, params=params) as response:
            with tempfile.NamedTemporaryFile(dir=target.parent, delete=False, prefix=".google-download-") as stream:
                temporary = Path(stream.name)
                for chunk in response.iter_content(chunk_size=65536):
                    size += len(chunk)
                    if size > cap:
                        raise Error("file_too_large", "文件超过本次下载或导出上限。")
                    stream.write(chunk)
        os.link(temporary, target)
    except FileExistsError:
        raise invalid("目标文件已存在，请使用新路径。") from None
    except OSError:
        raise Error("download_failed", "无法保存下载文件，请检查目录权限与可用空间。") from None
    finally:
        if temporary is not None:
            temporary.unlink(missing_ok=True)
    return {"file_id": ident, "output": str(target), "bytes": size, "message": "文件已保存到指定位置。"}


def register(commands):
    find = commands.add_parser("search", help="搜索可访问的文件和目录")
    find.set_defaults(operation=search)
    find.add_argument("--name", help="文件名查询词，按 Google Drive 的名称匹配规则")
    find.add_argument("--kind", choices=sorted(MIMES), help="筛选文件类型")
    find.add_argument("--folder", help="目录标识或链接")
    find.add_argument("--drive", help="限定共享云端硬盘标识")
    find.add_argument("--modified-since", help="从此日期起修改，格式 YYYY-MM-DD（UTC）")
    find.add_argument("--limit", type=int, default=20, help="本页最多返回多少项")
    find.add_argument("--page-token", help="上一页返回的分页标记")
    info = commands.add_parser("info", help="读取指定文件的元数据")
    info.set_defaults(operation=lambda api, args: details(api, args.file))
    info.add_argument("--file", required=True, help="文件标识或链接")
    save = commands.add_parser("download", help="下载普通文件或导出原生文件")
    save.set_defaults(operation=download)
    save.add_argument("--file", required=True, help="文件标识或链接")
    save.add_argument("--output", type=Path, required=True, help="保存到尚不存在的本机文件")
    save.add_argument("--format", choices=("pdf", "docx", "xlsx", "pptx", "txt"), help="原生文件导出格式")
