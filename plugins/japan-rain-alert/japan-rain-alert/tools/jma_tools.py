"""日本雨量预警助手：中文原生只读工具。

- 警报/注意报代码表、AMeDAS 观测点数据读取方式、1 km 网格色块读取与色阶表、WBGT 估算公式
  改编自 okura1234/claude-plugins 的 plugins/amedas-rain（MIT，Copyright (c) 2026 okura1234，
  固定提交 412612b0c1f2e6f000d9d287c2ed494730264d67，版本 1.3.1；完整许可文本见
  licenses/amedas-rain/LICENSE），已改为中文结构化输出、显式错误，并去掉 Pillow 依赖、
  磁盘缓存和默认地区，见 THIRD_PARTY_NOTICES.md。
- PNG 解码、参数校验、限流、内存缓存、预报区解析、错误处理为本团队独立编写。
- 数据来自气象厅、国土地理院、环境省热中症预防情报网站和 zipcloud 的公开接口，
  不使用账号，也不读取或保存任何凭据；本插件不向磁盘写入任何文件。
"""
from __future__ import annotations

import asyncio
from collections import OrderedDict, deque
from copy import deepcopy
import datetime
import json
import math
import re
import socket
import struct
import threading
import time
from typing import Any, AsyncIterator
import urllib.error
import urllib.parse
import urllib.request
import zlib

from openjiuwen.core.foundation.tool import Tool, ToolCard

JMA = "https://www.jma.go.jp/bosai"
AMEDAS_DATA = JMA + "/amedas/data"
AMEDAS_TABLE = JMA + "/amedas/const/amedastable.json"
AREA_JSON = JMA + "/common/const/area.json"
WARNING_URL = JMA + "/warning/data/r8/{office}.json"
OVERVIEW_URL = JMA + "/forecast/data/overview_forecast/{office}.json"
NOWC_TIMES = JMA + "/jmatile/data/nowc/targetTimes_N1.json"
RISK_TIMES = JMA + "/jmatile/data/risk/targetTimes.json"
NOWC_TILE = JMA + "/jmatile/data/nowc/{base}/none/{valid}/surf/hrpns/{z}/{x}/{y}.png"
RISK_TILE = JMA + "/jmatile/data/risk/{base}/{member}/{valid}/surf/{element}/{z}/{x}/{y}.png"
GSI_SEARCH = "https://msearch.gsi.go.jp/address-search/AddressSearch?q="
GSI_REVERSE = "https://mreversegeocoder.gsi.go.jp/reverse-geocoder/LonLatToAddress?lon={lon}&lat={lat}"
ZIPCLOUD = "https://zipcloud.ibsnet.co.jp/api/search?zipcode="
ENV_CSV = "https://www.wbgt.env.go.jp/est15WG/dl/wbgt_{code}_{ym}.csv"

USER_AGENT = "japan-rain-alert-agentic-hub/1.0.0"
TIMEOUT_SECONDS = 20
MAX_JSON_BYTES = 8 * 1024 * 1024
MAX_TILE_BYTES = 512 * 1024
CACHE_SECONDS = 300
LONG_CACHE_SECONDS = 86400
CACHE_ENTRIES = 256
TILE_ZOOM = 10  # 上游实测 z12 为空瓦片，固定 z10。
JST = datetime.timezone(datetime.timedelta(hours=9))
WD_ZH = "一二三四五六日"

# 日本国土范围（含离岛）的粗略外框，超出时直接拒绝，避免对境外坐标给出"无降水"的假结论。
LAT_RANGE = (20.0, 46.5)
LON_RANGE = (122.0, 154.5)

ATTRIBUTION_ZH = ("数据来源：出典：气象厅网站（jma.go.jp）；国土地理院网站（地名检索与逆地理编码）；"
                  "环境省热中症预防情报网站（wbgt.env.go.jp，仅用于暑热指数日射修正）；邮编转换使用 zipcloud。"
                  "以上内容经本插件编辑、加工后呈现，并非气象厅、国土地理院或环境省发布的内容。")
DISCLAIMER_ZH = "本插件是非官方工具；速报值和估算值仅供参考，防灾、停工等决定请以气象厅发布的信息和现场实测为准。"

# 府县预报区代码（上游 PREF 表）：当无法由 area.json 解析时的兜底，同时用于把"东京""大阪"等名称转成预报区。
PREF = {"北海道": "016000", "青森": "020000", "岩手": "030000", "宮城": "040000", "秋田": "050000", "山形": "060000", "福島": "070000",
        "茨城": "080000", "栃木": "090000", "群馬": "100000", "埼玉": "110000", "千葉": "120000", "東京": "130000", "神奈川": "140000",
        "新潟": "150000", "富山": "160000", "石川": "170000", "福井": "180000", "山梨": "190000", "長野": "200000", "岐阜": "210000",
        "静岡": "220000", "愛知": "230000", "三重": "240000", "滋賀": "250000", "京都": "260000", "大阪": "270000", "兵庫": "280000",
        "奈良": "290000", "和歌山": "300000", "鳥取": "310000", "島根": "320000", "岡山": "330000", "広島": "340000", "山口": "350000",
        "徳島": "360000", "香川": "370000", "愛媛": "380000", "高知": "390000",
        "長崎": "420000", "佐賀": "410000", "福岡": "400000", "熊本": "430000",
        "大分": "440000", "宮崎": "450000", "鹿児島": "460100", "沖縄": "471000"}

# 本插件新增（独立编写）：都道府县 -> (府县厅所在地观测站代码, 站名)。
# 直接用县名去地名检索会命中同名的市（如“沖縄”命中沖縄市），而不少站名在多个县重名（如“山形”“山口”“大津”），
# 所以县名一律按府县厅所在地的观测站处理并在结果里说明。代码已逐一核实：每个观测站坐标经国土地理院逆地理编码都落在对应都道府县内。
PREFECTURE_STATIONS = {
    "北海道": ("14163", "札幌"),
    "青森": ("31312", "青森"),
    "岩手": ("33431", "盛岡"),
    "宮城": ("34392", "仙台"),
    "秋田": ("32402", "秋田"),
    "山形": ("35426", "山形"),
    "福島": ("36127", "福島"),
    "茨城": ("40201", "水戸"),
    "栃木": ("41277", "宇都宮"),
    "群馬": ("42251", "前橋"),
    "埼玉": ("43241", "さいたま"),
    "千葉": ("45212", "千葉"),
    "東京": ("44132", "東京"),
    "神奈川": ("46106", "横浜"),
    "新潟": ("54232", "新潟"),
    "富山": ("55102", "富山"),
    "石川": ("56227", "金沢"),
    "福井": ("57066", "福井"),
    "山梨": ("49142", "甲府"),
    "長野": ("48156", "長野"),
    "岐阜": ("52586", "岐阜"),
    "静岡": ("50331", "静岡"),
    "愛知": ("51106", "名古屋"),
    "三重": ("53133", "津"),
    "滋賀": ("60216", "大津"),
    "京都": ("61286", "京都"),
    "大阪": ("62078", "大阪"),
    "兵庫": ("63518", "神戸"),
    "奈良": ("64036", "奈良"),
    "和歌山": ("65042", "和歌山"),
    "鳥取": ("69122", "鳥取"),
    "島根": ("68132", "松江"),
    "岡山": ("66408", "岡山"),
    "広島": ("67437", "広島"),
    "山口": ("81286", "山口"),
    "徳島": ("71106", "徳島"),
    "香川": ("72086", "高松"),
    "愛媛": ("73166", "松山"),
    "高知": ("74182", "高知"),
    "福岡": ("82182", "福岡"),
    "佐賀": ("85142", "佐賀"),
    "長崎": ("84496", "長崎"),
    "熊本": ("86141", "熊本"),
    "大分": ("83216", "大分"),
    "宮崎": ("87376", "宮崎"),
    "鹿児島": ("88317", "鹿児島"),
    "沖縄": ("91197", "那覇"),
}
# 简体中文都道府县名 -> 日文（日文写法与简体相同的不必列出）。
ZH_PREFECTURES = {"宫城": "宮城", "福岛": "福島", "枥木": "栃木", "群马": "群馬", "千叶": "千葉", "东京": "東京", "新泻": "新潟", "长野": "長野", "静冈": "静岡", "滋贺": "滋賀", "兵库": "兵庫", "鸟取": "鳥取", "岛根": "島根", "冈山": "岡山", "广岛": "広島", "德岛": "徳島", "爱知": "愛知", "爱媛": "愛媛", "福冈": "福岡", "佐贺": "佐賀", "长崎": "長崎", "宫崎": "宮崎", "鹿儿岛": "鹿児島", "冲绳": "沖縄"}
PREFECTURE_SUFFIXES = ("都", "府", "県", "县")


