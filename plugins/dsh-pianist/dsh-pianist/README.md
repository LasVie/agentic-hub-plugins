# 离线钢琴演奏

这是 dsh-pianist 的 WorkSwarm 中文移植版，复用上游乐谱规范化、校验、移调、时间线与生成式备用钢琴音色。完全离线，不需要账号、CDN、API Key、音色下载或录音样本包。需要 Node.js 22 或以上；标准 macOS WorkSwarm 安装会自动找到自带 Node，其他位置可设置 `DSH_NODE_BINARY`。

## 安装与使用

在 WorkSwarm「扩展」导入原生测试 ZIP、安装并在新对话中启用。请助手调用 `dsh_pianist`，提供已有工作目录的绝对路径 `workspace_dir` 与 `notes` 数组：

```json
{"workspace_dir":"/你的专用工作目录","title":"中文钢琴练习","bpm":100,"transpose":0,"notes":[{"midi":60,"start_beat":0,"beats":1,"velocity":0.65},{"midi":64,"start_beat":1,"beats":1,"velocity":0.65},{"midi":67,"start_beat":2,"beats":2,"velocity":0.65}]}
```

MIDI 范围21–108；start_beat 是起始拍，beats 是时值；同时开始可形成和弦。BPM 为30–240，移调 -24 至24半音。单次最多256个音符、60秒；小数节拍精确到1/960拍。越界或非法输入会返回中文错误，不会悄悄替换音高。

成功后会在独立 `piano-<标识>` 子目录生成 `performance.wav`、`score.json`、`player.html`。打开 player.html，点击「播放」「暂停」「从头播放」，也可以试听88键键盘或下载 WAV。所有脚本与音频都在单个 HTML 内，不需要启动服务。浏览器要求手动点击后才允许发声。

输出为22050Hz、单声道、16位 WAV。音色是上游生成式备用方案，并非录音级 Salamander 音色；本包不包含上游 Salamander CC BY 3.0 录音、MP3、音色清单或预加载器，不声称达到录音采样音质。没有 DeepSeek 专用聊天组件或自动播放；WorkSwarm 使用可独立打开的本地产物界面。

许可、固定提交、复用路径见 THIRD_PARTY_NOTICES.md。
