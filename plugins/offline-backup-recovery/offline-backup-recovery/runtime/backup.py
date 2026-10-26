#!/usr/bin/env python3
"""离线备份与恢复：POSIX Python3.11+，仅标准库。

Adapted backup/verify/preview/recovery workflow from dsh-backup 0.13.4,
Copyright (c) 2026 xiaoyuyu6420, MIT. Full notice: licenses/dsh-backup/LICENSE.
Modified 2026-10-26: bounded structured ZIP, Python adapter, explicit paths,
exclusive creation, new-target recovery and Chinese results; no host hooks,
shell, schedules, deletion policy, network, credentials vault or live migration.
"""
import argparse
from contextlib import contextmanager
from datetime import datetime, timezone
import hashlib
import json
import os
from pathlib import Path, PurePosixPath
import re
import shutil
import stat
import sys
import uuid
import zipfile

VERSION = "1.0.0"
FORMAT = "offline-backup-recovery/v1"
MANIFEST = "backup-manifest.json"
MAX_ENTRIES = 1000
MAX_FILE = 16 * 1024 * 1024
MAX_TOTAL = 64 * 1024 * 1024
MAX_ARCHIVE = 80 * 1024 * 1024
MAX_MANIFEST = 512 * 1024
MAX_DEPTH = 20
SHA = re.compile(r"[0-9a-f]{64}\Z")


class Failure(Exception):
    def __init__(self, code, message, **details):
        self.code, self.message, self.details = code, message, details


def require(condition, code, message):
    if not condition:
        raise Failure(code, message)


def clean_name(s):
    require(isinstance(s, str) and s and s not in (".", "..")
            and not any(c in s for c in '/\\:') and not any(ord(c) < 32 or ord(c) == 127 for c in s),
            "unsafe_path", "路径名不得为空或含控制字符、冒号、反斜线或特殊路径段。")
    try:
        s.encode("utf-8", errors="strict")
    except UnicodeError:
        raise Failure("unsafe_path", "路径名必须是有效 UTF-8 文本。")
    return s


def absolute(value):
    require(isinstance(value, str) and value.startswith("/") and value != "/"
            and all(p not in ("", ".", "..") for p in value.split("/")[1:]),
            "unsafe_path", "请使用不含空段、. 或 .. 的真实绝对路径，不能选择根目录。")
    for part in value.split("/")[1:]:
        clean_name(part)
    return Path(value)


def directory(path):
    fd = os.open("/", os.O_RDONLY | os.O_DIRECTORY)
    try:
        for part in path.parts[1:]:
            new = os.open(part, os.O_RDONLY | os.O_DIRECTORY | os.O_NOFOLLOW, dir_fd=fd)
            os.close(fd)
            fd = new
        return fd
    except BaseException:
        os.close(fd)
        raise


@contextmanager
def parent(path):
    fd = directory(path.parent)
    try:
        yield fd, path.name
    finally:
        os.close(fd)


def regular(fd, limit):
    s = os.fstat(fd)
    require(stat.S_ISREG(s.st_mode) and s.st_nlink == 1, "unsafe_file", "只接受普通且无硬链接的文件。")
    require(s.st_size <= limit, "size_limit", "文件超过大小上限。")
    return s


def signature(s):
    return s.st_dev, s.st_ino, s.st_size, s.st_mtime_ns, s.st_ctime_ns


def digest_stream(f):
    f.seek(0)
    h, count = hashlib.sha256(), 0
    while chunk := f.read(65536):
        count += len(chunk)
        require(count <= MAX_ARCHIVE, 'size_limit', '读取期间归档超过大小上限。')
        h.update(chunk)
    return h.hexdigest()


def zip_info(name, is_dir=False):
    z = zipfile.ZipInfo(name, (1980, 1, 1, 0, 0, 0))
    z.create_system = 3
    z.compress_type = zipfile.ZIP_STORED
    z.external_attr = ((stat.S_IFDIR | 0o700) if is_dir else (stat.S_IFREG | 0o600)) << 16
    return z


def no_duplicate_keys(pairs):
    out = {}
    for k, v in pairs:
        require(k not in out, "invalid_archive", "清单含重复字段。")
        out[k] = v
    return out


