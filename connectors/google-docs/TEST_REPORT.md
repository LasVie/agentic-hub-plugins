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

## 1.0.1 compatibility correction · 2026-11-13

Accept Google-provided tab IDs such as `t.0` returned by the provider. No change to scopes or authentication. The 1.0.0 archives and their recorded hashes remain available.

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

Created a disposable document, read its explicit Google-assigned tab, appended a paragraph with Chinese text and emoji, replaced a substring using UTF-16 offsets and the current revision, and read back the expected result in that tab.

Drive was disconnected first and the remaining three card sessions were
still connected. The test harness disconnected all remaining sessions and
removed its imported client copy. Only the three newly created test
files were written. This test exercised real Google APIs through the
installed CLI and the stock host's connector RPC. The earlier chat model
test used a synthetic provider. Public Hub installation, manual test
acceptance and original user screenshots are pending.

## Live retest and original screenshot · 2026-11-13

Installed the exact 1.0.1 wrapped ZIP (`b50efb5f7eda90ce6dfd0559fb1462b86cbc91494d85c5173935905a678c0fd3`) on stock macOS WorkSwarm 0.2.8 through the local Hub fixture. The user completed Google browser OAuth for the same Desktop test project. A scripted local model drove the stock host chat RPC and Bash tool to run the installed CLI against the real Google API. The isolated web gateway exited at startup, so the screenshot comes from the destination application. Only the designated test files were written.

After a fresh Docs consent attempt, the chat tool appended `WorkSwarm 中文段落 · 截图验证 172027` to the selected document tab using the current revision and read the paragraph back. The original screenshot shows the resulting document in Google Docs.

[Original screenshot](evidence/1.0.1/append-readback.jpg). The isolated connector sessions and copied OAuth client file were cleared after testing. Public Hub installation and explicit user confirmation of test completion are pending.

## User confirmation · 2026-11-13

After receiving the exact-version results and original screenshots, Song Haoran requested proceeding with the PR merge in the current conversation. The confirmed version is 1.0.1, wrapped ZIP SHA-256 b50efb5f7eda90ce6dfd0559fb1462b86cbc91494d85c5173935905a678c0fd3. The linked confirmation is RPT-20261113-google-docs-confirmed.
