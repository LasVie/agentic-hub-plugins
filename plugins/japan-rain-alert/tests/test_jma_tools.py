"""Offline unit tests for jma_tools (no network). Run from a scratch cwd:
    python -I -B tests/test_jma_tools.py   (with the openjiuwen SDK importable)
"""
import asyncio
import datetime
import json
from pathlib import Path
import struct
import sys
import unittest
from unittest import mock
import zlib

sys.dont_write_bytecode = True
import os

ROOT = Path(__file__).resolve().parents[1]
# JAPAN_RAIN_ALERT_PAYLOAD 指向解压后的交付包目录时，测试针对该目录而不是源码目录。
PAYLOAD = Path(os.environ.get('JAPAN_RAIN_ALERT_PAYLOAD') or ROOT / 'japan-rain-alert')
sys.path.insert(0, str(PAYLOAD / 'tools'))
import jma_tools as J  # noqa: E402

assert Path(J.__file__).resolve().is_relative_to(PAYLOAD.resolve()), J.__file__


def png(width, height, ctype, depth, rows, palette=None, trns=None, interlace=0, filters=None):
    """Minimal PNG encoder used only by the tests. `rows` are already-packed scanline bytes."""
    bpp = max(1, (J_channels(ctype) * depth) // 8)
    raw, prev = bytearray(), bytes(len(rows[0]))
    for i, line in enumerate(rows):
        f = (filters or [0])[i % len(filters or [0])]
        out = bytearray(len(line))
        for k, byte in enumerate(line):
            a = line[k - bpp] if k >= bpp else 0
            b = prev[k]
            c = prev[k - bpp] if k >= bpp else 0
            if f == 0:
                pred = 0
            elif f == 1:
                pred = a
            elif f == 2:
                pred = b
            elif f == 3:
                pred = (a + b) >> 1
            else:
                p = a + b - c
                pa, pb, pc = abs(p - a), abs(p - b), abs(p - c)
                pred = a if pa <= pb and pa <= pc else (b if pb <= pc else c)
            out[k] = (byte - pred) & 255
        raw += bytes([f]) + out
        prev = line

    def chunk(kind, body):
        return struct.pack('>I', len(body)) + kind + body + struct.pack('>I', zlib.crc32(kind + body))
    data = b'\x89PNG\r\n\x1a\n' + chunk(b'IHDR', struct.pack('>IIBBBBB', width, height, depth, ctype, 0, 0, interlace))
    if palette:
        data += chunk(b'PLTE', palette)
    if trns:
        data += chunk(b'tRNS', trns)
    return data + chunk(b'IDAT', zlib.compress(bytes(raw))) + chunk(b'IEND', b'')


def J_channels(ctype):
    return {0: 1, 2: 3, 3: 1, 4: 2, 6: 4}[ctype]


class PngDecoder(unittest.TestCase):
    def test_rgba_all_filters(self):
        w, h = 5, 5
        rows = [bytes((x * 40 + y * 7) % 256 for x in range(w * 4)) for y in range(h)]
        for f in range(5):
            width, height, rgba = J.decode_png(png(w, h, 6, 8, rows, filters=[f]))
            self.assertEqual((width, height), (w, h))
            self.assertEqual(rgba, b''.join(rows), f'filter {f}')
        # 同一张图的每一行使用不同滤镜
        self.assertEqual(J.decode_png(png(w, h, 6, 8, rows, filters=[0, 1, 2, 3, 4]))[2], b''.join(rows))

    def test_rgb_gray_gray_alpha(self):
        rows = [bytes([10, 20, 30, 40, 50, 60]), bytes([70, 80, 90, 100, 110, 120])]
        self.assertEqual(J.decode_png(png(2, 2, 2, 8, rows, filters=[1, 2]))[2],
                         bytes([10, 20, 30, 255, 40, 50, 60, 255, 70, 80, 90, 255, 100, 110, 120, 255]))
        self.assertEqual(J.decode_png(png(3, 1, 0, 8, [bytes([0, 128, 255])]))[2],
                         bytes([0, 0, 0, 255, 128, 128, 128, 255, 255, 255, 255, 255]))
        self.assertEqual(J.decode_png(png(2, 1, 4, 8, [bytes([200, 0, 100, 255])]))[2],
                         bytes([200, 200, 200, 0, 100, 100, 100, 255]))

    def test_palette_depths_and_transparency(self):
        palette = bytes([255, 0, 0, 0, 255, 0, 0, 0, 255, 9, 9, 9])
        # depth 2：像素 0,1,2,3,3,2,1,0 打包成 2 字节
        packed = bytes([0b00011011, 0b11100100])
        width, _, rgba = J.decode_png(png(8, 1, 3, 2, [packed], palette=palette, trns=bytes([0, 128])))
        self.assertEqual(width, 8)
        px = [tuple(rgba[i:i + 4]) for i in range(0, 32, 4)]
        self.assertEqual(px[0], (255, 0, 0, 0))      # tRNS 索引 0 全透明
        self.assertEqual(px[1], (0, 255, 0, 128))    # 索引 1 半透明
        self.assertEqual(px[2], (0, 0, 255, 255))    # 未列出的索引不透明
        self.assertEqual(px[3], (9, 9, 9, 255))
        # depth 1 与 depth 8
        _, _, bw = J.decode_png(png(8, 1, 3, 1, [bytes([0b10100101])], palette=bytes([0, 0, 0, 255, 255, 255])))
        self.assertEqual([bw[i] for i in range(0, 32, 4)], [255, 0, 255, 0, 0, 255, 0, 255])
        _, _, p8 = J.decode_png(png(2, 1, 3, 8, [bytes([3, 0])], palette=palette))
        self.assertEqual(tuple(p8[0:4]), (9, 9, 9, 255))

    def test_rejects_unsupported_or_damaged(self):
        rows = [bytes(8)] * 2
        for bad, code in ((b'not a png', 'UPSTREAM_FORMAT_ERROR'),
                          (png(2, 2, 6, 8, rows, interlace=1), 'UNSUPPORTED_TILE_FORMAT'),
                          (png(1, 1, 2, 16, [bytes(6)]), 'UNSUPPORTED_TILE_FORMAT'),
                          (png(2, 2, 6, 8, rows)[:-20], 'UPSTREAM_FORMAT_ERROR')):
            with self.assertRaises(J.SourceError) as ctx:
                J.decode_png(bad)
            self.assertEqual(ctx.exception.code, code)
        with self.assertRaises(J.SourceError):  # 索引越界
            J.decode_png(png(1, 1, 3, 8, [bytes([5])], palette=bytes([0, 0, 0])))

    def test_size_bomb_is_bounded(self):
        bomb = png(4096, 4096, 6, 8, [bytes(4096 * 4)] * 2)  # 头部声称 4096x4096，实际数据很短
        with self.assertRaises(J.SourceError) as ctx:
            J.decode_png(bomb)
        self.assertEqual(ctx.exception.code, 'UPSTREAM_FORMAT_ERROR')


class Helpers(unittest.TestCase):
    def test_parsers(self):
        self.assertEqual(J.parse_zip('100-0005'), '1000005')
        self.assertEqual(J.parse_zip('〒154-0004'), '1540004')
        self.assertEqual(J.parse_zip('1000005'), '1000005')
        self.assertIsNone(J.parse_zip('10-0005'))
        self.assertEqual(J.parse_latlon('35.681,139.767'), (35.681, 139.767))
        self.assertEqual(J.parse_latlon(' 35.681 ， 139.767 '), (35.681, 139.767))
        self.assertIsNone(J.parse_latlon('东京'))

    def test_tile_math_matches_known_tile(self):
        # 东京站附近在 z10 的瓦片编号（Web 墨卡托标准公式）
        tx, ty, px, py = J.tile_pixel_xy(35.681, 139.767, 10)
        self.assertEqual((tx, ty), (909, 403))
        self.assertTrue(0 <= px < 256 and 0 <= py < 256)

    def test_color_tables(self):
        self.assertEqual(J.nearest_color((33, 140, 255), J.PRECIP_COLORS), '5～10 mm/h')
        self.assertEqual(J.nearest_color((250, 240, 5), J.PRECIP_COLORS), '20～30 mm/h')
        self.assertEqual(J.nearest_color((242, 242, 255), J.PRECIP_COLORS), '0～1 mm/h（微弱降水）')   # 实时瓦片里最常见的弱降水色
        self.assertEqual(J.nearest_color((160, 210, 255), J.PRECIP_COLORS), '1～5 mm/h')              # 与相邻档位不混淆
        self.assertIsNone(J.nearest_color((128, 128, 128), J.PRECIP_COLORS))
        self.assertIn('级别5', J.nearest_color((12, 0, 64), J.KIKI_COLORS))

    def test_wbgt_formula_and_ranks(self):
        self.assertAlmostEqual(J.stull_wet_bulb(20, 50), 13.7, delta=0.1)   # Stull (2011) 论文示例
        base = J.wbgt_base(30, 70)
        self.assertTrue(26 < base < 29, base)
        self.assertIsNone(J.wbgt_base(None, 50))
        self.assertEqual([J.wbgt_rank(v) for v in (None, 10, 21, 25, 28, 31)], [None, '基本安全', '注意', '警戒', '严重警戒', '危险'])

    def test_validation(self):
        self.assertEqual(J.validate('rainfall', {'place': ' 東京 ', 'days': 3})[0], {'place': '東京', 'days': 3})
        for tool, args in (('rainfall', {'days': 0}), ('rainfall', {'days': 8}), ('rainfall', {'days': True}), ('rainfall', {'bogus': 1}),
                           ('rainfall', {'station_code': 'abc'}), ('locate', {}), ('wbgt', {'place': 'x', 'times': '8:30;13:00'}), ('locate', 'x'),
                           ('warnings', {'place': 'x', 'include_outlook': 'yes'})):
            self.assertIsNotNone(J.validate(tool, args)[1], (tool, args))

    def test_call_tool_errors_do_not_touch_network(self):
        with mock.patch.object(J, 'fetch', side_effect=AssertionError('network used')):
            self.assertEqual(asyncio.run(J.call_tool('rainfall', {'days': 99}))['error']['code'], 'INVALID_ARGUMENTS')
            self.assertEqual(asyncio.run(J.call_tool('nope', {}))['error']['code'], 'UNKNOWN_TOOL')
            self.assertEqual(asyncio.run(J.call_tool('wbgt', {'place': 'x', 'times': '25:00'}))['error']['code'], 'INVALID_ARGUMENTS')

    def test_prefecture_names_map_to_capital_station_codes(self):
        self.assertEqual(len(J.PREFECTURE_STATIONS), 47)
        self.assertEqual(len({code for code, _ in J.PREFECTURE_STATIONS.values()}), 47)
        self.assertEqual(J.prefecture_station('冲绳')[:2], ('91197', '那覇'))
        self.assertEqual(J.prefecture_station('沖縄県')[:2], ('91197', '那覇'))
        self.assertEqual(J.prefecture_station('冲绳县')[:2], ('91197', '那覇'))
        self.assertEqual(J.prefecture_station('神奈川')[:2], ('46106', '横浜'))
        self.assertEqual(J.prefecture_station('东京都')[:2], ('44132', '東京'))
        self.assertEqual(J.prefecture_station('北海道')[:2], ('14163', '札幌'))
        self.assertEqual(J.prefecture_station('山形')[0], '35426')                 # 与岩手县同名的“山形”站不能被选中
        self.assertEqual(J.prefecture_station('山口')[0], '81286')                 # 与北海道同名的“山口”站不能被选中
        self.assertIn('府县厅所在地', J.prefecture_station('冲绳')[2])
        self.assertIsNone(J.prefecture_station('東京')[2])                          # 名称本身就是观测站名时不需要说明
        self.assertIsNone(J.prefecture_station('松山'))                             # 城市名不是都道府县名
        self.assertIsNone(J.prefecture_station('100-0005'))
        for simplified, japanese in J.ZH_PREFECTURES.items():
            self.assertIn(japanese, J.PREFECTURE_STATIONS, simplified)

    def test_limiter_refuses_instead_of_waiting(self):
        lim = J.Limiter(0, 2)
        lim.acquire(); lim.acquire()
        with self.assertRaises(J.SourceError) as ctx:
            lim.acquire()
        self.assertEqual(ctx.exception.code, 'RATE_LIMITED')


NOW = datetime.datetime(2026, 7, 10, 14, 20, tzinfo=J.JST)
TABLE = {'44132': {'elems': '11112110', 'lat': [35, 41.4], 'lon': [139, 45.7], 'kjName': '東京', 'knName': 'トウキョウ'},
         '44136': {'elems': '11112110', 'lat': [35, 55.0], 'lon': [139, 40.0], 'kjName': '東京一', 'knName': 'トウキョウイチ'},
         '99001': {'elems': '01000000', 'lat': [35, 40.0], 'lon': [139, 46.0], 'kjName': '雨量なし', 'knName': 'ウリョウナシ'},
         '62078': {'elems': '11112110', 'lat': [34, 40.0], 'lon': [135, 31.0], 'kjName': '大阪', 'knName': 'オオサカ'}}
AREA = {'class20s': {'1310100': {'name': '千代田区', 'parent': '130011'}, '1310200': {'name': '中央区', 'parent': '130011'}},
        'class15s': {'130011': {'parent': '130010'}}, 'class10s': {'130010': {'parent': '130000'}}, 'offices': {'130000': {'name': '東京都'}}}


def point_block(day, hour, mm_per_slot, count=18):
    out = {}
    for i in range(count):
        minute = i * 10
        stamp = f'{day}{hour + minute // 60:02d}{minute % 60:02d}00'
        out[stamp] = {'precipitation10m': [mm_per_slot, 0], 'precipitation1h': [mm_per_slot * 6, 0], 'precipitation24h': [12.5, 0],
                      'temp': [31.0, 0], 'humidity': [60, 0]}
    return out


class FakeNetwork:
    def __init__(self):
        self.calls = []

    def __call__(self, source, url, kind='json', ttl=300, limit=0):
        self.calls.append(url)
        if url.endswith('amedastable.json'):
            return TABLE
        if url.endswith('latest_time.txt'):
            return NOW.isoformat()
        if url.endswith('area.json'):
            return AREA
        if 'zipcloud' in url:
            return {'results': [{'address1': '東京都', 'address2': '千代田区', 'address3': '丸の内'}]} if 'zipcode=1000005' in url else {'results': None}
        if 'msearch.gsi' in url:
            return [{'geometry': {'coordinates': [139.767, 35.681]}, 'properties': {'title': '東京都千代田区丸の内'}}] if 'q=' in url and 'nowhere' not in url else []
        if 'reverse-geocoder' in url:
            return {'results': {'muniCd': '13101', 'lv01Nm': '丸の内一丁目'}}
        if '/amedas/data/point/' in url:
            m = url.rsplit('/', 1)[1].replace('.json', '')
            day, hour = m.split('_')
            if day > '20260710' or (day == '20260710' and int(hour) > 12):
                raise J.SourceError('NOT_FOUND', 'x')
            return point_block(day, int(hour), 0.5)
        if '/warning/data/r8/' in url:
            return [{'reportDatetime': '2026-07-10T14:00:00+09:00', 'warning': {'class20Items': [
                {'areaCode': '1310100', 'kinds': [{'code': '10', 'status': '発表'}, {'code': '03', 'status': '継続'}, {'code': '14', 'status': '解除'}, {'code': '99', 'status': '発表'}]},
                {'areaCode': '1310200', 'kinds': [{'code': '29', 'status': '発表'}]}]}}]
        if 'overview_forecast' in url:
            return {'publishingOffice': '気象庁', 'reportDatetime': '2026-07-10T11:00:00+09:00', 'targetArea': '東京都', 'text': '大気の状態が不安定です。' * 200}
        if 'targetTimes_N1' in url:
            return [{'basetime': '20260710052000', 'validtime': '20260710052000'}]
        if 'risk/targetTimes' in url:
            return [{'basetime': '20260710051000', 'validtime': '20260710051000', 'member': 'immed0'}]
        if url.endswith('.png'):
            return TILES[next(k for k in TILES if k in url)]
        if 'wbgt.env.go.jp' in url:
            if '202607' in url:
                return 'Date,Time,44132\n2026/7/10,13:00,33.0\n2026/7/10,14:00,34.0\n2026/7/10,8:00,25.0\n2026/7/9,8:00,24.0\n'
            raise J.SourceError('NOT_FOUND', 'x')
        raise AssertionError('unexpected url ' + url)


def solid(color):
    return png(256, 256, 6, 8, [bytes(color * 256)] * 256)


TILES = {'hrpns': solid((33, 140, 255, 255)), 'rain_mesh': solid((255, 40, 0, 255)), 'flood_mesh': solid((0, 0, 0, 0)), 'land': solid((170, 0, 255, 255))}


class Tools(unittest.TestCase):
    def setUp(self):
        self.net = FakeNetwork()
        patcher = mock.patch.object(J, 'fetch', self.net)
        patcher.start()
        self.addCleanup(patcher.stop)

    def run_tool(self, name, **args):
        return asyncio.run(J.call_tool(name, args))

    def test_locate_postal_code(self):
        r = self.run_tool('locate', place='100-0005')
        self.assertTrue(r['ok'], r)
        d = r['data']
        self.assertEqual((d['kind'], d['municipality_code'], d['forecast_office_code']), ('postal_code', '13101', '130000'))
        self.assertEqual(d['rain_station']['code'], '44132')           # 最近且有雨量计
        self.assertNotEqual(d['rain_station']['code'], '99001')        # 无雨量计的站点被跳过
        self.assertIn('attribution_zh', r)
        self.assertTrue(any('zipcode=1000005' in u for u in self.net.calls))

    def test_locate_errors(self):
        self.assertEqual(self.run_tool('locate', place='999-9999')['error']['code'], 'PLACE_NOT_FOUND')
        self.assertEqual(self.run_tool('locate', place='nowhere-land')['error']['code'], 'PLACE_NOT_FOUND')
        self.assertEqual(self.run_tool('locate', place='51.5,-0.12')['error']['code'], 'OUT_OF_COVERAGE')
        amb = self.run_tool('locate', place='トウキョウ')
        self.assertEqual(amb['error']['code'], 'AMBIGUOUS_PLACE')
        self.assertEqual(len(amb['error']['candidates']), 2)
        self.assertEqual(self.run_tool('locate', place='东京')['data']['kind'], 'station')   # 简体别名 -> 東京，唯一精确匹配

    def test_prefecture_alias_note_reaches_every_tool(self):
        table = dict(TABLE)
        table['91197'] = {'elems': '11112110', 'lat': [26, 12.4], 'lon': [127, 41.2], 'kjName': '那覇', 'knName': 'ナハ'}
        with mock.patch.object(J, 'station_table', return_value=table):
            for name, args in (('locate', {}), ('rainfall', {'days': 1}), ('warnings', {}), ('site_rain_risk', {}), ('wbgt', {'days': 1})):
                r = self.run_tool(name, place='冲绳', **args)
                self.assertTrue(r['ok'], (name, r))
                self.assertTrue(any('已按府县厅所在地的观测站“那覇”处理' in w for w in r['warnings_zh']), name)
        self.assertIsNone(self.run_tool('locate', place='東京')['data']['alias_note'])      # 写法本身就是观测站名，不加说明
        self.assertIn('府县厅所在地', self.run_tool('locate', place='东京')['data']['alias_note'])  # 简体写法需要说明按哪个站处理

    def test_rate_limit_from_reverse_geocoder_is_reported_not_swallowed(self):
        inner = self.net

        def limited(source, url, *a, **k):
            if 'reverse-geocoder' in url:
                raise J.SourceError('RATE_LIMITED', '限流')
            return inner(source, url, *a, **k)
        with mock.patch.object(J, 'fetch', limited):
            self.assertEqual(self.run_tool('locate', place='100-0005')['error']['code'], 'RATE_LIMITED')

    def test_other_reverse_geocoder_failure_degrades_with_a_warning(self):
        inner = self.net

        def broken(source, url, *a, **k):
            if 'reverse-geocoder' in url:
                raise J.SourceError('CONNECTION_FAILED', 'x')
            return inner(source, url, *a, **k)
        with mock.patch.object(J, 'fetch', broken):
            r = self.run_tool('locate', place='100-0005')
        self.assertTrue(r['ok'])
        self.assertIsNone(r['data']['municipality_code'])
        self.assertTrue(any('未能取得市町村代码' in w for w in r['warnings_zh']))
        with mock.patch.object(J, 'fetch', broken):
            self.assertEqual(self.run_tool('warnings', place='100-0005')['error']['code'], 'AREA_NOT_RESOLVED')

    def test_rainfall_daily_totals_and_partial_day(self):
        r = self.run_tool('rainfall', place='東京', days=2)
        self.assertTrue(r['ok'], r)
        rows = {x['date']: x for x in r['data']['daily']}
        self.assertEqual(set(rows), {'2026-07-09', '2026-07-10'})
        self.assertAlmostEqual(rows['2026-07-09']['total_mm'], 0.5 * 18 * 8, places=1)
        self.assertTrue(rows['2026-07-09']['complete'] is True or rows['2026-07-09']['slots_10min'] == 144)
        self.assertFalse(rows['2026-07-10']['complete'])
        self.assertTrue(any('140' in w for w in r['warnings_zh']))
        self.assertEqual(r['data']['latest_observation']['precipitation_24h_mm'], 12.5)
        self.assertEqual(r['data']['station']['code'], '44132')

    def test_rainfall_requires_a_location_and_reports_missing_station_code(self):
        self.assertEqual(self.run_tool('rainfall')['error']['code'], 'INVALID_ARGUMENTS')
        self.assertEqual(self.run_tool('rainfall', station_code='11111')['error']['code'], 'PLACE_NOT_FOUND')
        self.assertTrue(self.run_tool('rainfall', station_code='44132', days=1)['ok'])

    def test_no_data_is_an_error_not_zero(self):
        with mock.patch.object(J, 'collect_10min', return_value=({}, 8, 8)):
            self.assertEqual(self.run_tool('rainfall', place='東京')['error']['code'], 'NO_DATA')

    def test_warnings_highest_level_per_element_and_outlook(self):
        r = self.run_tool('warnings', place='100-0005')
        self.assertTrue(r['ok'], r)
        active = {w['element_ja']: w for w in r['data']['active_warnings']}
        self.assertEqual(active['大雨']['level'], 3)                       # 同要素取最高级别（警报 > 注意报）
        self.assertNotIn('雷', active)                                     # 已解除
        self.assertNotIn('土砂災害', active)                               # 另一个市町村（中央区）的注意报不计入该位置
        self.assertEqual([w['level'] for w in r['data']['active_warnings']], sorted((w['level'] for w in r['data']['active_warnings']), reverse=True))
        self.assertLessEqual(len(r['data']['outlook']['text_ja']), 1000)
        none = self.run_tool('warnings', place='100-0005', include_outlook=False)
        self.assertIsNone(none['data']['outlook'])

    def test_warnings_when_area_unknown(self):
        with mock.patch.object(J, 'office_for_municipality', return_value=(None, None, None)):
            self.assertEqual(self.run_tool('warnings', place='100-0005')['error']['code'], 'AREA_NOT_RESOLVED')

    def test_site_rain_risk_reads_tile_colours(self):
        r = self.run_tool('site_rain_risk', place='35.681,139.767')
        self.assertTrue(r['ok'], r)
        d = r['data']
        self.assertEqual(d['analysis_rainfall']['rate_zh'], '5～10 mm/h')
        levels = {x['index_zh']: x['level_zh'] for x in d['kikikuru']['layers']}
        self.assertIn('级别3', levels['表面雨量指数（大雨、内涝）'])
        self.assertEqual(levels['流域雨量指数（洪水）'], '级别1以下（无色）')      # 全透明 = 无值
        self.assertIn('级别4', levels['土壤雨量指数（土砂灾害）'])
        self.assertEqual(d['analysis_rainfall']['valid_time_jst'], '2026-07-10 14:20')  # UTC+9
        urls = [u for u in self.net.calls if u.endswith('.png')]
        self.assertEqual(len(urls), 4)
        self.assertTrue(all('/10/909/403.png' in u for u in urls))

    def test_site_rain_risk_weak_rain_colour_is_classified(self):
        with mock.patch.dict(TILES, {'hrpns': solid((242, 242, 255, 255))}):
            self.assertEqual(self.run_tool('site_rain_risk', place='35.681,139.767')['data']['analysis_rainfall']['rate_zh'], '0～1 mm/h（微弱降水）')

    def test_site_rain_risk_dry_tile_means_no_rain(self):
        with mock.patch.dict(TILES, {'hrpns': solid((0, 0, 0, 0))}):
            self.assertIn('无降水', self.run_tool('site_rain_risk', place='35.681,139.767')['data']['analysis_rainfall']['rate_zh'])

    def test_site_rain_risk_unsupported_tile_is_explicit(self):
        with mock.patch.dict(TILES, {'hrpns': png(2, 2, 6, 8, [bytes(8)] * 2, interlace=1)}):
            self.assertEqual(self.run_tool('site_rain_risk', place='35.681,139.767')['error']['code'], 'UNSUPPORTED_TILE_FORMAT')

    def test_wbgt_with_and_without_solar_correction(self):
        r = self.run_tool('wbgt', place='東京', days=2, times='8:30,13:00')
        self.assertTrue(r['ok'], r)
        self.assertTrue(r['data']['solar_correction_available'])
        today = [x for x in r['data']['days'] if x['date'] == '2026-07-10'][0]['values']
        base = J.wbgt_base(31.0, 60)
        by_time = {c['time']: c for c in today}
        self.assertAlmostEqual(by_time['08:30']['wbgt_estimate'], round(max(base, 25.0), 1), places=1)   # 官方 8:00 和 9:00 缺一个，只用 8:00=25.0
        self.assertTrue(by_time['13:00']['solar_correction_applied'])                                   # 官方 13:00=33.0 高于估算，被采用
        self.assertAlmostEqual(by_time['13:00']['wbgt_estimate'], 33.0, places=1)
        self.assertEqual(by_time['13:00']['rank_zh'], '危险')
        with mock.patch.object(J, 'official_wbgt', return_value={}):
            r2 = self.run_tool('wbgt', place='東京', days=1)
        self.assertFalse(r2['data']['solar_correction_available'])
        self.assertTrue(any('未做日射修正' in w for w in r2['warnings_zh']))
        self.assertAlmostEqual(r2['data']['days'][0]['values'][0]['wbgt_estimate'], round(base, 1), places=1)

    def test_wbgt_missing_observation_stays_null(self):
        with mock.patch.object(J, 'temp_humidity_at', return_value=(None, None)), mock.patch.object(J, 'official_wbgt', return_value={}):
            cells = self.run_tool('wbgt', place='東京', days=1)['data']['days'][0]['values']
        self.assertTrue(all(c['wbgt_estimate'] is None and c['rank_zh'] is None for c in cells))

    def test_every_result_carries_attribution_and_disclaimer(self):
        for name, args in (('locate', {'place': '100-0005'}), ('rainfall', {'place': '東京', 'days': 1}), ('warnings', {'place': '100-0005'}),
                           ('site_rain_risk', {'place': '東京'}), ('wbgt', {'place': '東京', 'days': 1})):
            r = self.run_tool(name, **args)
            self.assertTrue(r['ok'], (name, r))
            self.assertIn('气象厅', r['attribution_zh'])
            self.assertIn('编辑、加工', r['attribution_zh'])
            self.assertTrue(any('非官方' in w for w in r['warnings_zh']))

    def test_tool_cards_are_chinese_and_closed(self):
        self.assertEqual(sorted(J.TOOL_PREFIX + k for k in J.CATALOG), ['jma_locate', 'jma_rainfall', 'jma_site_rain_risk', 'jma_warnings', 'jma_wbgt'])
        for cls in J.TOOL_TYPES:
            tool = cls()
            self.assertTrue(any('一' <= ch <= '鿿' for ch in tool.card.description))
            self.assertFalse(tool.card.input_params['additionalProperties'])
        r = asyncio.run(J.TOOL_TYPES[1]().invoke({'place': '東京', 'days': 1}))
        self.assertTrue(r['ok'])


if __name__ == '__main__':
    unittest.main(verbosity=2)
