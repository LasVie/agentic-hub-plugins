import os
from pathlib import Path
import shutil
import subprocess
import sys


def main():
    bundled = Path('/Applications/WorkSwarm.app/Contents/Resources/node-runtime/bin/node')
    candidates = [str(bundled)] if bundled.is_file() else []
    located = shutil.which('node')
    if located and located not in candidates:
        candidates.append(located)
    for executable in candidates:
        try:
            version = subprocess.check_output([executable, '--version'], stderr=subprocess.DEVNULL, timeout=5).decode().strip()
            if int(version.lstrip('v').split('.')[0]) < 20:
                continue
            os.execv(executable, [executable, str(Path(__file__).resolve().with_name('server.mjs'))])
        except (OSError, ValueError, subprocess.SubprocessError):
            continue
    print('变更影响与回归检查台启动失败：未找到 Node.js 20+。macOS 优先使用 WorkSwarm 自带 Node；本插件无需安装 npm 依赖。', file=sys.stderr)
    return 1


if __name__ == '__main__':
    sys.exit(main())