def relative(value):
    require(isinstance(value, str) and len(value.encode('utf-8', errors='replace')) <= 2048,
            "unsafe_path", "清单路径无效或过长。")
    parts = value.split("/")
    require(0 < len(parts) <= MAX_DEPTH, "size_limit", "目录深度超过20层。")
    for part in parts:
        clean_name(part)
    require(PurePosixPath(value).as_posix() == value, "unsafe_path", "清单路径不是规范相对路径。")
    return parts


def inspect_stream(f, expected=None):
    before = regular(f.fileno(), MAX_ARCHIVE)
    if expected is not None:
        require(isinstance(expected, str) and SHA.fullmatch(expected), "invalid_argument", "expected_sha256 必须是完整的小写 SHA-256。")
    archive_hash = digest_stream(f)
    require(expected is None or archive_hash == expected, "integrity_mismatch", "归档 SHA-256 与指定值不一致。")
    f.seek(0)
    with zipfile.ZipFile(f) as z:
        infos = z.infolist()
        require(1 <= len(infos) <= MAX_ENTRIES + 1, "size_limit", "归档条目数超过上限。")
        names = [i.filename for i in infos]
        require(len(set(names)) == len(names), "invalid_archive", "归档含重复条目。")
        require(MANIFEST in names, "invalid_archive", "不是本插件支持的备份格式：缺少清单。")
        for i in infos:
            require(i.compress_type == zipfile.ZIP_STORED and not i.flag_bits & 1,
                    "invalid_archive", "只支持本插件的非加密、不压缩 ZIP 格式。")
            mode = i.external_attr >> 16
            require(stat.S_IFMT(mode) in (stat.S_IFREG, stat.S_IFDIR), "unsafe_file", "归档含链接或非普通文件类型。")
            require(i.file_size <= (MAX_MANIFEST if i.filename == MANIFEST else MAX_FILE), "size_limit", "归档成员超过大小上限。")
        mi = z.getinfo(MANIFEST)
        require(not mi.is_dir() and stat.S_ISREG(mi.external_attr >> 16), "invalid_archive", "清单必须是普通文件。")
        m = json.loads(z.read(mi).decode("utf-8"), object_pairs_hook=no_duplicate_keys)
        require(isinstance(m, dict) and set(m) == {"format", "plugin_version", "source_name", "created_at", "entries"}
                and m['format'] == FORMAT and m['plugin_version'] == VERSION
                and isinstance(m['created_at'], str), "invalid_archive", "清单格式或版本不受支持。")
        clean_name(m['source_name'])
        entries = m['entries']
        require(isinstance(entries, list) and len(entries) <= MAX_ENTRIES, "size_limit", "清单条目数超过上限。")
        indexed, total, files = {}, 0, 0
        for e in entries:
            require(isinstance(e, dict) and set(e) == {"path", "type", "size", "sha256"}, "invalid_archive", "清单条目字段无效。")
            relative(e['path'])
            require(e['path'] not in indexed, "invalid_archive", "清单含重复路径。")
            require(e['type'] in ('file', 'directory') and type(e['size']) is int and 0 <= e['size'] <= MAX_FILE,
                    "invalid_archive", "清单类型或大小无效。")
            is_dir = e['type'] == 'directory'
            require((is_dir and e['size'] == 0 and e['sha256'] is None)
                    or (not is_dir and isinstance(e['sha256'], str) and SHA.fullmatch(e['sha256'])),
                    "invalid_archive", "清单摘要无效。")
            name = 'data/' + e['path'] + ('/' if is_dir else '')
            require(name in names, "invalid_archive", "清单对应的归档成员缺失。")
            info = z.getinfo(name)
            require(info.is_dir() == is_dir and info.file_size == e['size']
                    and stat.S_ISDIR(info.external_attr >> 16) == is_dir, "invalid_archive", "成员类型或大小与清单不符。")
            if is_dir:
                require(z.read(info) == b'', 'invalid_archive', '目录成员必须为空且通过ZIP校验。')
            total += e['size']
            require(total <= MAX_TOTAL, "size_limit", "文件合计超过64MiB。")
            if not is_dir:
                h, read = hashlib.sha256(), 0
                with z.open(info) as src:
                    while chunk := src.read(65536):
                        read += len(chunk)
                        require(read <= e['size'], "size_limit", "实际数据超出声明大小。")
                        h.update(chunk)
                require(read == e['size'] and h.hexdigest() == e['sha256'], "integrity_mismatch", "成员 SHA-256 校验失败。")
                files += 1
            indexed[e['path']] = e
        require(set(names) == {MANIFEST} | {'data/' + e['path'] + ('/' if e['type'] == 'directory' else '') for e in entries},
                "invalid_archive", "归档含未列入清单的成员。")
        for path in indexed:
            for ancestor in PurePosixPath(path).parents:
                if str(ancestor) != '.':
                    require(str(ancestor) in indexed and indexed[str(ancestor)]['type'] == 'directory',
                            "invalid_archive", "父目录缺失或被文件占用。")
    require(signature(before) == signature(regular(f.fileno(), MAX_ARCHIVE)), "source_changed", "校验期间归档发生变化。")
    return m, {'archive_sha256': archive_hash, 'archive_bytes': before.st_size, 'file_count': files,
               'directory_count': len(entries) - files, 'total_bytes': total, 'integrity_verified': True}


