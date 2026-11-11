# 第三方依赖与许可说明

本连接器为独立实现。运行依赖通过 `requirements.txt` 在专用 Python 环境中单独安装；
本 ZIP 不包含依赖源码、二进制文件、安装包或虚拟环境。下列完整许可文本仅作为依赖说明
随包提供，原文保持不变；它们不为本项目自行编写的代码重新指定许可证。

| 依赖 | 审核版本 | 原作者信息与许可 | 完整许可文件 |
| --- | --- | --- | --- |
| [MCP Python SDK](https://github.com/modelcontextprotocol/python-sdk) | 1.25.0 | Copyright (c) 2024 Anthropic, PBC；MIT | `licenses/mcp/LICENSE` |
| [google-auth-oauthlib](https://github.com/googleapis/google-auth-library-python-oauthlib) | 1.2.3 | Google LLC 源文件版权声明；Apache-2.0 | `licenses/google-auth-oauthlib/LICENSE` |
| [google-auth](https://github.com/googleapis/google-auth-library-python) | 2.41.1 | Google LLC 源文件版权声明；Apache-2.0 | `licenses/google-auth/LICENSE` |
| [Requests](https://github.com/psf/requests) | 2.32.5 | 发行包作者 Kenneth Reitz；Apache-2.0 | `licenses/requests/LICENSE` |

上述许可文件取自所列版本的已安装发行包；未修改依赖文件。这四个发行包的文件清单中未发现
单独的 NOTICE 文件。安装后的其他依赖仍保留各自发行包内的许可证；本包不复制或替换这些文件。

传递依赖包含 MIT、MIT-0、Apache-2.0、BSD、ISC、PSF-2.0 等许可，以及 cryptography 的
`Apache-2.0 OR BSD-3-Clause` 和 Certifi 的 **MPL-2.0**。不得将整个依赖链称为“全部为宽松许可”
或“无 copyleft”。完整版本与审核记录见源码目录中的 `provenance.json` 和 `SOURCE_REVIEW.md`。
若未来需要将依赖源码或二进制随包分发，必须重新检查相应源码、许可、NOTICE 与分发义务。

已评估的 `taylorwilsdon/google_workspace_mcp` v2.4.0（MIT）未被复制或移植；
现有 Gmail 邮件助手的实现复用许可仍未确认，本包不使用其实现、提示词或素材。
Google/Gmail 名称仅用于说明所连接的服务，不表示 Google 官方出品或认可。
开源依赖许可不代替 Google API 的服务条款、用户授权、应用验证或数据使用要求。
