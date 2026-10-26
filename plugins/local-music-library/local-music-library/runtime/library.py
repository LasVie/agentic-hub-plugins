"""本地音乐库核心：只读音频、独立歌单、有限目录扫描。

Portions adapted from dsh-music-player/lib/index.js
Copyright (c) 2026 kendu76 — MIT; full notice: ../licenses/dsh-music-player/LICENSE.
Changes: Python port, canonical descriptor access, independent scan limits,
bounded HTTP ranges, strict state validation and atomic playlist persistence.
"""
import contextlib
import hashlib
import json
import os
from pathlib import Path
import re
import stat
import tempfile
import threading

VERSION = "1.0.0"
AUDIO_TYPES = {".mp3": "audio/mpeg", ".m4a": "audio/mp4", ".m4b": "audio/mp4",
               ".aac": "audio/aac", ".flac": "audio/flac", ".wav": "audio/wav",
               ".ogg": "audio/ogg", ".oga": "audio/ogg", ".opus": "audio/ogg",
               ".webm": "audio/webm"}
MAX_TRACKS, MAX_ENTRIES, MAX_DEPTH = 500, 5000, 4
MAX_FILE_BYTES, MAX_STATE_BYTES = 512 * 1024 * 1024, 256 * 1024
ID = re.compile(r"[0-9a-f]{64}\Z")


class LibraryError(ValueError):
    def __init__(self, code, message):
        super().__init__(message)
        self.code = code


def fail(code, message):
    raise LibraryError(code, message)


def canonical_directory(value):
    if not isinstance(value, str) or not value or len(value) > 4096 or "\x00" in value:
        fail("invalid_path", "请提供已有目录的真实绝对路径。")
    p = Path(value)
    if not p.is_absolute() or ".." in p.parts or p == Path(p.anchor):
        fail("invalid_path", "不能使用相对路径、.. 或文件系统根目录。")
    try:
        if p.resolve(strict=True) != p or not p.is_dir():
            fail("unsafe_path", "目录必须存在，且路径不能经过符号链接。")
    except OSError:
        fail("invalid_path", "目录不存在或不可访问。")
    return p


def atomic_json(path, value):
    data = (json.dumps(value, ensure_ascii=False, allow_nan=False, separators=(",", ":")) + "\n").encode()
    if len(data) > MAX_STATE_BYTES:
        fail("state_limit", "歌单与进度状态超过大小限制。")
    fd, tmp = tempfile.mkstemp(prefix=".write-", dir=path.parent)
    try:
        with os.fdopen(fd, "wb") as f:
            f.write(data)
            f.flush()
            os.fsync(f.fileno())
        os.replace(tmp, path)
    finally:
        with contextlib.suppress(FileNotFoundError):
            os.unlink(tmp)


def read_json(path):
    fd = os.open(path, os.O_RDONLY | os.O_NOFOLLOW | os.O_NONBLOCK)
    with os.fdopen(fd, "rb") as f:
        st = os.fstat(f.fileno())
        if not stat.S_ISREG(st.st_mode) or st.st_nlink != 1 or st.st_size > MAX_STATE_BYTES:
            fail("invalid_state", "状态文件不是安全的普通小文件。")
        return json.loads(f.read(MAX_STATE_BYTES + 1))


def parse_range(value, size):
    """只接受一个标准字节范围；返回起点、终点和响应状态。"""
    if value is None:
        return 0, size - 1, 200
    m = re.fullmatch(r"bytes=(\d{0,20})-(\d{0,20})", value)
    if not m or not any(m.groups()) or size == 0:
        fail("invalid_range", "字节范围无效或超出文件长度。")
    a, b = m.groups()
    if a:
        start, end = int(a), min(int(b), size - 1) if b else size - 1
    else:
        suffix = int(b)
        if suffix == 0:
            fail("invalid_range", "后缀字节数必须大于零。")
        start, end = max(0, size - suffix), size - 1
    if start > end or start >= size:
        fail("invalid_range", "字节范围超出文件长度。")
    return start, end, 206