@contextmanager
def opened_archive(path):
    with parent(path) as (fd, name):
        n = os.open(name, os.O_RDONLY | os.O_NOFOLLOW | os.O_NONBLOCK, dir_fd=fd)
        with os.fdopen(n, 'rb') as f:
            yield f


def create(inputs):
    require(inputs.get('confirmed') is True, "confirmation_required", "请先取得用户对复制该目录并创建备份的明确授权。")
    source, output = absolute(inputs.get('source_dir')), absolute(inputs.get('archive_path'))
    require(source != Path.home(), "unsafe_path", "请选择具体数据目录，不备份整个用户主目录。")
    require(output.suffix == '.zip' and not output.is_relative_to(source), "unsafe_path", "备份须为源目录以外的新 .zip 文件。")
    source_fd = directory(source)
    try:
        with parent(output) as (dest, name):
            require(not os.path.lexists(output), "output_exists", "备份目标已存在，拒绝覆盖。")
            temp = '.offline-backup-' + uuid.uuid4().hex + '.tmp'
            fd = os.open(temp, os.O_RDWR | os.O_CREAT | os.O_EXCL | os.O_NOFOLLOW, 0o600, dir_fd=dest)
            entries, total = [], 0
            try:
                with os.fdopen(fd, 'w+b') as f:
                    with zipfile.ZipFile(f, 'w', compression=zipfile.ZIP_STORED) as z:
                        def walk(dfd, prefix=''):
                            nonlocal total
                            before = os.fstat(dfd)
                            names = []
                            with os.scandir(dfd) as scan:
                                for item in scan:
                                    names.append(item.name)
                                    require(len(names) + len(entries) <= MAX_ENTRIES, 'size_limit', '最多备份1000个文件和目录。')
                            for name in sorted(names):
                                clean_name(name)
                                rel = prefix + name
                                relative(rel)
                                require(len(entries) < MAX_ENTRIES, "size_limit", "最多备份1000个文件和目录。")
                                s = os.stat(name, dir_fd=dfd, follow_symlinks=False)
                                if stat.S_ISDIR(s.st_mode):
                                    child = os.open(name, os.O_RDONLY | os.O_DIRECTORY | os.O_NOFOLLOW, dir_fd=dfd)
                                    try:
                                        z.writestr(zip_info('data/' + rel + '/', True), b'')
                                        entries.append({'path': rel, 'type': 'directory', 'size': 0, 'sha256': None})
                                        walk(child, rel + '/')
                                    finally:
                                        os.close(child)
                                else:
                                    require(stat.S_ISREG(s.st_mode) and s.st_nlink == 1, "unsafe_file", "源目录含链接、硬链接或非普通文件，备份已拒绝。")
                                    n = os.open(name, os.O_RDONLY | os.O_NOFOLLOW | os.O_NONBLOCK, dir_fd=dfd)
                                    with os.fdopen(n, 'rb') as src:
                                        first = regular(src.fileno(), MAX_FILE)
                                        require(signature(s) == signature(first), "source_changed", "扫描后源文件发生变化。")
                                        h, count = hashlib.sha256(), 0
                                        with z.open(zip_info('data/' + rel), 'w') as out:
                                            while chunk := src.read(65536):
                                                count += len(chunk)
                                                total += len(chunk)
                                                require(count <= MAX_FILE and total <= MAX_TOTAL, "size_limit", "单文件最多16MiB，合计最多64MiB。")
                                                out.write(chunk)
                                                h.update(chunk)
                                        require(count == first.st_size and signature(first) == signature(regular(src.fileno(), MAX_FILE)),
                                                "source_changed", "读取期间源文件发生变化，请待目录稳定后重试。")
                                    entries.append({'path': rel, 'type': 'file', 'size': count, 'sha256': h.hexdigest()})
                            require(signature(before) == signature(os.fstat(dfd)), "source_changed", "备份期间目录发生变化，请在停止写入后重试。")
                        walk(source_fd)
                        manifest = {'format': FORMAT, 'plugin_version': VERSION, 'source_name': source.name,
                                    'created_at': datetime.now(timezone.utc).isoformat(), 'entries': entries}
                        raw = json.dumps(manifest, ensure_ascii=False, separators=(',', ':')).encode('utf-8')
                        require(len(raw) <= MAX_MANIFEST, "size_limit", "备份清单过大。")
                        z.writestr(zip_info(MANIFEST), raw)
                    f.flush()
                    os.fsync(f.fileno())
                    _, report = inspect_stream(f)
                    # Atomic exclusive publication; never replace a racing output.
                    os.link(temp, output.name, src_dir_fd=dest, dst_dir_fd=dest, follow_symlinks=False)
                os.unlink(temp, dir_fd=dest)
                return {'message': '备份已创建并逐文件校验。请保存归档 SHA-256；它不是来源认证或加密。',
                        'archive_path': str(output), **report}
            finally:
                try:
                    os.unlink(temp, dir_fd=dest)
                except FileNotFoundError:
                    pass
    finally:
        os.close(source_fd)


