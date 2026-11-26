# Source review

Dropbox → Dropbox 文件连接器 → `dropbox`. Song Haoran. AH-20261117-dropbox-connector.

Independent implementation based on [provider documentation](https://docs.dropboxapi.com/dropbox-api/docs/oauth) (Dropbox API v2 / PKCE; upstream Claude plugin 1.0.1 reviewed as reference). No third-party code is included in the package. Provider permissions, account terms, and implementation license coverage were considered separately. The pre-icon release bundled no upstream prompts, artwork, account material or logo.

## 1.0.3 brand asset

- [Dropbox official material](https://brand.dropbox.com/logo), retrieved 2026-11-17. [DBX_Tab_128.png](https://www.dropbox.com/scl/fo/6qjduc7j5ujf09f75w1p7/AGATVvVEZHoOrsYEKaNctAI/Logos/Dropbox/Tab/DBX_Tab_128.png?rlkey=tkqw8jcoi7f24voc6577vakky&dl=0) is bundled unchanged as `icon.png` (SHA-256 `77dc1afb3d82c5fcbde086580a7648e216cda8760629dad3f8079e62f25f24c8`).
- [Terms](https://docs.dropboxapi.com/dropbox-api/docs/developer-resources/branding-guide). The developer guide allows an approved Dropbox mark within an app to identify its Dropbox integration. This exact PNG is used on the installed WorkSwarm connector card only. The Hub wrapper has no Dropbox mark and the OAuth application branding is separate.
- Attribution is included in `THIRD_PARTY_NOTICES.md`. The mark retains its owner and usage terms.