class Library:
    def __init__(self, root, store, max_tracks=MAX_TRACKS, max_entries=MAX_ENTRIES, max_depth=MAX_DEPTH):
        self.root = canonical_directory(str(root))
        self.root_fd = os.open(self.root, os.O_RDONLY | os.O_DIRECTORY | os.O_NOFOLLOW)
        self.store = Path(store)
        self.max_tracks, self.max_entries, self.max_depth = max_tracks, max_entries, max_depth
        self.lock = threading.RLock()
        self.tracks = {}
        self.scan_info = {}
        self.state = {"version": VERSION, "playlists": [], "resume": {}}
        try:
            if self.store.exists() or self.store.is_symlink():
                self.state = self.validate_state(read_json(self.store))
            self.scan()
        except BaseException:
            os.close(self.root_fd)
            raise

    def close(self):
        os.close(self.root_fd)

    @staticmethod
    def validate_state(value):
        if not isinstance(value, dict) or set(value) != {"version", "playlists", "resume"} or value["version"] != VERSION:
            fail("invalid_state", "状态结构或版本不匹配；未自动修改。")
        ps = value["playlists"]
        if not isinstance(ps, list) or len(ps) > 16:
            fail("invalid_state", "歌单状态无效。")
        names = set()
        for p in ps:
            if not isinstance(p, dict) or set(p) != {"name", "tracks"}:
                fail("invalid_state", "歌单结构无效。")
            name = p["name"]
            if not isinstance(name, str) or not name.strip() or len(name) > 80 or name in names:
                fail("invalid_state", "歌单名称为空、重复或过长。")
            names.add(name)
            ids = p["tracks"]
            if not isinstance(ids, list) or len(ids) > MAX_TRACKS or any(not isinstance(x, str) or not ID.fullmatch(x) for x in ids) or len(set(ids)) != len(ids):
                fail("invalid_state", "歌单曲目编号无效或重复。")
        resume = value["resume"]
        if not isinstance(resume, dict) or set(resume) - {"track", "seconds", "volume", "mode"}:
            fail("invalid_state", "续播状态无效。")
        if resume:
            if set(resume) != {"track", "seconds", "volume", "mode"} or not isinstance(resume["track"], str) or not ID.fullmatch(resume["track"]):
                fail("invalid_state", "续播曲目编号无效。")
            for key, upper in (("seconds", 86400 * 7), ("volume", 1)):
                n = resume[key]
                if type(n) not in (int, float) or not 0 <= n <= upper:
                    fail("invalid_state", "续播时间或音量无效。")
            if resume["mode"] not in ("sequence", "repeat", "shuffle"):
                fail("invalid_state", "播放模式无效。")
        return value

    def open_relative(self, rel):
        parts = Path(rel).parts
        if not parts or Path(rel).is_absolute() or any(x in (".", "..") for x in parts):
            fail("unsafe_path", "拒绝库目录外的文件。")
        parent = os.dup(self.root_fd)
        try:
            for part in parts[:-1]:
                nxt = os.open(part, os.O_RDONLY | os.O_DIRECTORY | os.O_NOFOLLOW, dir_fd=parent)
                os.close(parent)
                parent = nxt
            fd = os.open(parts[-1], os.O_RDONLY | os.O_NOFOLLOW | os.O_NONBLOCK, dir_fd=parent)
            st = os.fstat(fd)
            if not stat.S_ISREG(st.st_mode) or st.st_nlink != 1 or not 0 < st.st_size <= MAX_FILE_BYTES:
                os.close(fd)
                fail("unsupported_file", "文件为空、过大、不是普通文件或含硬链接。")
            return fd, st
        finally:
            os.close(parent)

    @staticmethod
    def stamp(st):
        return st.st_dev, st.st_ino, st.st_size, st.st_mtime_ns

    def scan(self):
        with self.lock:
            tracks, skipped, count, truncated = {}, 0, 0, False

            def walk(fd, prefix, depth):
                nonlocal skipped, count, truncated
                entries = []
                with os.scandir(fd) as it:
                    for entry in it:
                        if count >= self.max_entries:
                            truncated = True
                            break
                        count += 1
                        entries.append(entry.name)
                for name in sorted(entries):
                    if name.startswith("."):
                        continue
                    if len(tracks) >= self.max_tracks:
                        truncated = True
                        return
                    rel = str(Path(prefix) / name)
                    try:
                        st = os.stat(name, dir_fd=fd, follow_symlinks=False)
                        if stat.S_ISDIR(st.st_mode):
                            if depth >= self.max_depth:
                                truncated = True
                                continue
                            child = os.open(name, os.O_RDONLY | os.O_DIRECTORY | os.O_NOFOLLOW, dir_fd=fd)
                            try:
                                walk(child, rel, depth + 1)
                            finally:
                                os.close(child)
                        elif Path(name).suffix.lower() in AUDIO_TYPES:
                            opened, actual = self.open_relative(rel)
                            os.close(opened)
                            tid = hashlib.sha256(rel.encode("utf-8")).hexdigest()
                            tracks[tid] = {"id": tid, "name": rel, "bytes": actual.st_size,
                                           "mime": AUDIO_TYPES[Path(name).suffix.lower()],
                                           "stamp": self.stamp(actual)}
                    except (OSError, LibraryError, UnicodeError):
                        skipped += 1

            walk(self.root_fd, "", 0)
            self.tracks = tracks
            self.scan_info = {"count": len(tracks), "entries": count, "skipped": skipped,
                              "truncated": truncated, "limits": {"tracks": self.max_tracks, "entries": self.max_entries, "depth": self.max_depth}}
            return self.manifest()

    def manifest(self):
        with self.lock:
            return {"ok": True, "version": VERSION, "display_name": "本地音乐库", "library": self.root.name,
                    "scan": self.scan_info, "tracks": [{k: v for k, v in t.items() if k != "stamp"} for t in self.tracks.values()],
                    "playlists": self.state["playlists"], "resume": self.state["resume"],
                    "message": "曲目已列出；格式能否解码由浏览器决定，点击播放后才能确认。"}

    def save_playlist(self, name, ids):
        if not isinstance(name, str) or not name.strip() or len(name.strip()) > 80:
            fail("invalid_playlist", "歌单名称必须为1至80个字符。")
        if not isinstance(ids, list) or len(ids) > MAX_TRACKS or any(not isinstance(x, str) or x not in self.tracks for x in ids):
            fail("invalid_playlist", "歌单只能包含当前库中的有效曲目。")
        with self.lock:
            name = name.strip()
            ps = [p for p in self.state["playlists"] if p["name"] != name]
            if len(ps) >= 16:
                fail("playlist_limit", "最多保存16个歌单。")
            new = {**self.state, "playlists": ps + [{"name": name, "tracks": list(dict.fromkeys(ids))}]}
            self.validate_state(new)
            atomic_json(self.store, new)
            self.state = new
            return self.manifest()

    def remove_playlist(self, name):
        if not isinstance(name, str) or not any(p["name"] == name for p in self.state["playlists"]):
            fail("playlist_missing", "未找到这个歌单。")
        with self.lock:
            new = {**self.state, "playlists": [p for p in self.state["playlists"] if p["name"] != name]}
            atomic_json(self.store, new)
            self.state = new
            return self.manifest()

    def save_resume(self, resume):
        with self.lock:
            new = {**self.state, "resume": resume}
            self.validate_state(new)
            if resume and resume["track"] not in self.tracks:
                fail("track_missing", "续播曲目已不在当前库中。")
            atomic_json(self.store, new)
            self.state = new
            return {"ok": True, "version": VERSION, "message": "播放进度已保存；再次打开后手动继续。"}

    def open_track(self, tid):
        with self.lock:
            track = self.tracks.get(tid)
            if not track:
                fail("track_missing", "未找到曲目；请刷新曲库。")
            try:
                fd, st = self.open_relative(track["name"])
            except (OSError, LibraryError):
                fail("file_changed", "文件不可访问或路径已变化；请刷新曲库。")
            if self.stamp(st) != track["stamp"]:
                os.close(fd)
                fail("file_changed", "音频文件已变化；请刷新曲库后重试。")
            return fd, st.st_size, track["mime"]