def inspect(inputs):
    path = absolute(inputs.get('archive_path'))
    with opened_archive(path) as f:
        m, report = inspect_stream(f, inputs.get('expected_sha256'))
    return {'message': '归档与全部成员校验通过；摘要一致不等于来源可信。', 'archive_path': str(path),
            'source_name': m['source_name'], 'created_at': m['created_at'], 'entries': m['entries'], **report}


def restore(inputs):
    mode = inputs.get('mode', 'preview')
    require(mode in ('preview', 'restore'), 'invalid_argument', 'mode 只能为 preview 或 restore。')
    archive, target = absolute(inputs.get('archive_path')), absolute(inputs.get('target_dir'))
    expected = inputs.get('expected_sha256')
    if mode == 'restore':
        require(inputs.get('confirmed') is True, 'confirmation_required', '恢复写入需要用户明确授权，confirmed=true。')
        require(isinstance(expected, str) and SHA.fullmatch(expected), 'invalid_argument', '恢复必须提供先前校验返回的完整 archive_sha256，作为 expected_sha256。')
    with opened_archive(archive) as f, parent(target) as (pfd, name):
        require(not os.path.lexists(target), 'output_exists', '恢复目标必须尚不存在；即使是空目录也拒绝覆盖。')
        m, report = inspect_stream(f, expected)
        if mode == 'preview':
            return {'message': '仅预览；未创建目录或写入文件。恢复只新建目标目录，不覆盖现有内容。',
                    'mode': mode, 'target_dir': str(target), 'writes_performed': False, 'entries': m['entries'], **report}
        os.mkdir(name, 0o700, dir_fd=pfd)
        identity = os.stat(name, dir_fd=pfd, follow_symlinks=False)
        try:
            dfd = os.open(name, os.O_RDONLY | os.O_DIRECTORY | os.O_NOFOLLOW, dir_fd=pfd)
            try:
                f.seek(0)
                with zipfile.ZipFile(f) as z:
                    for e in sorted(m['entries'], key=lambda e: (len(relative(e['path'])), e['path'])):
                        if e['type'] == 'directory':
                            os.mkdir(e['path'], 0o700, dir_fd=dfd)
                        else:
                            fd = os.open(e['path'], os.O_WRONLY | os.O_CREAT | os.O_EXCL | os.O_NOFOLLOW, 0o600, dir_fd=dfd)
                            h, count = hashlib.sha256(), 0
                            with os.fdopen(fd, 'wb') as out, z.open('data/' + e['path']) as src:
                                while chunk := src.read(65536):
                                    count += len(chunk)
                                    require(count <= e['size'], 'integrity_mismatch', '恢复读取大小发生变化。')
                                    out.write(chunk)
                                    h.update(chunk)
                                out.flush()
                                os.fsync(out.fileno())
                            require(count == e['size'] and h.hexdigest() == e['sha256'], 'integrity_mismatch', '恢复文件摘要不匹配。')
                            check_fd = os.open(e['path'], os.O_RDONLY | os.O_NOFOLLOW | os.O_NONBLOCK, dir_fd=dfd)
                            with os.fdopen(check_fd, 'rb') as saved:
                                before = regular(saved.fileno(), MAX_FILE)
                                actual = digest_stream(saved)
                                require(before.st_size == e['size'] and actual == e['sha256']
                                        and signature(before) == signature(regular(saved.fileno(), MAX_FILE)),
                                        'integrity_mismatch', '恢复后的磁盘文件复核失败。')
                require(digest_stream(f) == report['archive_sha256'], 'source_changed', '恢复期间归档发生变化。')
            finally:
                os.close(dfd)
        except BaseException as error:
            try:
                current = os.stat(name, dir_fd=pfd, follow_symlinks=False)
                require((current.st_dev, current.st_ino) == (identity.st_dev, identity.st_ino), 'source_changed', '失败目标被其他进程替换，拒绝清理。')
                shutil.rmtree(name, dir_fd=pfd)
            except Exception:
                raise Failure('partial_output', '恢复失败且无法安全清理新目标，请人工检查；不会删除其他目录。', partial_output=str(target)) from error
            raise
    return {'message': '已恢复到新目录，并在写入时逐文件复核摘要。原有目录未覆盖。', 'mode': mode,
            'target_dir': str(target), 'writes_performed': True, **report}


