"""Apply child-only resource/network limits, then replace this PID with HiGHS."""
import os
from pathlib import Path
import resource

ROOT = Path(__file__).resolve().parents[1]
resource.setrlimit(resource.RLIMIT_CPU, (10, 11))
resource.setrlimit(resource.RLIMIT_FSIZE, (2 * 1024 * 1024, 2 * 1024 * 1024))
resource.setrlimit(resource.RLIMIT_NOFILE, (64, 64))
# This plugin is macOS 26+ only. Deny all network in the owned solver process;
# this is an OS child sandbox, not a hook or patch in the WorkSwarm host.
binary = str(ROOT / "vendor" / "highs" / "bin" / "highs")
os.execve("/usr/bin/sandbox-exec", ["sandbox-exec", "-p", "(version 1)(allow default)(deny network*)",
          binary, "--model_file", "model.lp", "--options_file", "options.txt",
          "--solution_file", "solution.sol"], dict(os.environ))
