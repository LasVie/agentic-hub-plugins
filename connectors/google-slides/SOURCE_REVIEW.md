# Source review

Google Slides Connector → Google 幻灯片连接器 → `google-slides` · `AH-20261113-google-slides` · Song Haoran.

The team-owned Gmail 1.5.1 payload (wrapped SHA-256
`9140035cb10415cf88f4394ec9cf34f6642ef591052d66d48fcb705781f11f2e`)
provides the launcher and Desktop OAuth patterns and the unchanged requirements
and license files. The new bootstrap shares its hash-locked runtime across the
four separate cards. OAuth state uses a common Desktop client configuration and
per-card token/attempt files. This reuses the team's code and preserves prior
dependency attributions without assigning a new license to it.

The public Hub Google Drive 1.0.0 listing documents manual short-lived token
configuration and Drive/Docs/Sheets operations. License permission for its
implementation remains unknown; only the catalog text and filename listing
were inspected. Google Workspace CLI v0.22.5 (Apache-2.0, tag commit
`705fb0ecac6f4249679958f6325b809b63fdde17`) was evaluated through its README and
license. Neither project's implementation, prompts, executables or images enter
this connector. `service.py`, packaged documentation and skill are written
against the [Google REST specification](https://developers.google.com/workspace/slides/api/reference/rest). No sample source or branding
assets were copied. The bundled text licenses cover the three direct/auth
dependencies noted in THIRD_PARTY_NOTICES; dependency wheels are installed with
hash verification and remain outside the ZIP.
