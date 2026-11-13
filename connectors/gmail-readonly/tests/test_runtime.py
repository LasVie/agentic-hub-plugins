"""Check the actual executable and CLI response contract without Gmail access."""
from __future__ import annotations

import json
import os
from pathlib import Path
import site
import subprocess
import sys
import venv

import pytest

PAYLOAD = Path(__file__).resolve().parents[1] / "gmail-readonly"
sys.path.insert(0, str(PAYLOAD))
import launcher


@pytest.fixture
def command(tmp_path, monkeypatch):
    private = tmp_path / "private"
    private.mkdir(mode=0o700)
    monkeypatch.setenv("GMAIL_READONLY_HOME", str(private))
    runtime = private / "runtime"
    venv.EnvBuilder(with_pip=False).create(runtime)
    packages = next(runtime.glob("Lib/site-packages" if os.name == "nt" else "lib/python*/site-packages"))
    (packages / "test-deps.pth").write_text("\n".join(site.getsitepackages()) + "\n")
    bin_dir = tmp_path / "test bin"
    launcher.install_command(bin_dir)
    launcher.install_command(bin_dir)
    executable = bin_dir / ("gmail-readonly.cmd" if os.name == "nt" else "gmail-readonly")

    def invoke(*args):
        return subprocess.run([str(executable), *args], cwd=tmp_path, capture_output=True, text=True, timeout=15)

    return invoke


def test_command_runs_outside_package_directory(command):
    assert command("runtime-version").stdout.strip() == "1.5.1"
    help_result = command("--help")
    assert help_result.returncode == 0 and "读取一个邮件会话" in help_result.stdout
    assert "发送一封新邮件" in help_result.stdout and "更新现有草稿" in help_result.stdout


def test_runtime_probe_does_not_report_version_before_setup(tmp_path, monkeypatch):
    monkeypatch.setenv("GMAIL_READONLY_HOME", str(tmp_path / "private"))
    result = subprocess.run(
        [sys.executable, "-B", str(PAYLOAD / "launcher.py"), "runtime-version"],
        cwd=tmp_path, capture_output=True, text=True, timeout=15,
    )
    assert result.returncode == 1
    assert not result.stdout
    assert launcher.VERSION not in result.stderr


@pytest.mark.parametrize("use_symlink", [False, True])
def test_prepare_selects_uv_python_when_desktop_path_has_only_system_python(tmp_path, monkeypatch, use_symlink):
    monkeypatch.setattr(launcher.sys, "version_info", (3, 9, 6))
    monkeypatch.setattr(launcher.sys, "platform", "darwin")
    monkeypatch.setattr(launcher.shutil, "which", lambda name: None)
    monkeypatch.setattr(launcher.platform, "machine", lambda: "arm64")
    monkeypatch.setenv("HOME", str(tmp_path))
    python = tmp_path / ".local/share/uv/python/cpython-3.11-macos-aarch64-none/bin/python3.11"
    python.parent.mkdir(parents=True)
    python.touch(mode=0o700)
    shortcut = tmp_path / ".local/bin/python3.11"
    if use_symlink:
        shortcut.parent.mkdir(parents=True)
        shortcut.symlink_to(python)
    # Keep the host's other installation directories out of the fixture.
    monkeypatch.setattr(launcher.os, "access", lambda path, mode: path in {python, shortcut})
    assert launcher.runtime_python() == str(python)


@pytest.mark.parametrize("args, code", [
    (["search", "--query", "subject:未授权合成测试", "--max-results", "1"], "not_signed_in"),
    (["read-message", "--message-id", "../send"], "invalid_argument"),
    (["read-thread", "--thread-id", "synthetic-thread"], "not_signed_in"),
    (["edit-draft", "--draft-id", "d1", "--body", "新正文"], "not_signed_in"),
    (["send", "--to", "receiver@example.invalid", "--subject", "主题", "--body", "正文"], "not_signed_in"),
    (["send-draft", "--draft-id", "d1"], "not_signed_in"),
    (["reply", "--message-id", "m1", "--body", "回信"], "not_signed_in"),
])
def test_read_commands_fail_without_credentials_or_with_invalid_arguments(command, args, code):
    result = command(*args)
    assert result.returncode == 1
    payload = json.loads(result.stderr)
    assert payload["ok"] is False and payload["version"] == "1.5.1"
    assert payload["error"]["code"] == code


def test_invalid_cli_parameters_do_not_echo_query(command):
    result = command("search", "--max-results", "private-argument")
    assert result.returncode == 2
    assert "private-argument" not in result.stderr
    assert json.loads(result.stderr)["error"]["code"] == "invalid_argument"
