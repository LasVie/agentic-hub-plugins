# Test report

`AH-20261113-google-docs` · Google 文档连接器 · 1.0.0 · Song Haoran.

## Package and stock WorkSwarm tests · 2026-11-13

Official Agentic Hub CLI 0.0.1 validation and packaging, JavaScript
preflight, and source/native/wrapped/extracted payload equivalence passed.
The exact wrapped SHA-256 is `2cb4d8106002ce5308e803e19eef8578f740b251c89c1aaaeaed8948051646b4`
and the native SHA-256 is `d06b174de216f1b1747a959d9f03ddf888dc06964abbd6deaf1014b2821adaee`.
Both contain the Chinese README, skill and license references and no secrets.

All four exact wrapped archives were downloaded and installed by the stock
macOS WorkSwarm 0.2.8 backend with an empty isolated profile and local Hub
catalog fixture. PATH contained only macOS system paths. Python 3.11 was
already installed and the first package bootstrapped the hash-locked
dependencies from PyPI. The other three reused the same private runtime.
Without configuration the card provided no authorization URL. One Desktop
JSON import enabled all four cards to start OAuth. Each asked only for its
expected scope, used PKCE S256, and received a real localhost HTTP callback.
The Google token exchange used a synthetic fixture. The stock host showed
connected status and installed the skill. Disconnecting Drive cleared its
local session, while Slides, Docs and Sheets still reported connected.

The installed CLI read a specified Chinese tab, sent a revision-checked append to that tab, and read back the changed text. A unit regression covered a nested tab and UTF-16 offsets across styled text runs with Chinese and emoji.

Ten shared focused functional regressions passed. The OAuth and Google
business operations exercised by these tests used synthetic data. Actual
Google consent/API results, user screenshots and acceptance, public Hub
installation, Linux, Windows and remote backend behavior are pending.
