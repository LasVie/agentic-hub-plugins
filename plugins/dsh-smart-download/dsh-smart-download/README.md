# 智能下载

修改说明：2026-10-22，版本 1.0.1 将展示信息、实际 Skill、工具说明和可读错误补全为简体中文。保留技术标识、原始 MIT 许可与署名、下载与续传的主要处理流程。校验错误使用专用内部异常保留 `CHECKSUM_MISMATCH` 分类；状态网址隐藏凭据与查询参数，格式无效的网址返回结构化错误，并保留既有下载目录的访问权限。负责人保持 Siu Lok Yin；任务 `AH-20261022-dsh-smart-download`，候选 `CAND-DSH-139`。

通过 HTTP(S) 下载用户明确指定的文件，并提供下载状态、服务器分段加速、安全续传和可选的 SHA-256 校验。下载采用 Python 标准库和宿主原生工具，不需要连接器、Node.js、aria2、云账户或 API 密钥。

## 主要功能

- `smart_download`：将一个明确的 HTTP(S) 网址下载到本地目标路径，可指定 `sha256`。
- `download_status`：使用返回的 `task_id` 查询已保存的任务状态。
- 服务器正确支持 Range 且文件足够大时，可使用 4 或 8 个连接；否则使用单连接或回退到单连接。
- 先写入 `.part` 临时文件；续传所需的网址、验证器和大小元数据匹配时，才继续已有的临时文件。完成后校验大小和可选 SHA-256，再原子替换目标文件。

## 安装与使用

在兼容 WorkSwarm/OpenJiuwen 原生 Tool API 的宿主扩展面板，导入 `dsh-smart-download-1.0.1-native-test.zip`。确认版本 `1.0.1`、一个 Skill 和两个工具，再在目标会话选中插件。

示例：“请把这个 HTTP(S) 文件下载到我指定的本地路径。先说明目标路径，使用我提供的 SHA-256 校验；完成后查询任务状态并报告字节数和校验结果。”

文件名明确时传入 `output_path`；仅指定目录时使用 `output_dir`，让服务器响应或网址提供经过清理的文件名，两者不能同时提供。`workers` 只能为 `1`、`4` 或 `8`。已有目标文件默认不会覆盖；只有用户明确要求才设置 `overwrite=true`。

对公开提供的预期哈希，传入 64 个十六进制字符的 `sha256`。校验失败时返回 `CHECKSUM_MISMATCH`，不会将失败内容保存为最终目标文件。查询状态必须使用工具实际返回的 32 个字符 `task_id`。

市场包 `dsh-smart-download-1.0.1.zip` 使用 `dsh-smart-download/plugin.yaml` 外壳和 `dsh-smart-download/dsh-smart-download/` 内层；本地测试包直接包含相同载荷。两种 ZIP 的哈希不同。

## 必要依赖与限制

需要 Python >=3.10、兼容的宿主 Tool API、HTTP(S) 网络访问权限和目标路径写入权限。会话中的自然语言调度需要宿主已配置的模型。默认超时为 60 秒；参数允许的范围为 1 至 600 秒。

默认拒绝私有、回环、链路本地和保留地址。只有在用户明确批准的内网或本地测试中，才传入 `allow_private_network=true`；使用本地测试服务器的结果不证明公开互联网下载或其他网络策略已经通过。

HTTP 请求可使用 `headers` 提供必要信息，不要在对话中回显密钥。工具不接受网址内的用户名和密码；状态中隐藏网址查询参数与用户凭据。续传元数据可能保留原始网址及查询参数，状态与临时元数据文件以仅当前用户可读写的权限保存；下载目录和本地路径仍属于用户数据，应妥善管理。

不支持 FTP、BT、磁力链接、云盘账户管理、网页内容解析或下载后执行。分段加速依赖服务器真实支持 Range，不承诺固定速度提升。状态为 `completed` 才能报告下载完成；指定了哈希时，还必须确认 `verified=true`。未指定预期哈希时，输出计算所得的 SHA-256 不等于已验证内容来源。

## 来源与许可

移植自 [dsh-smart-download](https://github.com/LeiSureYu/dsh-smart-download) `v1.4.6`，固定提交 `e80a6574407fed44a8ad6efde3a789bce119beeb`。完整原始 MIT 许可见 `licenses/dsh-smart-download/LICENSE`，复用范围和修改说明见 `THIRD_PARTY_NOTICES.md`。不捆绑原 DSH/Cordis 界面、aria2 或其平台二进制，不表示获得上游背书。