def prefecture_station(raw: str) -> tuple[str, str, str | None] | None:
    """都道府县名（日文或简体中文，可带 都/府/県/县）-> (观测站代码, 站名, 说明)；不是都道府县名返回 None。"""
    name = raw.strip()
    candidates = [name]
    if name and name[-1] in PREFECTURE_SUFFIXES and len(name) > 1:
        candidates.append(name[:-1])
    for candidate in candidates:
        ja = ZH_PREFECTURES.get(candidate, candidate)
        if ja in PREFECTURE_STATIONS:
            code, capital = PREFECTURE_STATIONS[ja]
            note = None if raw.strip() == capital else f"“{raw.strip()}”是都道府县名，已按府县厅所在地的观测站“{capital}”处理；要查府县内其他地点，请提供邮编、地址或经纬度。"
            return code, capital, note
    return None


# 常用城市的简体中文写法 -> 日文（独立编写）。
ZH_CITIES = {"那霸": "那覇", "横滨": "横浜", "神户": "神戸", "金泽": "金沢", "名古屋": "名古屋", "札幌": "札幌", "仙台": "仙台", "川崎": "川崎",
             "北九州": "北九州", "冈山": "岡山", "静冈": "静岡", "新泻": "新潟"}

# 警报/注意报代码 -> (要素, 要素中文, 级别, 日文名称)。上游 WARN_CODES（气象厅 2026-05-29 新防灾气象信息体系），中文要素名为本插件新增。
WARN_CODES = {
    "33": ("大雨", "大雨", 5, "レベル5大雨特別警報"), "43": ("大雨", "大雨", 4, "レベル4大雨危険警報"),
    "03": ("大雨", "大雨", 3, "レベル3大雨警報"), "10": ("大雨", "大雨", 2, "レベル2大雨注意報"),
    "39": ("土砂災害", "土砂灾害", 5, "レベル5土砂災害特別警報"), "49": ("土砂災害", "土砂灾害", 4, "レベル4土砂災害危険警報"),
    "09": ("土砂災害", "土砂灾害", 3, "レベル3土砂災害警報"), "29": ("土砂災害", "土砂灾害", 2, "レベル2土砂災害注意報"),
    "38": ("高潮", "风暴潮", 5, "レベル5高潮特別警報"), "48": ("高潮", "风暴潮", 4, "レベル4高潮危険警報"),
    "08": ("高潮", "风暴潮", 3, "レベル3高潮警報"), "19": ("高潮", "风暴潮", 2, "レベル2高潮注意報"),
    "35": ("暴風", "暴风", 5, "暴風特別警報"), "05": ("暴風", "暴风", 3, "暴風警報"), "15": ("暴風", "暴风", 2, "強風注意報"),
    "32": ("暴風雪", "暴风雪", 5, "暴風雪特別警報"), "02": ("暴風雪", "暴风雪", 3, "暴風雪警報"), "13": ("暴風雪", "暴风雪", 2, "風雪注意報"),
    "36": ("大雪", "大雪", 5, "大雪特別警報"), "06": ("大雪", "大雪", 3, "大雪警報"), "12": ("大雪", "大雪", 2, "大雪注意報"),
    "37": ("波浪", "海浪", 5, "波浪特別警報"), "07": ("波浪", "海浪", 3, "波浪警報"), "16": ("波浪", "海浪", 2, "波浪注意報"),
    "14": ("雷", "雷电", 2, "雷注意報"), "17": ("融雪", "融雪", 2, "融雪注意報"), "20": ("濃霧", "浓雾", 2, "濃霧注意報"),
    "21": ("乾燥", "干燥", 2, "乾燥注意報"), "22": ("なだれ", "雪崩", 2, "なだれ注意報"), "23": ("低温", "低温", 2, "低温注意報"),
    "24": ("霜", "霜冻", 2, "霜注意報"), "25": ("着氷", "积冰", 2, "着氷注意報"), "26": ("着雪", "着雪", 2, "着雪注意報"),
}
LEVEL_ZH = {2: "注意报级", 3: "警报级", 4: "危险警报级", 5: "特别警报级"}

# 解析雨量色块 -> mm/h 档位；キキクル（危险度分布）色块 -> 警戒级别。均为上游色阶表。
# 最弱一档 (242,242,255) 不在上游色阶表中：它是实时瓦片里大片弱降水区的主色，内部嵌套 (160,210,255) 和 (33,140,255) 等更强的档位，
# 与其余七档构成由弱到强的连续色阶，据此归为 0～1 mm/h；气象厅图例原文未在本次核对中取得，见 SOURCE_REVIEW.md。
PRECIP_COLORS = [((242, 242, 255), "0～1 mm/h（微弱降水）"), ((160, 210, 255), "1～5 mm/h"), ((33, 140, 255), "5～10 mm/h"), ((0, 65, 255), "10～20 mm/h"),
                 ((250, 245, 0), "20～30 mm/h"), ((255, 153, 0), "30～50 mm/h"), ((255, 40, 0), "50～80 mm/h"),
                 ((180, 0, 104), "80 mm/h 以上")]
KIKI_COLORS = [((242, 231, 0), "级别2 注意（黄）"), ((255, 40, 0), "级别3 警戒（红），相当于警报级"),
               ((170, 0, 255), "级别4 非常危险（紫），相当于危险警报级"), ((12, 0, 64), "级别5 极其危险（黑紫），相当于特别警报级")]
KIKI_LAYERS = (("rain_mesh", "表面雨量指数（大雨、内涝）"), ("flood_mesh", "流域雨量指数（洪水）"), ("land", "土壤雨量指数（土砂灾害）"))


# ---------------------------------------------------------------- 错误、限流、缓存

class SourceError(Exception):
    def __init__(self, code: str, message: str, **details: Any) -> None:
        super().__init__(message)
        self.code, self.message, self.details = code, message, details


def error(code: str, message: str, **details: Any) -> dict:
    return {"ok": False, "error": {"code": code, "message": message, **details}}


