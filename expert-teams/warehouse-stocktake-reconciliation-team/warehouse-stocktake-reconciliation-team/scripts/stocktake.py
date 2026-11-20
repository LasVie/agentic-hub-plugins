"""Offline cut-off reconciliation for one authorized stocktake."""
from __future__ import annotations

import argparse
from collections import defaultdict
import csv
from datetime import datetime, timezone
import hashlib
import io
import json
from pathlib import Path
import re
import sys

HEADERS = {
    'book': 'sku location unit at quantity',
    'count': 'sku location unit at quantity',
    'moves': 'id sku location unit at delta',
}
CSV_COLUMNS = ('商品编码', '库位', '单位', '账面时点 UTC', '盘点时点 UTC', '原账面数量', '实盘数量',
               '流水净变动', '盘点时点账面数量', '剩余差异', '分类', '纳入流水编号')
LABELS = {'timing': '时点差异已解释', 'recount': '建议复盘', 'match': '无差异'}
TOKEN = re.compile(r'[^\W_][\w.-]{0,79}\Z')
TIME = re.compile(r'\d{4}-\d{2}-\d{2}T\d{2}:\d{2}:\d{2}(?:Z|[+-]\d{2}:\d{2})\Z', re.ASCII)
MAX_BYTES = 4 * 1024 * 1024


def digest(raw):
    return hashlib.sha256(raw).hexdigest()


def bounded(path):
    with path.open('rb') as f:
        raw = f.read(MAX_BYTES + 1)
    if len(raw) > MAX_BYTES:
        raise ValueError(f'{path.name} 超过大小上限')
    return raw


def timestamp(text):
    if not TIME.fullmatch(text) or text.endswith('-00:00'):
        raise ValueError('时点必须带明确时区偏移，精确到秒')
    if text[-1] != 'Z' and (int(text[-2:]) > 59 or int(text[-5:-3]) > 23):
        raise ValueError('时区偏移无效')
    try:
        return datetime.fromisoformat(text.replace('Z', '+00:00')).astimezone(timezone.utc)
    except (ValueError, OverflowError):
        raise ValueError('日期或时区偏移无效') from None


def parse_csv(raw, name):
    header = HEADERS[name].split()
    try:
        reader = csv.reader(io.StringIO(raw.decode('utf-8-sig'), newline=''), strict=True)
        if next(reader, None) != header:
            raise ValueError('CSV 表头与规定顺序不符')
        for row in reader:
            try:
                if len(row) != len(header):
                    raise ValueError('列数不符')
                data = dict(zip(header, row))
                for field in ('sku', 'location', 'unit') + (('id',) if name == 'moves' else ()):
                    if not TOKEN.fullmatch(data[field]):
                        raise ValueError(f'{field} 须以字母或数字开头，且不能含空格或公式')
                field = 'delta' if name == 'moves' else 'quantity'
                pattern = r'-?[0-9]{1,12}' if name == 'moves' else r'[0-9]{1,12}'
                if not re.fullmatch(pattern, data[field]):
                    raise ValueError(f'{field} 必须为规定范围内的整数')
                qty = int(data[field])
                if name == 'moves' and qty == 0:
                    raise ValueError('流水变动不能为零')
                yield (data['sku'], data['location']), data['unit'], timestamp(data['at']), qty, data.get('id')
            except ValueError as e:
                raise ValueError(f'第 {reader.line_num} 行：{e}') from None
    except (csv.Error, UnicodeError, ValueError) as e:
        raise ValueError(f'{name}.csv：{e}') from None


def load(folder):
    raw = {name: bounded(folder / f'{name}.csv') for name in HEADERS}
    snapshots = []
    for name in ('book', 'count'):
        balances = {}
        for key, unit, at, qty, _ in parse_csv(raw[name], name):
            if key in balances:
                raise ValueError(f'{name}.csv 有重复商品和库位')
            balances[key] = (unit, at, qty)
        if not balances:
            raise ValueError(f'{name}.csv 缺少数据')
        snapshots.append(balances)
    book, count = snapshots
    if book.keys() != count.keys():
        raise ValueError('账面或实盘缺少对应的商品和库位；不能用零代替')
    for key, (unit, at, _) in book.items():
        if unit != count[key][0]:
            raise ValueError(f'单位不一致：{key[0]} / {key[1]}')
        if at > count[key][1]:
            raise ValueError(f'盘点早于账面时点：{key[0]} / {key[1]}')
    ids = set()
    moves = []
    for move in parse_csv(raw['moves'], 'moves'):
        key, unit, _, _, mid = move
        if mid in ids:
            raise ValueError(f'重复流水编号：{mid}')
        ids.add(mid)
        if key not in book or unit != book[key][0]:
            raise ValueError(f'流水商品、库位或单位与快照不一致：{mid}')
        moves.append(move)
    return book, count, moves, {f'{n}.csv': digest(b) for n, b in raw.items()}


def as_row(key, book, count, expected, residual, move_ids):
    unit, start, original = book[key]
    _, end, observed = count[key]
    if expected < 0:
        raise ValueError(f'盘点时点推算库存为负：{key[0]} / {key[1]}')
    label = 'recount' if residual else ('timing' if original != observed else 'match')
    return dict(sku=key[0], location=key[1], unit=unit, start=start.isoformat(), end=end.isoformat(),
                original=original, observed=observed, expected=expected, residual=residual,
                movement_ids=sorted(move_ids), label=label)


