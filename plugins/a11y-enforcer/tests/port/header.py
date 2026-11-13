"""网页无障碍检查：两个只读原生工具 a11y_scan（静态扫描）和 a11y_contrast（WCAG 对比度）。

本文件中“移植自上游”一段（扫描规则和对比度算法）来自 a11y-enforcer：
  https://github.com/petrovicistefan/claude-code-plugins/tree/0b19c0dd919c2b5e0b992fb1610ef2ca427a357f/a11y-enforcer
  skills/a11y-enforcer/scripts/a11y_scan.py 与 contrast.py
  MIT License, Copyright (c) 2026 Stefan Petrovici
完整许可文本见 licenses/a11y-enforcer/LICENSE，来源与修改摘要见 THIRD_PARTY_NOTICES.md。
本团队的修改：中文输出和中文识别、有界匹配与时间上限（防止畸形输入拖死）、去掉命令行入口和写文件选项、
输入范围检查；文件末尾的两个原生工具、输入校验和错误处理为本团队编写。

只读：只读取用户指定的网页界面代码文件，不改文件、不联网、不保存内容。
"""
from __future__ import annotations

import os
import re
import time

MAX_FILE_BYTES = 1024 * 1024        # 单个文件上限 1 MiB，超过的跳过并说明
MAX_TAG_CHARS = 8000                # 一个标签（含属性）最长匹配 8000 字符，防止未闭合标签造成二次方回溯
MAX_INNER_CHARS = 20000             # 查找按钮/链接结束标签时最多向后看 20000 字符
MAX_LABEL_CHARS = 2000              # 一个 <label> 标签最长匹配 2000 字符
SCAN_BUDGET_SECONDS = 60.0          # 一次调用的总时间预算
FILE_BUDGET_SECONDS = 10.0          # 单个文件的时间预算


class ScanTimeout(Exception):
    """扫描一个文件超过了时间预算。"""


class FileTooLarge(Exception):
    """文件超过大小上限。"""


def read_source(path):
    """读取一个文件并按上游的文本模式规整换行（\\r\\n、\\r 都当作 \\n）。"""
    size = os.path.getsize(path)
    if size > MAX_FILE_BYTES:
        raise FileTooLarge(size)
    with open(path, "rb") as handle:
        data = handle.read(MAX_FILE_BYTES + 1)
    if len(data) > MAX_FILE_BYTES:
        raise FileTooLarge(len(data))
    return data.decode("utf-8", errors="replace").replace("\r\n", "\n").replace("\r", "\n")


def _check_deadline(deadline):
    if deadline is not None and time.monotonic() > deadline:
        raise ScanTimeout()


def iter_tags(src, deadline=None):
    """与 TAG_RE.finditer(src) 结果相同（标签不超过 MAX_TAG_CHARS 时），但每次匹配都限定在一个窗口内，
    并定期检查时间预算；上游的整段匹配遇到大量未闭合的标签时耗时随长度二次方增长。"""
    pos = 0
    size = len(src)
    attempts = 0
    while True:
        start_match = _TAG_START.search(src, pos)
        if start_match is None:
            return
        start = start_match.start()
        attempts += 1
        if attempts % 64 == 0:
            _check_deadline(deadline)
        match = TAG_RE.match(src, start, min(size, start + MAX_TAG_CHARS))
        if match:
            yield match
            pos = match.end()
        else:
            pos = start + 1


def collect_label_for(src, deadline=None):
    """与上游 re.findall(<label ... for=...>) 得到的集合相同，但每个 <label 的匹配限定在窗口内。"""
    found = set()
    size = len(src)
    attempts = 0
    for start_match in _LABEL_START.finditer(src):
        attempts += 1
        if attempts % 64 == 0:
            _check_deadline(deadline)
        match = _LABEL_FOR.match(src, start_match.start(), min(size, start_match.start() + MAX_LABEL_CHARS))
        if match:
            found.add(match.group(1))
    return found


_TAG_START = re.compile(r"<[A-Za-z]")
_LABEL_START = re.compile(r"<label\b")
_LABEL_FOR = re.compile(r"<label\b[^>]*\b(?:for|htmlFor)\s*=\s*[\"'{]\s*[\"']?([\w:-]+)")


# ==== 以下为移植自上游的规则代码（a11y_scan.py 和 contrast.py，改动见 THIRD_PARTY_NOTICES.md） ====
