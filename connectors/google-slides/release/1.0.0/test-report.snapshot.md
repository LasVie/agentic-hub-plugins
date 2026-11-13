# Test report

`AH-20261113-google-slides` · Google 幻灯片连接器 · 1.0.0 · Song Haoran.

## Package and stock WorkSwarm tests · 2026-11-13

Official Agentic Hub CLI 0.0.1 validation and packaging, JavaScript
preflight, and source/native/wrapped/extracted payload equivalence passed.
The exact wrapped SHA-256 is `b799afd7c43287abf0c210fb0f1d530f16ced7297c6e1ebcad307068584d0b4d`
and the native SHA-256 is `640e3509401de9b3088e94f374a1cd9c6adc5f17ac5dd0fdf868669a62d555b2`.
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

With the Drive result the installed CLI read a specific slide, sent revision-checked replacement to that page only, then read back the changed Chinese text. A real WorkSwarm chat request with a synthetic OpenAI-compatible model called the installed Drive and Slides CLIs via the host Bash tool and returned the Chinese readback. Unit tests also checked creation of a new page and stale revision handling.

Ten shared focused functional regressions passed. The OAuth and Google
business operations exercised by these tests used synthetic data. Actual
Google consent/API results, user screenshots and acceptance, public Hub
installation, Linux, Windows and remote backend behavior are pending.
