# 第三方来源与许可

本地音乐库以 `ported` 方式适配 kendu76/dsh-music-player 的本地曲库、歌单成员/持久化和字节范围播放逻辑。

- 来源：https://github.com/kendu76/dsh-music-player
- 固定提交：`172355b147f91ae994631aa4cbd61adfe8a5fb66`，上游版本1.0.3。
- 原始路径：`lib/index.js` 的本地 MIME、scan、resolvePlaylistMember/publicPlaylist、playlist persistence 和本地音频 Range 路由。
- 本包适配路径：`runtime/library.py`。改写为 Python，增加独立扫描上限、描述符级路径限制、严格状态校验、原子持久化与有限字节范围。
- 原版权：Copyright (c) 2026 kendu76。完整原 MIT 许可、授权条件与免责声明见 `licenses/dsh-music-player/LICENSE`，不得用此说明替代。
- 上游未发现独立 NOTICE。其他本包文件为本次宿主/界面适配；不声称拥有上游版权或官方背书。

不包含上游 React 客户端、在线歌曲/歌词/电台、音频样本、截图、品牌图片、QRCode、TTS、新闻或服务依赖。音频由用户提供，需自行确认处理权限。运行时仅使用 Python 标准库、宿主既有 SDK 和浏览器音频解码；未重新分发 Python、浏览器或 SDK。
