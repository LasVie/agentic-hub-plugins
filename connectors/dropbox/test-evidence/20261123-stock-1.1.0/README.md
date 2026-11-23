# Dropbox 1.1.0 实测原图

Task ID AH-20261117-dropbox-connector；Candidate ID CAND-CLD-001。原版 WorkSwarm 0.2.8、macOS、本地 Hub 目录夹具。最终包、完整功能记录、哈希和边界见 ../../TEST_REPORT.md。

Song Haoran 于 2026-11-23 在当前对话明确回复「确认通过并附五张原图提交 PR」，批准五张未经修改原图的公开发布。确认来源及时间记录见 user-test-confirmation.json，原图尺寸/字节摘要见 manifest.json。

1. 09-final-readonly-consent.jpg：文件名保留；实际画面是最终包的授权完成回跳页，不是同意页。
2. 10-final-card-connected.jpg：最终卡片详情与「使用」按钮。
3. 14-final-chat-file-metadata.jpg：最终新聊天的文件 ID、修订、111 字节、完整读取和哈希核对。
4. 12-final-chat-fulltext.jpg：最终新聊天的完整中文正文、末尾换行和 SHA-256。
5. 08-native-file-preview.jpg：原生 Dropbox 预览的同一测试文件全文。

原生预览两行重建的 111 字节本地夹具与服务端 content_hash 和实际聊天字节一致；浏览器下载等待超时，不声称下载成功或找到了最初上传源。仅测试文件读取，无 Dropbox 文件写入。

本次批准限于包、五张原图和 PR，不含自动合并或 Hub 发布。
