"""File lock shared by the launcher and OAuth state."""
from contextlib import contextmanager
import os


@contextmanager
def file_lock(file):
    if file.is_symlink():
        raise ValueError("锁文件不能是符号链接。")
    fd = os.open(file, os.O_CREAT | os.O_RDWR | getattr(os, "O_NOFOLLOW", 0), 0o600)
    with os.fdopen(fd, "r+b") as stream:
        if os.name == "nt":
            import msvcrt
            stream.write(b"0")
            stream.flush()
            stream.seek(0)
            msvcrt.locking(stream.fileno(), msvcrt.LK_LOCK, 1)
        else:
            import fcntl
            fcntl.flock(stream.fileno(), fcntl.LOCK_EX)
        yield


def install_lock(root):
    return file_lock(root / "runtime.lock")
