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

## 1.0.1 compatibility correction · 2026-11-13

Accept Google-provided slide object IDs containing a colon returned by the provider. No change to scopes or authentication. The 1.0.0 archives and their recorded hashes remain available.

The exact 1.0.1 wrapper also installed in the same stock host. The simulated provider returned its punctuation-bearing identifier; the read/write and readback passed. All ten shared regressions passed.

## Live OAuth on stock WorkSwarm 0.2.8 · 2026-11-13

In a new isolated profile, the stock WorkSwarm backend downloaded and
installed this exact wrapped archive from a local Hub catalog fixture.
The user granted the connector's single scope in Google's browser flow
using a Desktop client from My First Project. The Google token exchange
and localhost callback were real. WorkSwarm reported the card connected
and its skill installed. Disconnecting Drive cleared its local session
while the other three real sessions remained connected; the remaining
test sessions were then disconnected.

In that first live round Google returned HTTP 403 for the business
operation. The Cloud console showed that the relevant REST API was not
enabled for the project associated with the Desktop OAuth client. With the
user's approval, all four REST APIs were enabled in the correct project
and each enabled state was confirmed in the console. The follow-up round did not receive a browser callback before the consent window expired. Live business requests after API enablement still need verification. No test files were created in these runs. The isolated test sessions and imported client copy were cleared.

## Successful live Google operations · 2026-11-13

Retested exact 1.0.1 on stock macOS WorkSwarm 0.2.8 in a new isolated
profile with the local Hub catalog fixture. An on-demand local landing
page started each card's authorization only when selected. The user
completed all four browser callbacks after the correct Cloud project had
the APIs enabled. All four cards reported connected and installed their skills.

Created a disposable presentation, appended a title and body page, replaced one matching Chinese text occurrence on that page using the current revision, and read back the changed text. Drive subsequently found and exported the same presentation.

Drive was disconnected first and the remaining three card sessions were
still connected. The test harness disconnected all remaining sessions and
removed its imported client copy. Only the three newly created test
files were written. This test exercised real Google APIs through the
installed CLI and the stock host's connector RPC. The earlier chat model
test used a synthetic provider. Public Hub installation, manual test
acceptance and original user screenshots are pending.

## Live retest and original screenshot · 2026-11-13

Installed the exact 1.0.1 wrapped ZIP (`343cd6d9d78b0b514e04e8891ed77b2a720ec6bc98c2ae6a3f2c8ff2b3d772d6`) on stock macOS WorkSwarm 0.2.8 through the local Hub fixture. The user completed Google browser OAuth for the same Desktop test project. A scripted local model drove the stock host chat RPC and Bash tool to run the installed CLI against the real Google API. The isolated web gateway exited at startup, so the screenshot comes from the destination application. Only the designated test files were written.

The chat tool replaced one title on the selected page and read back the exact Chinese text, including `截图验证 172027 · 回读通过`. The original screenshot shows that page in Google Slides. The test title wraps in the default title box.

[Original screenshot](evidence/1.0.1/text-replacement-readback.jpg). The isolated connector sessions and copied OAuth client file were cleared after testing. Public Hub installation and explicit user confirmation of test completion are pending.

## User confirmation · 2026-11-13

After receiving the exact-version results and original screenshots, Song Haoran requested proceeding with the PR merge in the current conversation. The confirmed version is 1.0.1, wrapped ZIP SHA-256 343cd6d9d78b0b514e04e8891ed77b2a720ec6bc98c2ae6a3f2c8ff2b3d772d6. The linked confirmation is RPT-20261113-google-slides-confirmed.