class Limiter:
    """进程内限流：保证最小间隔，也不超过每分钟上限；超限时直接报错，不自动重试。"""

    def __init__(self, min_interval: float, per_minute: int) -> None:
        self.min_interval, self.per_minute = min_interval, per_minute
        self.stamps: deque[float] = deque()
        self.lock = threading.Lock()

    def acquire(self) -> None:
        with self.lock:
            now = time.monotonic()
            while self.stamps and now - self.stamps[0] >= 60:
                self.stamps.popleft()
            if len(self.stamps) >= self.per_minute:
                wait = max(1, math.ceil(60 - (now - self.stamps[0])))
                raise SourceError("RATE_LIMITED", f"已达到本插件对该数据源的每分钟请求上限（{self.per_minute} 次），为避免给公共服务造成负担未发出请求；请约 {wait} 秒后再查询。",
                                  retry_after_seconds=wait)
            if self.stamps and now - self.stamps[-1] < self.min_interval:
                time.sleep(self.min_interval - (now - self.stamps[-1]))
            self.stamps.append(time.monotonic())


LIMITERS = {"jma": Limiter(0.1, 150), "gsi": Limiter(0.5, 30), "zipcloud": Limiter(1.0, 10), "env": Limiter(0.5, 20)}
CACHE: "OrderedDict[str, tuple[float, float, Any]]" = OrderedDict()
CACHE_LOCK = threading.Lock()


def fetch(source: str, url: str, kind: str = "json", ttl: float | None = CACHE_SECONDS, limit: int = MAX_JSON_BYTES) -> Any:
    """读取公共数据源。kind: json / text / bytes。ttl 为 None 时不缓存（zipcloud 条款要求展示最新信息）。"""
    now = time.monotonic()
    if ttl:
        with CACHE_LOCK:
            hit = CACHE.get(url)
            if hit and now - hit[0] < hit[1]:
                CACHE.move_to_end(url)
                return deepcopy(hit[2])
    LIMITERS[source].acquire()
    request = urllib.request.Request(url, headers={"User-Agent": USER_AGENT, "Accept": "*/*"})
    try:
        with urllib.request.urlopen(request, timeout=TIMEOUT_SECONDS) as response:
            body = response.read(limit + 1)
    except urllib.error.HTTPError as exc:
        status = exc.code
        code, message = {403: ("ACCESS_DENIED", "数据源拒绝访问（HTTP 403）；不能据此认定没有数据。"),
                         404: ("NOT_FOUND", "数据源没有该时间或该地点的数据（HTTP 404）。"),
                         429: ("RATE_LIMITED", "数据源限流（HTTP 429）；请稍后再查，本插件不自动重试。")
                         }.get(status, ("HTTP_ERROR", f"数据源返回 HTTP {status}；本次未自动重试。"))
        raise SourceError(code, message, http_status=status, source=source) from None
    except (socket.timeout, TimeoutError):
        raise SourceError("TIMEOUT", "请求未在时限内完成；本次未自动重试。", source=source) from None
    except urllib.error.URLError as exc:
        if isinstance(exc.reason, (socket.timeout, TimeoutError)):
            raise SourceError("TIMEOUT", "请求未在时限内完成；本次未自动重试。", source=source) from None
        raise SourceError("CONNECTION_FAILED", "无法连接数据源；请检查网络或数据源状态，本次未自动重试。", source=source) from None
    except OSError:
        raise SourceError("CONNECTION_FAILED", "无法连接数据源；请检查网络或数据源状态，本次未自动重试。", source=source) from None
    if len(body) > limit:
        raise SourceError("RESPONSE_TOO_LARGE", "数据源响应过大；请缩小范围，本次不截断或编造结果。", source=source)
    try:
        if kind == "json":
            data: Any = json.loads(body.decode("utf-8-sig"))
        elif kind == "text":
            data = body.decode("utf-8-sig").strip()
        else:
            data = body
    except (ValueError, UnicodeDecodeError):
        raise SourceError("UPSTREAM_FORMAT_ERROR", "数据源返回的内容无法解析；不能把响应当作已验证数据。", source=source) from None
    if ttl:
        with CACHE_LOCK:
            CACHE[url] = (time.monotonic(), ttl, deepcopy(data))
            while len(CACHE) > CACHE_ENTRIES:
                CACHE.popitem(last=False)
    return data


# ---------------------------------------------------------------- 独立编写的 PNG 解码（替代 Pillow）