OPERATIONS = {'create': create, 'inspect': inspect, 'restore': restore}


def dispatch(operation, inputs):
    try:
        require(os.name == 'posix' and sys.version_info >= (3, 11), 'unsupported_platform', '仅支持 macOS/Linux 的 Python3.11及以上版本。')
        require(operation in OPERATIONS and isinstance(inputs, dict), 'invalid_argument', '操作或参数对象无效。')
        allowed = {'create': {'source_dir', 'archive_path', 'confirmed'},
                   'inspect': {'archive_path', 'expected_sha256'},
                   'restore': {'archive_path', 'target_dir', 'mode', 'expected_sha256', 'confirmed'}}
        require(set(inputs) <= allowed[operation], 'invalid_argument', '含不支持的参数；不会静默忽略。')
        return {'ok': True, 'version': VERSION, **OPERATIONS[operation](inputs)}
    except Failure as e:
        return {'ok': False, 'version': VERSION, 'error': {'code': e.code, 'message': e.message, **e.details}}
    except (zipfile.BadZipFile, UnicodeError, json.JSONDecodeError, KeyError, TypeError, ValueError, RecursionError, NotImplementedError):
        return {'ok': False, 'version': VERSION, 'error': {'code': 'invalid_archive', 'message': '参数或备份内容无效、损坏或格式不受支持；操作未成功。'}}
    except OSError as e:
        return {'ok': False, 'version': VERSION, 'error': {'code': 'filesystem_error', 'message': '文件系统操作失败；请检查路径、权限、链接、并发修改和磁盘空间。', 'errno': e.errno}}


if __name__ == '__main__':
    class ChineseParser(argparse.ArgumentParser):
        def format_help(self):
            return super().format_help().replace('usage:', '用法：')

        def error(self, message):
            self.exit(2, json.dumps({'ok': False, 'version': VERSION, 'error': {
                'code': 'invalid_argument', 'message': '命令行参数无效；请使用 --help 查看中文用法。'}}, ensure_ascii=False) + '\n')

    parser = ChineseParser(description='离线备份与恢复：手动创建、校验、预览并恢复到新目录。', add_help=False)
    parser._positionals.title = '位置参数'
    parser._optionals.title = '选项'
    parser.add_argument('-h', '--help', action='help', help='显示中文帮助后退出')
    parser.add_argument('operation', choices=tuple(OPERATIONS), help='create创建、inspect校验、restore预览或恢复')
    parser.add_argument('--input-json', required=True, help='与工具相同的 JSON 参数对象')
    args = parser.parse_args()
    try:
        data = json.loads(args.input_json)
    except (json.JSONDecodeError, ValueError):
        data = None
    result = dispatch(args.operation, data)
    print(json.dumps(result, ensure_ascii=False, indent=2))
    sys.exit(0 if result['ok'] else 2)
