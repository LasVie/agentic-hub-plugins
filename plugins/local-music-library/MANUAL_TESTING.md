# 本地音乐库 v1.0.0：人工测试

- 候选：CAND-DSH-335；任务：AH-20261023-local-music-library；负责人：Cai Zhenze。
- 内部标识：local-music-library；本地分支：feat/local-music-library。
- 人工测试尚未完成；自动检查和浏览器自测不替代你的确认。

## 安装与包身份

独立 WorkSwarm：<http://127.0.0.1:6283>。此实例的后端为127.0.0.1:29110，WebSocket连接与配置读取已通过；没有更改模型设置。当前已安装本插件，可直接打开「Extensions → My Extensions → 本地音乐库」。如需重新导入，在「Create → Create from file」选择下面的原生测试ZIP，再确认安装。保留其他插件，不要点击Publish。

**此旧版WorkSwarm使用根manifest测试ZIP：**

`/Users/IDLE_And_R/Downloads/Huawei/agentic-hub-plugins/plugins/local-music-library/test-packages/local-music-library-1.0.0-workswarm.zip`

SHA-256：`e81650018d2d85667e6d2042c4ed33eb1129b58aba9de7be24c6f9c4e11eb24a`

相同文件也在 `dist/local-music-library/1.0.0/`。仓库规范双层ZIP：

`/Users/IDLE_And_R/Downloads/Huawei/agentic-hub-plugins/releases/agent-plugin/local-music-library/1.0.0/local-music-library-1.0.0.zip`

SHA-256：`5c32cc0f4068d75272e00bff309b84a9b98c279d469d8c636d96960ca5e8408f`

规范ZIP含市场wrapper，两个ZIP的14个内层文件逐字节相同，已经提取验证。不要把其中一个ZIP的摘要当作另一个的摘要。

## 实际工具测试

已准备两个原创16秒合成WAV（220Hz和440Hz），以及一个故意损坏的WAV，不读取你的真实曲库。已有自测歌单可能存在。目录如下：

- 音频：`/Users/IDLE_And_R/Downloads/Huawei/agentic-hub-plugins/dist/local-music-library/1.0.0/test-audio`
- 独立工作目录：`/Users/IDLE_And_R/Downloads/Huawei/agentic-hub-plugins/dist/local-music-library/1.0.0/manual-workspace`

在插件详情点击Use，并使用以下测试请求。只有你自行提交聊天后才会使用宿主模型；本次开发未执行模型对话或付费调用。

```text
请实际调用「本地音乐库」的 local_music_library 工具测试 v1.0.0。
我授权为下列合成测试目录启动仅本机的播放器：
action = start
library_dir = /Users/IDLE_And_R/Downloads/Huawei/agentic-hub-plugins/dist/local-music-library/1.0.0/test-audio
workspace = /Users/IDLE_And_R/Downloads/Huawei/agentic-hub-plugins/dist/local-music-library/1.0.0/manual-workspace
confirmed = true

展示实际返回的ok、version、running、scan.count、scan.truncated和url。
核对版本为1.0.0；不要编造URL，不要自行编写替代播放器。
然后用同样路径实际调用action=status，确认同一会话仍在运行。
只把实际会话URL给我，不公开分享。不要把服务启动或扫描成功当作实际音频播放通过。
工具不可用或失败时如实报告，不使用记忆替代结果。
```

不使用模型的等效入口：在仓库根目录用Python3.11+运行下列命令（测试相同内层载荷，但不证明WorkSwarm聊天调用成功）：

```sh
python3 -B plugins/local-music-library/local-music-library/runtime/control.py '{"action":"start","library_dir":"/Users/IDLE_And_R/Downloads/Huawei/agentic-hub-plugins/dist/local-music-library/1.0.0/test-audio","workspace":"/Users/IDLE_And_R/Downloads/Huawei/agentic-hub-plugins/dist/local-music-library/1.0.0/manual-workspace","confirmed":true}'
```

## 浏览器操作与预期

1. 在桌面Chrome独立标签页打开工具实际返回的完整URL；不要用WorkSwarm内嵌预览。页面应显示「本地音乐库 v1.0.0」和3首文件；扩展名列表不证明文件可播放。
2. 点击「中文示例-低音.wav」播放。确认16秒音频实际播放、进度前进，能够暂停、拖动进度、调整音量，再播放。测试下一首切换到高音。合成声音不是音乐品质评测。
3. 勾选两个正常WAV，保存新歌单「我的离线测试」，打开后确认只有两首；验证搜索和下一首。同名替换、删除歌单需先确认，均不能移动或删除源音频。
4. 播放若干秒后暂停，点击「保存进度」，看到成功提示再刷新。应恢复同一曲目、位置、歌单并保持暂停，手动点击才继续。再次关闭本库服务、start后仍应保留状态。
5. 点击「查看全部」并尝试损坏WAV，应显示中文加载/解码失败，不能报告播放成功。重新选择正常WAV应恢复播放。
6. 以相同路径调用action=stop且confirmed=true，应返回running=false；同路径status应确认关闭。不要根据PID关闭其他进程。关闭网页不会关闭服务；30分钟无请求自动退出。

服务地址含本地会话凭据，截图请只包含页面内容，避免地址栏。提供原始截图显示工具实际返回的版本和关键结果，以及播放器操作/保存恢复结果；不要把开发自测截图当作你的人工测试证据。完成后请明确确认此 **v1.0.0与上述两个摘要对应的包** 测试完成/通过，并说明任何未解决问题。

## 已验证与限制

自动功能：源与规范ZIP提取载荷各24/24项；真实HTTP、范围读取、路径约束、状态持久化。宿主：实际运行实例导入/安装/list/show与WebSocket；独立SDK进程加载已安装插件，DeepAgent绑定/调用/卸载；浏览器实播、歌单与刷新恢复。没有执行用户/模型对话；系统文件选择器上传流程未自动完成，导入通过真实后端RPC完成，UI导入对话框和已安装详情已查看。

仅macOS/Linux Python3.11+；本机回环，不提供远程访问、Windows支持或在线音乐/歌词/转码。浏览器编解码器决定格式支持，本次实播只验证Chrome合成PCM WAV；其他编码、浏览器和移动端未验证。最多500首、5000个枚举条目、4层子目录、512MiB/文件；状态私有但不加密。完整边界见内层README和外层TEST_REPORT。