def decode_png(data: bytes, max_pixels: int = 1024 * 1024) -> tuple[int, int, bytes]:
    """解码非交错 PNG，返回 (宽, 高, RGBA 字节)。支持色彩类型 0/2/3/4/6；不支持交错和 16 位，遇到时显式报错。"""
    if data[:8] != b"\x89PNG\r\n\x1a\n":
        raise SourceError("UPSTREAM_FORMAT_ERROR", "地图瓦片不是 PNG 图像。")
    pos, ihdr, palette, trns, idat = 8, None, b"", b"", []
    while pos + 8 <= len(data):
        length, kind = struct.unpack(">I4s", data[pos:pos + 8])
        chunk = data[pos + 8:pos + 8 + length]
        if len(chunk) != length:
            raise SourceError("UPSTREAM_FORMAT_ERROR", "PNG 数据被截断。")
        pos += 12 + length
        if kind == b"IHDR":
            ihdr = struct.unpack(">IIBBBBB", chunk)
        elif kind == b"PLTE":
            palette = chunk
        elif kind == b"tRNS":
            trns = chunk
        elif kind == b"IDAT":
            idat.append(chunk)
        elif kind == b"IEND":
            break
    if not ihdr or not idat:
        raise SourceError("UPSTREAM_FORMAT_ERROR", "PNG 缺少必要数据块。")
    width, height, depth, ctype, comp, filt, interlace = ihdr
    if interlace != 0 or comp != 0 or filt != 0:
        raise SourceError("UNSUPPORTED_TILE_FORMAT", "地图瓦片使用了本插件不支持的 PNG 交错格式，无法读取色块。")
    channels = {0: 1, 2: 3, 3: 1, 4: 2, 6: 4}.get(ctype)
    if channels is None or (ctype == 3 and depth not in (1, 2, 4, 8)) or (ctype != 3 and depth != 8):
        raise SourceError("UNSUPPORTED_TILE_FORMAT", "地图瓦片使用了本插件不支持的 PNG 色彩格式，无法读取色块。")
    if width <= 0 or height <= 0 or width * height > max_pixels:
        raise SourceError("UPSTREAM_FORMAT_ERROR", "地图瓦片尺寸异常。")
    bits = channels * depth
    stride = (width * bits + 7) // 8
    expected = (stride + 1) * height
    try:
        decomp = zlib.decompressobj()
        raw = decomp.decompress(b"".join(idat), expected + 1)
    except zlib.error:
        raise SourceError("UPSTREAM_FORMAT_ERROR", "PNG 压缩数据损坏。") from None
    if len(raw) != expected:
        raise SourceError("UPSTREAM_FORMAT_ERROR", "PNG 像素数据长度与尺寸不符。")
    bpp = max(1, bits // 8)
    rows: list[bytearray] = []
    prev = bytearray(stride)
    for y in range(height):
        start = y * (stride + 1)
        ftype, line = raw[start], bytearray(raw[start + 1:start + 1 + stride])
        if ftype == 1:
            for i in range(bpp, stride):
                line[i] = (line[i] + line[i - bpp]) & 255
        elif ftype == 2:
            for i in range(stride):
                line[i] = (line[i] + prev[i]) & 255
        elif ftype == 3:
            for i in range(stride):
                left = line[i - bpp] if i >= bpp else 0
                line[i] = (line[i] + ((left + prev[i]) >> 1)) & 255
        elif ftype == 4:
            for i in range(stride):
                a = line[i - bpp] if i >= bpp else 0
                b = prev[i]
                c = prev[i - bpp] if i >= bpp else 0
                p = a + b - c
                pa, pb, pc = abs(p - a), abs(p - b), abs(p - c)
                pred = a if pa <= pb and pa <= pc else (b if pb <= pc else c)
                line[i] = (line[i] + pred) & 255
        elif ftype != 0:
            raise SourceError("UPSTREAM_FORMAT_ERROR", "PNG 行过滤类型无效。")
        rows.append(line)
        prev = line
    out = bytearray(width * height * 4)
    o = 0
    mask = (1 << depth) - 1
    for line in rows:
        for x in range(width):
            if ctype == 6:
                r, g, b, a = line[4 * x:4 * x + 4]
            elif ctype == 2:
                r, g, b = line[3 * x:3 * x + 3]
                a = 255
            elif ctype == 0:
                r = g = b = line[x]
                a = 255
            elif ctype == 4:
                r = g = b = line[2 * x]
                a = line[2 * x + 1]
            else:
                bit = x * depth
                idx = (line[bit >> 3] >> (8 - depth - (bit & 7))) & mask
                if idx * 3 + 3 > len(palette):
                    raise SourceError("UPSTREAM_FORMAT_ERROR", "PNG 调色板索引越界。")
                r, g, b = palette[idx * 3:idx * 3 + 3]
                a = trns[idx] if idx < len(trns) else 255
            out[o:o + 4] = bytes((r, g, b, a))
            o += 4
    return width, height, bytes(out)


# ---------------------------------------------------------------- 地理与观测站

def parse_zip(text: str) -> str | None:
    m = re.fullmatch(r"〒?\s*(\d{3})\s*[-－ー‐]?\s*(\d{4})", text.strip())
    return m.group(1) + m.group(2) if m else None


def parse_latlon(text: str) -> tuple[float, float] | None:
    m = re.fullmatch(r"\s*(-?\d{1,2}(?:\.\d+)?)\s*[,，]\s*(-?\d{1,3}(?:\.\d+)?)\s*", text)
    return (float(m.group(1)), float(m.group(2))) if m else None


def station_table() -> dict:
    data = fetch("jma", AMEDAS_TABLE, ttl=LONG_CACHE_SECONDS)
    if not isinstance(data, dict) or not data:
        raise SourceError("UPSTREAM_FORMAT_ERROR", "观测站表的结构与预期不符；不能当作已验证数据。")
    return data


def station_coords(entry: dict) -> tuple[float, float]:
    return entry["lat"][0] + entry["lat"][1] / 60, entry["lon"][0] + entry["lon"][1] / 60


def distance_km(lat1: float, lon1: float, lat2: float, lon2: float) -> float:
    return math.hypot((lat2 - lat1) * 111, (lon2 - lon1) * 111 * math.cos(math.radians(lat1)))


def has_rain_gauge(entry: dict) -> bool:
    elems = str(entry.get("elems", ""))
    return len(elems) >= 2 and elems[1] == "1"


def has_temp_humidity(entry: dict) -> bool:
    elems = str(entry.get("elems", ""))
    return len(elems) >= 6 and elems[0] == "1" and elems[5] == "1"


def nearest_station(lat: float, lon: float, accept) -> dict | None:
    best = None
    for code, entry in station_table().items():
        if not accept(entry):
            continue
        la, lo = station_coords(entry)
        d = distance_km(lat, lon, la, lo)
        if best is None or d < best["distance_km"]:
            best = {"code": code, "name": entry.get("kjName", ""), "kana": entry.get("knName", ""), "distance_km": round(d, 1)}
    return best


def find_stations(text: str) -> list[tuple[str, str, str]]:
    hits = []
    for code, entry in station_table().items():
        kj, kn = entry.get("kjName") or "", entry.get("knName") or ""
        if text in kj or text in kn:
            hits.append((code, kj, kn))
    return hits


def geocode(address: str) -> tuple[float, float, str] | None:
    data = fetch("gsi", GSI_SEARCH + urllib.parse.quote(address))
    if not isinstance(data, list):
        raise SourceError("UPSTREAM_FORMAT_ERROR", "国土地理院地名检索返回的结构与预期不符。")
    if not data:
        return None
    try:
        lon, lat = data[0]["geometry"]["coordinates"]
        title = (data[0].get("properties") or {}).get("title") or address
    except (KeyError, TypeError, ValueError):
        raise SourceError("UPSTREAM_FORMAT_ERROR", "国土地理院地名检索返回的结构与预期不符。") from None
    return float(lat), float(lon), str(title)


def reverse_municipality(lat: float, lon: float) -> str | None:
    try:
        data = fetch("gsi", GSI_REVERSE.format(lon=lon, lat=lat))
    except SourceError as exc:
        if exc.code == "RATE_LIMITED":
            raise  # 限流不能被当作“查不到市町村”悄悄吞掉
        return None
    code = ((data or {}).get("results") or {}).get("muniCd") if isinstance(data, dict) else None
    return str(code) if code else None


def office_for_municipality(muni: str | None) -> tuple[str | None, str | None, str | None]:
    """市町村代码（5 位）-> (预报区代码, 预报区名, 市町村名)；沿用 area.json 的 class20 -> class15 -> class10 -> offices 层级。"""
    if not muni:
        return None, None, None
    try:
        area = fetch("jma", AREA_JSON, ttl=LONG_CACHE_SECONDS)
        classes = area["class20s"]
        keys = [k for k in classes if k.startswith(muni)] or [k for k in classes if k.startswith(muni[:3] + "00")]
        if not keys:
            return None, None, None
        key = sorted(keys)[0]
        node = classes[key]
        muni_name = node.get("name")
        for table in ("class15s", "class10s"):
            node = area[table][node["parent"]]
        office = node["parent"]
        return office, area["offices"][office].get("name"), muni_name
    except (KeyError, TypeError):
        return None, None, None


def resolve_location(place: str) -> dict:
    """把邮编 / 经纬度 / 地址 / 观测站名解析成坐标，并附市町村、预报区和最近的观测站。"""
    raw = place.strip()
    pref = prefecture_station(raw)
    if pref and pref[0] in station_table():
        loc = _station_location(pref[0], station_table()[pref[0]])
        loc["input"], loc["alias_note"] = place, pref[2]
        return loc
    alias_note = None
    text = ZH_CITIES.get(raw, raw)
    zipcode, latlon = parse_zip(text), parse_latlon(text)
    address = ""
    if zipcode:
        data = fetch("zipcloud", ZIPCLOUD + zipcode, ttl=None)
        results = data.get("results") if isinstance(data, dict) else None
        if not results:
            raise SourceError("PLACE_NOT_FOUND", f"zipcloud 查不到邮编 {zipcode[:3]}-{zipcode[3:]}；请核对邮编，或改用地址、经纬度。")
        item = results[0]
        address = f"{item.get('address1', '')}{item.get('address2', '')}{item.get('address3', '')}"
        found = geocode(address)
        if not found:
            raise SourceError("PLACE_NOT_FOUND", f"国土地理院查不到该邮编对应地址的坐标：{address}；请改用经纬度。")
        lat, lon, _ = found
        kind, label = "postal_code", f"〒{zipcode[:3]}-{zipcode[3:]} {address}"
    elif latlon:
        lat, lon = latlon
        kind, label = "coordinates", f"坐标 {lat}, {lon}"
    else:
        hits = find_stations(text)
        exact = [h for h in hits if h[1] == text]
        chosen = hits[0] if len(hits) == 1 else (exact[0] if len(exact) == 1 else None)
        if hits and chosen is None:
            raise SourceError("AMBIGUOUS_PLACE", f"“{place}”匹配到 {len(hits)} 个观测站，请换更完整的地名、邮编或经纬度，或用 station_code 指定。",
                              candidates=[{"code": c, "name": kj, "kana": kn} for c, kj, kn in hits[:20]])
        if chosen:
            entry = station_table()[chosen[0]]
            lat, lon = station_coords(entry)
            kind, label, address = "station", f"观测站 {chosen[1]}（{chosen[0]}）", chosen[1]
        else:
            found = geocode(text)
            if not found:
                raise SourceError("PLACE_NOT_FOUND", f"没有找到“{place}”；请改用日语地名/地址、邮编（如 100-0005）或经纬度（如 35.681,139.767）。")
            lat, lon, address = found
            kind, label = "address", f"地址 {address}"
    if not (LAT_RANGE[0] <= lat <= LAT_RANGE[1] and LON_RANGE[0] <= lon <= LON_RANGE[1]):
        raise SourceError("OUT_OF_COVERAGE", "该位置在日本以外，气象厅的雨量、警报和 1 km 网格数据不覆盖，未给出任何结果。")
    muni = reverse_municipality(lat, lon)
    office, office_name, muni_name = office_for_municipality(muni)
    return {"input": place, "kind": kind, "label": label, "address": address, "lat": round(lat, 5), "lon": round(lon, 5),
            "municipality_code": muni, "municipality_name": muni_name, "forecast_office_code": office, "forecast_office_name": office_name,
            "rain_station": nearest_station(lat, lon, has_rain_gauge), "temp_humidity_station": nearest_station(lat, lon, has_temp_humidity),
            "alias_note": alias_note}


def precision_note(kind: str) -> str:
    return {"coordinates": "坐标定位：1 km 网格即该坐标正上方。", "postal_code": "邮编定位：以邮编对应地址的代表点为准，同一邮编内相距较远的地点可能落在不同网格。",
            "address": "地址定位：以地名检索返回的代表点为准。", "station": "观测站定位：以该观测站坐标为准。"}[kind]


def location_notes(loc: dict) -> list[str]:
    notes = [precision_note(loc["kind"])]
    if loc.get("alias_note"):
        notes.append(loc["alias_note"])
    return notes


# ---------------------------------------------------------------- 通用工具

def now_jst() -> datetime.datetime:
    return datetime.datetime.fromisoformat(fetch("jma", AMEDAS_DATA + "/latest_time.txt", kind="text", ttl=60))


def value_of(item: Any) -> Any:
    return None if (not isinstance(item, list) or not item or item[0] is None) else item[0]


def result_envelope(tool: str, arguments: dict, data: Any, summary: list[str], warnings: list[str]) -> dict:
    return {"ok": True, "tool": tool, "retrieved_at_utc": datetime.datetime.now(datetime.timezone.utc).isoformat(), "arguments": arguments,
            "message": "已取得数据源实际返回；请用简体中文整理，保留日文地名、观测站名和警报名称的原写法，缺失值写“未取得”，不得写成零。",
            "summary_zh": summary, "data": data, "attribution_zh": ATTRIBUTION_ZH, "warnings_zh": warnings + [DISCLAIMER_ZH]}


def location_from(a: dict) -> dict:
    """place 或 station_code -> 位置。"""
    if a.get("station_code"):
        code = a["station_code"]
        entry = station_table().get(code)
        if not entry:
            raise SourceError("PLACE_NOT_FOUND", f"没有观测站代码 {code}；可先用 jma_locate 查询。")
        return _station_location(code, entry)
    if not a.get("place"):
        raise SourceError("INVALID_ARGUMENTS", "请提供 place（邮编、地址、经纬度或观测站名）或 station_code。")
    return resolve_location(a["place"])


def _station_location(code: str, entry: dict) -> dict:
    lat, lon = station_coords(entry)
    muni = reverse_municipality(lat, lon)
    office, office_name, muni_name = office_for_municipality(muni)
    name = entry.get("kjName", code)
    return {"input": code, "kind": "station", "label": f"观测站 {name}（{code}）", "address": name, "lat": round(lat, 5), "lon": round(lon, 5), "alias_note": None,
            "municipality_code": muni, "municipality_name": muni_name, "forecast_office_code": office, "forecast_office_name": office_name,
            "rain_station": {"code": code, "name": name, "kana": entry.get("knName", ""),
                             "distance_km": 0.0} if has_rain_gauge(entry) else nearest_station(lat, lon, has_rain_gauge),
            "temp_humidity_station": {"code": code, "name": name, "kana": entry.get("knName", ""),
                                      "distance_km": 0.0} if has_temp_humidity(entry) else nearest_station(lat, lon, has_temp_humidity)}


# ---------------------------------------------------------------- 工具实现

def tool_locate(a: dict) -> dict:
    loc = resolve_location(a["place"])
    warnings = location_notes(loc)
    if not loc["municipality_code"]:
        warnings.append("未能取得市町村代码，警报查询可能无法定位到具体市町村。")
    summary = [f"{loc['label']}（{loc['lat']}, {loc['lon']}）"]
    if loc["rain_station"]:
        summary.append(f"最近的有雨量计的 AMeDAS 观测站：{loc['rain_station']['name']}（{loc['rain_station']['code']}），约 {loc['rain_station']['distance_km']} km。")
    if loc["forecast_office_name"]:
        summary.append(f"所属预报区：{loc['forecast_office_name']}（{loc['forecast_office_code']}）。")
    return result_envelope("jma_locate", a, loc, summary, warnings)


def collect_10min(code: str, start: datetime.datetime, end: datetime.datetime) -> tuple[dict, int, int]:
    data: dict[str, float] = {}
    day, missing, blocks = start.date(), 0, 0
    while day <= end.date():
        for hour in range(0, 24, 3):
            if datetime.datetime.combine(day, datetime.time(hour), tzinfo=JST) > end:
                break
            blocks += 1
            try:
                block = fetch("jma", f"{AMEDAS_DATA}/point/{code}/{day:%Y%m%d}_{hour:02d}.json")
            except SourceError as exc:
                if exc.code == "NOT_FOUND":
                    missing += 1
                    continue
                raise
            if not isinstance(block, dict):
                raise SourceError("UPSTREAM_FORMAT_ERROR", "观测点数据的结构与预期不符；不能当作已验证数据。")
            for stamp, record in block.items():
                p = value_of((record or {}).get("precipitation10m"))
                if p is not None:
                    data[stamp] = p
        day += datetime.timedelta(days=1)
    return data, missing, blocks


def tool_rainfall(a: dict) -> dict:
    loc = location_from(a)
    station = loc["rain_station"]
    if not station:
        raise SourceError("NO_STATION", "附近没有找到带雨量计的观测站。")
    days = a.get("days", 4)
    now = now_jst()
    latest = None
    for hour_shift in (0, 3):
        probe = now - datetime.timedelta(hours=hour_shift)
        try:
            block = fetch("jma", f"{AMEDAS_DATA}/point/{station['code']}/{probe:%Y%m%d}_{(probe.hour // 3) * 3:02d}.json")
        except SourceError as exc:
            if exc.code == "NOT_FOUND":
                continue
            raise
        if isinstance(block, dict) and block:
            stamp = sorted(block)[-1]
            rec = block[stamp] or {}
            latest = {"observed_at_jst": f"{stamp[:4]}-{stamp[4:6]}-{stamp[6:8]} {stamp[8:10]}:{stamp[10:12]}",
                      "precipitation_10min_mm": value_of(rec.get("precipitation10m")), "precipitation_1h_mm": value_of(rec.get("precipitation1h")),
                      "precipitation_24h_mm": value_of(rec.get("precipitation24h"))}
            break
    start = (now - datetime.timedelta(days=days - 1)).replace(hour=0, minute=0, second=0, microsecond=0)
    series, missing, blocks = collect_10min(station["code"], start, now)
    if not series:
        raise SourceError("NO_DATA", "该观测站在所选期间没有取得任何 10 分钟降水量；不能据此认定没有降水。", station=station["name"])
    daily: dict[str, float] = {}
    slots: dict[str, int] = {}
    for stamp, mm in series.items():
        daily[stamp[:8]] = daily.get(stamp[:8], 0.0) + mm
        slots[stamp[:8]] = slots.get(stamp[:8], 0) + 1
    rows = []
    for key in sorted(daily):
        d = datetime.datetime.strptime(key, "%Y%m%d")
        rows.append({"date": d.strftime("%Y-%m-%d"), "weekday": "周" + WD_ZH[d.weekday()], "total_mm": round(daily[key], 1), "slots_10min": slots[key],
                     "complete": slots[key] >= 140})
    warnings = location_notes(loc) + [
                "雨量取自最近的 AMeDAS 观测站（见 distance_km），不等于所查地点本身的降水量。",
                "日降水量由速报值 10 分钟降水量累加而成，与气象厅确定值可能相差数毫米；速报值只覆盖最近约 10 天。"]
    partial = [r["date"] for r in rows if not r["complete"]]
    if partial:
        warnings.append("以下日期的 10 分钟数据不足 140 格（当天未结束或有缺测），合计可能偏小，不能当作确定值：" + "、".join(partial) + "。")
    if missing:
        warnings.append(f"有 {missing}/{blocks} 个 3 小时数据块未取得，对应时段按缺测处理。")
    data = {"location": loc, "station": station, "latest_observation": latest, "daily": rows,
            "period_total_mm": round(sum(daily.values()), 1), "observation_latest_time_jst": now.strftime("%Y-%m-%d %H:%M")}
    summary = [f"{loc['label']}：最近的雨量观测站 {station['name']}（{station['code']}），约 {station['distance_km']} km。"]
    if latest:
        summary.append(f"最新 {latest['observed_at_jst']}：10 分钟 {latest['precipitation_10min_mm']} mm，1 小时 {latest['precipitation_1h_mm']} mm，24 小时累计 {latest['precipitation_24h_mm']} mm（None 表示未取得）。")
    summary.append(f"最近 {days} 天合计（速报值累加）：{data['period_total_mm']} mm。")
    return result_envelope("jma_rainfall", a, data, summary, warnings)


def tool_warnings(a: dict) -> dict:
    loc = location_from(a)
    office, muni = loc["forecast_office_code"], loc["municipality_code"]
    if not office or not muni:
        raise SourceError("AREA_NOT_RESOLVED", "没能把该位置对应到气象厅的预报区和市町村，无法查询警报；请改用日本境内的地址、邮编或经纬度。")
    area = fetch("jma", AREA_JSON, ttl=LONG_CACHE_SECONDS)
    classes = area.get("class20s", {}) if isinstance(area, dict) else {}
    codes = {k: v["name"] for k, v in classes.items() if k.startswith(muni)} or {k: v["name"] for k, v in classes.items() if k.startswith(muni[:3] + "00")}
    if not codes:
        raise SourceError("AREA_NOT_RESOLVED", "气象厅区域表中没有该市町村，无法查询警报。")
    data = fetch("jma", WARNING_URL.format(office=office))
    if not isinstance(data, list):
        raise SourceError("UPSTREAM_FORMAT_ERROR", "警报数据的结构与预期不符；不能当作已验证数据。")
    report, current = "未取得", {}
    for item_set in data:
        for item in (item_set.get("warning") or {}).get("class20Items", []):
            if item.get("areaCode") not in codes:
                continue
            stamp = item_set.get("reportDatetime", "")
            if stamp and (report == "未取得" or stamp > report):
                report = stamp
            for kind in item.get("kinds", []):
                meta = WARN_CODES.get(kind.get("code"))
                if not meta or kind.get("status") == "解除":
                    continue
                element, element_zh, level, name = meta
                if element not in current or level > current[element]["level"]:
                    current[element] = {"element_ja": element, "element_zh": element_zh, "level": level, "level_zh": LEVEL_ZH[level], "name_ja": name}
    active = sorted(current.values(), key=lambda v: -v["level"])
    outlook = None
    if a.get("include_outlook", True):
        try:
            ov = fetch("jma", OVERVIEW_URL.format(office=office))
            outlook = {"office": ov.get("publishingOffice"), "report_datetime": ov.get("reportDatetime"), "target_area": ov.get("targetArea"),
                       "text_ja": (ov.get("text") or "").strip()[:1000]}
        except SourceError as exc:
            outlook = {"error": exc.message}
    result = {"location": {k: loc[k] for k in ("label", "lat", "lon", "municipality_code", "municipality_name", "forecast_office_code", "forecast_office_name")},
              "warnings_report_datetime": report, "areas": list(codes.values()), "active_warnings": active, "outlook": outlook}
    summary = [f"{loc['label']}：{'、'.join(codes.values())}，{report} 发布的数据。"]
    summary.append("当前发布中：" + "；".join(f"{w['name_ja']}（{w['element_zh']}，{w['level_zh']}）" for w in active) if active else "当前没有发布中的警报或注意报。")
    warnings = location_notes(loc) + ["“气象台展望”原文为日语，请翻译概括，不要逐字改写成预测结论。",
                "本工具不预测警报何时解除；土壤雨量指数在降雨后仍会残留，新降雨还会改变情况。"]
    return result_envelope("jma_warnings", a, result, summary, warnings)


def tile_pixel_xy(lat: float, lon: float, z: int) -> tuple[int, int, int, int]:
    n = 2 ** z
    xt = (lon + 180) / 360 * n
    yt = (1 - math.asinh(math.tan(math.radians(lat))) / math.pi) / 2 * n
    tx, ty = int(xt), int(yt)
    return tx, ty, int((xt - tx) * 256), int((yt - ty) * 256)


def nearest_color(rgb: tuple, table: list, threshold: float = 70) -> str | None:
    best, bd = None, 1e9
    for color, label in table:
        d = sum((p - q) ** 2 for p, q in zip(rgb, color)) ** 0.5
        if d < bd:
            bd, best = d, label
    return best if bd <= threshold else None


def sample_tile(url_template: str, lat: float, lon: float) -> tuple | None:
    """返回该坐标 3x3 范围内出现最多的不透明颜色；全透明返回 None（表示该格没有值）。"""
    tx, ty, px, py = tile_pixel_xy(lat, lon, TILE_ZOOM)
    png = fetch("jma", url_template.format(z=TILE_ZOOM, x=tx, y=ty), kind="bytes", limit=MAX_TILE_BYTES)
    width, height, rgba = decode_png(png)
    px, py = min(px, width - 1), min(py, height - 1)
    counts: dict[tuple, int] = {}
    for dy in (-1, 0, 1):
        for dx in (-1, 0, 1):
            x, y = min(max(px + dx, 0), width - 1), min(max(py + dy, 0), height - 1)
            r, g, b, alpha = rgba[(y * width + x) * 4:(y * width + x) * 4 + 4]
            if alpha > 0:
                counts[(r, g, b)] = counts.get((r, g, b), 0) + 1
    return max(counts, key=counts.get) if counts else None


def jst_text(stamp: str) -> str:
    dt = datetime.datetime.strptime(stamp, "%Y%m%d%H%M%S") + datetime.timedelta(hours=9)
    return dt.strftime("%Y-%m-%d %H:%M")


def tool_site_rain_risk(a: dict) -> dict:
    loc = location_from(a)
    nowc = fetch("jma", NOWC_TIMES, ttl=60)
    risk = fetch("jma", RISK_TIMES, ttl=60)
    try:
        nowc, risk = nowc[0], risk[0]
        base_n, valid_n = nowc["basetime"], nowc["validtime"]
        base_r, member, valid_r = risk["basetime"], risk.get("member", "immed0"), risk["validtime"]
    except (KeyError, IndexError, TypeError):
        raise SourceError("UPSTREAM_FORMAT_ERROR", "瓦片时间表的结构与预期不符；不能当作已验证数据。") from None
    lat, lon = loc["lat"], loc["lon"]
    color = sample_tile(NOWC_TILE.format(base=base_n, valid=valid_n, z="{z}", x="{x}", y="{y}"), lat, lon)
    if color is None:
        rain = "无降水（该格没有降水色块）"
    else:
        rain = nearest_color(color, PRECIP_COLORS) or f"无法归类的颜色 {color}"
    layers = []
    for element, label in KIKI_LAYERS:
        color = sample_tile(RISK_TILE.format(base=base_r, member=member, valid=valid_r, element=element, z="{z}", x="{x}", y="{y}"), lat, lon)
        level = "级别1以下（无色）" if color is None else (nearest_color(color, KIKI_COLORS) or f"无法归类的颜色 {color}")
        layers.append({"index_zh": label, "level_zh": level})
    data = {"location": loc, "analysis_rainfall": {"valid_time_jst": jst_text(valid_n), "rate_zh": rain},
            "kikikuru": {"valid_time_jst": jst_text(valid_r), "layers": layers}, "tile_zoom": TILE_ZOOM}
    summary = [f"{loc['label']}（{lat}, {lon}）的 1 km 网格：解析雨量 {rain}（{jst_text(valid_n)} JST）。"]
    summary += [f"{x['index_zh']}：{x['level_zh']}（{jst_text(valid_r)} JST）。" for x in layers]
    warnings = location_notes(loc) + ["数值取自地图瓦片颜色，只能得到档位，不是精确数值，仅用于了解该位置的大致警戒程度。"]
    return result_envelope("jma_site_rain_risk", a, data, summary, warnings)


# ---- 暑热指数（WBGT）估算：上游公式，日射修正使用环境省官方实况 CSV（仅 4～10 月有数据）

def stull_wet_bulb(t: float, h: float) -> float:
    return (t * math.atan(0.151977 * math.sqrt(h + 8.313659)) + math.atan(t + h) - math.atan(h - 1.676331)
            + 0.00391838 * h ** 1.5 * math.atan(0.023101 * h) - 4.686035)


def wbgt_base(t: float | None, h: float | None) -> float | None:
    if t is None or h is None:
        return None
    return 0.7 * stull_wet_bulb(t, h) + 0.3 * t  # 黑球温度取气温时：0.7Tw + 0.2Ta + 0.1Ta


def wbgt_rank(v: float | None) -> str | None:
    if v is None:
        return None
    for limit, label in ((31, "危险"), (28, "严重警戒"), (25, "警戒"), (21, "注意")):
        if v >= limit:
            return label
    return "基本安全"


def official_wbgt(code: str, months: list[str]) -> dict:
    found: dict[tuple[str, str], float] = {}
    for ym in months:
        try:
            raw = fetch("env", ENV_CSV.format(code=code, ym=ym), kind="text")
        except SourceError:
            continue  # 该月无文件（运行期外）或站点无官方值：不做日射修正，并在结果中说明。
        for line in raw.splitlines()[1:]:
            parts = [x.strip() for x in line.split(",")]
            if len(parts) >= 3 and parts[2]:
                try:
                    found[(parts[0], parts[1])] = float(parts[2])
                except ValueError:
                    pass
    return found


def temp_humidity_at(code: str, day: datetime.date, hm: str) -> tuple[float | None, float | None]:
    hh, mm = hm.split(":")
    try:
        block = fetch("jma", f"{AMEDAS_DATA}/point/{code}/{day:%Y%m%d}_{(int(hh) // 3) * 3:02d}.json")
    except SourceError as exc:
        if exc.code == "NOT_FOUND":
            return None, None
        raise
    rec = (block or {}).get(f"{day:%Y%m%d}{int(hh):02d}{mm}00", {}) if isinstance(block, dict) else {}
    return value_of(rec.get("temp")), value_of(rec.get("humidity"))


def tool_wbgt(a: dict) -> dict:
    loc = location_from(a)
    th = loc["temp_humidity_station"]
    if not th:
        raise SourceError("NO_STATION", "附近没有找到同时观测气温和湿度的观测站。")
    days = a.get("days", 3)
    times = [x.strip() for x in a.get("times", "8:30,13:00").split(",") if x.strip()]
    now = now_jst()
    today = now.date()
    start = today - datetime.timedelta(days=days - 1)
    months = sorted({f"{(start + datetime.timedelta(days=i)).year}{(start + datetime.timedelta(days=i)).month:02d}" for i in range(days)})
    official = official_wbgt(th["code"], months)
    rows = []
    corrected = 0
    for i in range(days):
        day = start + datetime.timedelta(days=i)
        cells = []
        for tm in times:
            hh, mm = tm.split(":")
            hm = f"{int(hh):02d}:{mm}"
            ta, hu = temp_humidity_at(th["code"], day, hm)
            base = wbgt_base(ta, hu)
            est, applied = base, False
            if base is not None and official:
                h0, m0 = int(hh), int(mm)
                keys = [f"{h0}:00"] if m0 == 0 else [f"{h0}:00", f"{h0 + 1}:00"]
                day_key = f"{day.year}/{day.month}/{day.day}"
                vals = [official.get((day_key, k)) for k in keys]
                vals = [v for v in vals if v is not None]
                if vals:
                    est, applied = base + max(0.0, sum(vals) / len(vals) - base), True
                    corrected += 1
            cells.append({"time": hm, "temperature_c": ta, "humidity_pct": hu, "wbgt_estimate": None if est is None else round(est, 1),
                          "rank_zh": wbgt_rank(est), "solar_correction_applied": applied})
        rows.append({"date": day.strftime("%Y-%m-%d"), "weekday": "周" + WD_ZH[day.weekday()], "values": cells})
    note = None if official else "环境省官方实况文件（仅在每年 4 月下旬至 10 月下旬运行期有数据）当前不可用，未做日射修正；估算值相当于不含日照影响的下限，可能明显偏低。"
    data = {"location": loc, "station": th, "days": rows, "formula": "WBGT = 0.7×湿球温度 + 0.2×黑球温度 + 0.1×气温（黑球取气温，湿球用 Stull 近似），再用环境省官方实况做日射修正",
            "rank_bands_zh": "~21 基本安全；21~25 注意；25~28 警戒；28~31 严重警戒；31~ 危险", "solar_correction_available": bool(official)}
    summary = [f"{loc['label']}：气温和湿度取自 {th['name']}（{th['code']}），约 {th['distance_km']} km。",
               f"共估算 {sum(len(r['values']) for r in rows)} 个时刻，其中 {corrected} 个做了日射修正。"]
    warnings = location_notes(loc) + ["这是由观测站气温、湿度推算的估算值，不是所查地点本身的实测，也不是环境省发布的暑热指数；屋外作业的判断以带黑球的 WBGT 仪实测为准。"]
    if note:
        warnings.append(note)
    return result_envelope("jma_wbgt", a, data, summary, warnings)


# ---------------------------------------------------------------- 参数校验与工具目录

def check_value(name: str, spec: dict, value: Any) -> str | None:
    kind = spec.get("type")
    if kind == "integer":
        if isinstance(value, bool) or not isinstance(value, int):
            return f"{name} 必须是整数。"
        if "minimum" in spec and value < spec["minimum"] or "maximum" in spec and value > spec["maximum"]:
            return f"{name} 必须在 {spec.get('minimum')} 到 {spec.get('maximum')} 之间。"
    elif kind == "boolean":
        if not isinstance(value, bool):
            return f"{name} 必须是 true 或 false。"
    elif kind == "string":
        if not isinstance(value, str) or not value.strip():
            return f"{name} 必须是非空字符串。"
        if len(value) > spec.get("maxLength", 80):
            return f"{name} 过长。"
        if "pattern" in spec and not re.fullmatch(spec["pattern"], value.strip()):
            return f"{name} 格式不符合要求：{spec.get('patternHint', spec['pattern'])}"
    return None


def validate(tool: str, arguments: Any) -> tuple[dict | None, str | None]:
    if not isinstance(arguments, dict):
        return None, "参数必须是 JSON 对象，并直接传入字段，不要套 arguments。"
    schema = CATALOG[tool]["schema"]
    props = schema["properties"]
    unknown = sorted(set(arguments) - set(props))
    if unknown:
        return None, "存在未定义的参数：" + "、".join(unknown) + "。"
    values: dict[str, Any] = {}
    for key, value in arguments.items():
        if value is None:
            continue
        problem = check_value(key, props[key], value)
        if problem:
            return None, problem
        values[key] = value.strip() if isinstance(value, str) else value
    missing = [k for k in schema.get("required", []) if k not in values]
    if missing:
        return None, "缺少必填参数：" + "、".join(missing) + "。"
    return values, None


def schema(props: dict, required: list[str] | None = None) -> dict:
    return {"type": "object", "additionalProperties": False, "properties": props, **({"required": required} if required else {})}


PLACE = {"type": "string", "maxLength": 120,
         "description": "日本境内的位置：邮编（如 100-0005）、地址（如 長野県松本市丸の内3）、经纬度（如 35.681,139.767）或观测站名（如 東京）。地名请尽量用日语；都道府县名（日文或简体中文，如“冲绳”“東京都”）按府县厅所在地的观测站处理，结果会说明。"}
STATION = {"type": "string", "maxLength": 8, "pattern": r"\d{4,6}", "patternHint": "气象厅 AMeDAS 观测站代码，纯数字，如 44132。", "description": "AMeDAS 观测站代码；与 place 二选一。"}

CATALOG: dict[str, dict] = {
    "locate": {"run": tool_locate, "description": "把邮编、地址、经纬度或观测站名解析成坐标，并给出所属市町村、气象厅预报区和最近的雨量/气温湿度观测站（国土地理院、气象厅）。其他 jma_ 工具会自动做这一步，仅在需要核对定位或遇到候选站点时单独调用。",
               "schema": schema({"place": PLACE}, ["place"])},
    "rainfall": {"run": tool_rainfall, "description": "查询日本某位置最近的 AMeDAS 观测站的最新 10 分钟/1 小时/24 小时降水量，以及最近 1～7 天的日降水量（气象厅速报值）。雨量是最近观测站的值，不是该地点本身的值。",
                 "schema": schema({"place": PLACE, "station_code": STATION,
                                   "days": {"type": "integer", "minimum": 1, "maximum": 7, "description": "查询最近几天，默认 4，最多 7。"}})},
    "warnings": {"run": tool_warnings, "description": "查询日本某位置所在市町村当前发布中的警报、注意报（含新防灾气象信息的级别），并附气象台的展望原文（日语）。不预测解除时间。",
                 "schema": schema({"place": PLACE, "station_code": STATION,
                                   "include_outlook": {"type": "boolean", "description": "是否附上气象台展望原文，默认 true。"}})},
    "site_rain_risk": {"run": tool_site_rain_risk, "description": "读取日本某位置正上方 1 km 网格的解析雨量档位，以及キキクル（危险度分布）的表面雨量、流域雨量、土壤雨量三个警戒级别（气象厅地图瓦片，仅档位，不是精确数值）。",
                       "schema": schema({"place": PLACE, "station_code": STATION})},
    "wbgt": {"run": tool_wbgt, "description": "估算日本某位置附近的暑热指数（WBGT）：用最近的气温湿度观测站数据和 Stull 公式推算，4～10 月再用环境省官方实况做日射修正。是估算值，不是实测。",
             "schema": schema({"place": PLACE, "station_code": STATION,
                               "days": {"type": "integer", "minimum": 1, "maximum": 7, "description": "估算最近几天，默认 3，最多 7。"},
                               "times": {"type": "string", "maxLength": 60, "pattern": r"\d{1,2}:\d{2}(\s*,\s*\d{1,2}:\d{2}){0,5}",
                                         "patternHint": "逗号分隔的时刻，如 8:30,13:00。", "description": "估算的时刻（日本时间），默认 8:30,13:00，最多 6 个。"}})},
}
TOOL_PREFIX = "jma_"


async def call_tool(name: str, arguments: Any) -> dict:
    if name not in CATALOG:
        return error("UNKNOWN_TOOL", "此插件未提供该工具。")
    values, message = validate(name, arguments)
    if message:
        return error("INVALID_ARGUMENTS", message, tool=TOOL_PREFIX + name)
    if "times" in values:
        parts = [t.strip().split(":") for t in values["times"].split(",")]
        if any(not (0 <= int(h) <= 23 and 0 <= int(m) <= 59) for h, m in parts):
            return error("INVALID_ARGUMENTS", "times 中的时刻必须在 0:00 到 23:59 之间。", tool=TOOL_PREFIX + name)
    try:
        return await asyncio.wait_for(asyncio.to_thread(CATALOG[name]["run"], values), timeout=TIMEOUT_SECONDS * 8)
    except SourceError as exc:
        return error(exc.code, exc.message, tool=TOOL_PREFIX + name, **exc.details)
    except (asyncio.TimeoutError, TimeoutError):
        return error("TIMEOUT", "请求未在时限内完成；本次未自动重试，请稍后按需查询。", tool=TOOL_PREFIX + name)
    except asyncio.CancelledError:
        raise
    except Exception as exc:  # 不向用户暴露内部堆栈，也不伪造结果
        return error("INTERNAL_ERROR", f"工具内部出错（{type(exc).__name__}）；本次没有返回数据。", tool=TOOL_PREFIX + name)


class JmaTool(Tool):
    key = ""

    def __init__(self) -> None:
        entry = CATALOG[self.key]
        super().__init__(ToolCard(id=TOOL_PREFIX + self.key, name=TOOL_PREFIX + self.key, description=entry["description"],
                                  input_params=deepcopy(entry["schema"])))

    async def invoke(self, inputs: dict, **kwargs: Any) -> dict:
        return await call_tool(self.key, inputs)

    async def stream(self, inputs: dict, **kwargs: Any) -> AsyncIterator[dict]:
        yield await self.invoke(inputs, **kwargs)


class LocateTool(JmaTool):
    key = "locate"


class RainfallTool(JmaTool):
    key = "rainfall"


class WarningsTool(JmaTool):
    key = "warnings"


class SiteRainRiskTool(JmaTool):
    key = "site_rain_risk"


class WbgtTool(JmaTool):
    key = "wbgt"


TOOL_TYPES = (LocateTool, RainfallTool, WarningsTool, SiteRainRiskTool, WbgtTool)
