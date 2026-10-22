# 本地凭据保险库

这是 dsh-vault 的 WorkSwarm 中文移植版，只保留本地加密凭据 CRUD、掩码查询与 TOTP。无需 Apollo、Kodwai、CineFlo 或任何服务账号。使用 Node.js 22 或以上；macOS 标准安装的 WorkSwarm 可自动使用自带 Node，其他位置可用 `DSH_NODE_BINARY` 指定可执行文件。

## 安装与开始

1. 在 WorkSwarm 的「扩展」中导入提供的原生测试 ZIP，安装并启用本插件。Agentic Hub 外层 ZIP 是另一个包装，不能把两种包混为一谈。
2. 新建测试对话并选择本插件。先建立专用空测试目录，向助手说「使用 dsh_vault，action=demo，workspace_dir=这个目录的绝对路径」。
3. 演示使用虚构账户、公开测试口令，验证密文落盘、掩码、已知 TOTP 向量、错误口令拒绝。**演示目录不能保存真实秘密。**

## 真实本地使用

在终端运行 `python scripts/setup_vault.py /你的工作目录`，按提示输入主口令。该脚本只在本地获取口令并写入权限为600的 `vault-master-password.txt`，不经过聊天、不在命令行或日志中显示口令。随后让工具以 `action=init` 初始化一次。

将凭据在本地写成 `credential.json`，格式是 `{"label":"服务名称","username":"用户名","secret":"密码","totp_secret":"可选Base32密钥"}`。文件应为600权限，并在完成导入后由你自行安全处理；不要将真实内容粘贴到聊天、PR 或共享追踪表。

工具 `dsh_vault` 需要 `workspace_dir` 和 `action`：

- `init`：创建 `dsh-vault-data/vault.json`，存在时拒绝覆盖。
- `put`：用 `id` 与相对路径 `credential_file` 导入；覆盖已存在条目须明确给 `overwrite=true`。
- `list`：可给 `query` 搜索标签；秘密始终显示为 `********`。
- `get`：用 `id` 查询条目元数据，秘密始终掩码。本适配版不向聊天返回原密码，也不自动填写浏览器。
- `totp`：用户明确要求时生成该条目的当前验证码。验证码属于临时秘密，不能截图或上传真实验证码。
- `remove`：用户明确要求删除时设置 `confirm=true`。

加密采用上游 scrypt（N=32768,r=8,p=1）和每次随机 nonce 的 AES-256-GCM。主口令文件与保险库由同一用户账户读取：这不能抵御已控制该账户、能同时读取两者的进程。请使用强主口令、操作系统权限和加密磁盘；丢失口令不能恢复数据。没有云同步、密钥托管、浏览器集成或完整上游设置界面。

演示数据与真实保险库分开。所有写入加锁并原子替换；拒绝数据路径符号链接。许可、上游提交和修改范围见本包 THIRD_PARTY_NOTICES.md。
