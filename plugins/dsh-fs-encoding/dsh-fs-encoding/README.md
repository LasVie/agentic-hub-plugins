# 文件编码守护

修改说明：2026-10-22，版本 1.0.4 将展示信息和使用说明改为中文；补全 Skill、工具说明和可读提示的中文；工具接口与编码处理算法保持不变。

通过专用工具检查和修改旧编码文本，保留原始编码、BOM 与主要换行格式，并在写入前拒绝无法用原编码表示的字符。

## 主要功能

- `encoding_read`：使用明确编码或安全检测读取文件。
- `encoding_write`：创建或整体替换文本。
- `encoding_edit`：执行文字替换并校验编码。
- `encoding_grep`：在明确指定的文件中搜索已解码文本。
- `encoding_undo`：撤销最近一次且文件未被外部修改的工具写入。

## 安装与使用

在兼容 WorkSwarm/JiuwenSwarm 的扩展面板导入 `dsh-fs-encoding-1.0.4-native-test.zip`，确认版本 `1.0.4`、一个 Skill 和五个工具，再在会话中选中插件。

示例：“先用 encoding_read 以 gbk 读取这个文件；预览将‘旧文本’替换为‘新文本’，保留原有编码和 CRLF，得到我的写入指令后再修改。”

修改前先读取现有文件。没有 BOM 且不是 UTF-8 的文件，应明确指定 `gbk`、`big5`、`shift_jis`、`euc_kr` 或 `windows-1252` 等编码；不要把猜测当作确定结果。使用 `write=false` 预览，实际写入应符合用户授权。写入无法表示的字符会失败并保留原字节。撤销记录以仅当前用户可访问的权限保存在宿主临时目录，可供单独加载的工具共享。

市场包 `dsh-fs-encoding-1.0.4.zip` 使用 `dsh-fs-encoding/plugin.yaml` 外层和 `dsh-fs-encoding/dsh-fs-encoding/` 载荷。本地测试 ZIP 直接包含相同载荷；ZIP 哈希分别记录。

## 必要依赖与限制

需要支持原生 Python Tool API 的宿主及目标文件的读写权限。文件处理使用 Python 标准库；无需 Node.js、DSH 运行时、外部账号、API 密钥、MCP 连接或网络服务。会话中的自然语言调度仍需宿主模型。

只有显式调用这些 `encoding_*` 工具的操作受其保护，不会接管宿主内置文件工具。不会自动将既有文件转码为新编码。撤销只覆盖最近一次工具修改，文件发生外部变化后会拒绝撤销；临时记录也不替代版本控制或长期备份。

## 来源与许可

源自 [dsh-fs-encoding](https://github.com/MrWeiCodes/dsh-fs-encoding)，固定 npm 1.5.2 对应提交 `a4d31cc33bd6f0fab2bf6752f6e50e8301885b94` 的 Python 移植。完整 MIT 许可和原始署名保留在随包许可文件及 `THIRD_PARTY_NOTICES.md`。未捆绑 DSH/Cordis 运行时或其 Node 依赖，不表示获得上游背书。