def reconcile(book, count, moves):
    grouped = defaultdict(list)
    for key, _, at, delta, mid in moves:
        if book[key][1] < at <= count[key][1]:
            grouped[key].append((delta, mid))
    rows = []
    for key in sorted(book):
        included = grouped[key]
        expected = book[key][2] + sum(d for d, _ in included)
        rows.append(as_row(key, book, count, expected, count[key][2] - expected, [m for _, m in included]))
    return rows


def baseline(book, count, moves):
    # Independent reverse calculation from physical counts, not the forward ledger.
    implied_book = {key: rec[2] for key, rec in count.items()}
    ids = defaultdict(set)
    for key, _, at, delta, mid in sorted(moves, key=lambda m: (m[2], m[4]), reverse=True):
        if at > count[key][1] or at <= book[key][1]:
            continue
        implied_book[key] -= delta
        ids[key].add(mid)
    result = []
    for key, implied in sorted(implied_book.items()):
        residual = implied - book[key][2]
        result.append(as_row(key, book, count, count[key][2] - residual, residual, ids[key]))
    return result


def write_once(path, content):
    with path.open('xb') as fh:
        fh.write(content.encode('utf-8'))


def dump(value):
    return json.dumps(value, ensure_ascii=False, indent=2, sort_keys=True) + '\n'


def artifact(folder, name, hashes):
    obj = json.loads((folder / f'{name}.json').read_text(encoding='utf-8'))
    if not isinstance(obj, dict) or obj.get('stage') != name or obj.get('source_sha256') != hashes:
        raise ValueError('交接阶段或源文件指纹不一致')
    return obj


def deliver(folder, hashes, expected):
    outputs = ('exceptions.csv', 'review.md', 'audit.json')
    if any((folder / p).exists() for p in outputs):
        raise ValueError('交付文件已存在；请使用新的输出目录')
    checked = artifact(folder, 'inspect', hashes)
    reverse = artifact(folder, 'baseline', hashes)
    forward = artifact(folder, 'reconcile', hashes)
    if checked.get('keys') != len(expected) or forward.get('rows') != reverse.get('rows') or reverse.get('rows') != expected:
        raise ValueError('交接结果与独立复核不一致；不交付')
    summary = {label: sum(row['label'] == label for row in expected) for label in LABELS}
    buf = io.StringIO(newline='')
    writer = csv.writer(buf)
    writer.writerow(CSV_COLUMNS)
    for r in expected:
        if r['label'] == 'match':
            continue
        writer.writerow((r['sku'], r['location'], r['unit'], r['start'], r['end'], r['original'], r['observed'],
                         r['expected'] - r['original'], r['expected'], r['residual'], LABELS[r['label']],
                         ';'.join(r['movement_ids'])))
    write_once(folder / outputs[0], '\ufeff' + buf.getvalue())
    write_once(folder / outputs[1], '# 库存盘点差异复核\n\n正推与倒推独立复核结果一致。\n\n' +
               ''.join(f'- {LABELS[k]}：{n}\n' for k, n in summary.items()) +
               '\n详细差异见 `exceptions.csv`。本结果不证明原始流水完整或实盘无误，不修改库存。\n')
    write_once(folder / outputs[2], dump(dict(source_sha256=hashes, rows=expected, summary=summary,
               handoff_sha256={f'{s}.json': digest((folder / f'{s}.json').read_bytes())
                               for s in ('inspect', 'baseline', 'reconcile')})))


def main():
    p = argparse.ArgumentParser(add_help=False, usage='stocktake.py 阶段 输入目录 输出目录 --confirmed')
    p.add_argument('-h', '--help', action='help', help='显示帮助')
    p.add_argument('stage', choices=('inspect', 'baseline', 'reconcile', 'deliver'), help='执行阶段')
    p.add_argument('inputs', type=Path, help='三份 CSV 所在目录')
    p.add_argument('output', type=Path, help='本次任务专用的输出目录')
    p.add_argument('--confirmed', action='store_true', help='用户已确认时点口径和流水完整性')
    args = p.parse_args()
    try:
        if not args.confirmed:
            raise ValueError('先确认时点口径和流水完整性，再使用 --confirmed')
        folder = args.output.resolve()
        if not folder.is_dir() or folder == args.inputs.resolve():
            raise ValueError('请提供已建立的独立输出目录')
        book, count, moves, hashes = load(args.inputs)
        info = dict(stage=args.stage, source_sha256=hashes)
        if args.stage == 'inspect':
            info.update(keys=len(book), movements=len(moves))
        elif args.stage == 'baseline':
            info['rows'] = baseline(book, count, moves)
        elif args.stage == 'reconcile':
            artifact(folder, 'inspect', hashes)
            info['rows'] = reconcile(book, count, moves)
        else:
            deliver(folder, hashes, baseline(book, count, moves))
        if args.stage != 'deliver':
            write_once(folder / f'{args.stage}.json', dump(info))
        print('本阶段处理完成。')
    except FileExistsError:
        print('无法继续：阶段产物已存在；请使用新的输出目录。', file=sys.stderr)
        return 2
    except FileNotFoundError:
        print('无法继续：缺少输入文件或阶段产物。', file=sys.stderr)
        return 2
    except (ValueError, OSError) as e:
        print(f'无法继续：{e}', file=sys.stderr)
        return 2
    return 0


if __name__ == '__main__':
    raise SystemExit(main())
