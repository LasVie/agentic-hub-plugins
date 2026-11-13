# Test report

`AH-20261113-google-sheets` · Google 表格连接器 · 1.0.0 · Song Haoran.

## Package and stock WorkSwarm tests · 2026-11-13

Official Agentic Hub CLI 0.0.1 validation and packaging, JavaScript
preflight, and source/native/wrapped/extracted payload equivalence passed.
The exact wrapped SHA-256 is `65bdf3b6b49d3fa04130d1aeee8a7e7c014ba8815cbe744ee22fa0b06179b021`
and the native SHA-256 is `49b57e3597ff5ef7ef53cc4da760d4ba34ee2b25880364f9b3820e252114e4a4`.
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

The installed CLI read, updated and re-read the Chinese range A2:B2. Unit regressions covered bounded ranges, preserved formula cells, explicit typed formulas, literal writes, and append with INSERT_ROWS.

Ten shared focused functional regressions passed. The OAuth and Google
business operations exercised by these tests used synthetic data. Actual
Google consent/API results, user screenshots and acceptance, public Hub
installation, Linux, Windows and remote backend behavior are pending.

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

Retested exact 1.0.0 on stock macOS WorkSwarm 0.2.8 in a new isolated
profile with the local Hub catalog fixture. An on-demand local landing
page started each card's authorization only when selected. The user
completed all four browser callbacks after the correct Cloud project had
the APIs enabled. All four cards reported connected and installed their skills.

Created a disposable spreadsheet, wrote and read back the exact A1:B2 range, appended a row and read back A3:B3, wrote an explicit SUM formula into C1, and verified its computed value of 11.

Drive was disconnected first and the remaining three card sessions were
still connected. The test harness disconnected all remaining sessions and
removed its imported client copy. Only the three newly created test
files were written. This test exercised real Google APIs through the
installed CLI and the stock host's connector RPC. The earlier chat model
test used a synthetic provider. Public Hub installation, manual test
acceptance and original user screenshots are pending.

## Live retest and original screenshot · 2026-11-13

Installed the exact 1.0.0 wrapped ZIP (`65bdf3b6b49d3fa04130d1aeee8a7e7c014ba8815cbe744ee22fa0b06179b021`) on stock macOS WorkSwarm 0.2.8 through the local Hub fixture. The user completed Google browser OAuth for the same Desktop test project. A scripted local model drove the stock host chat RPC and Bash tool to run the installed CLI against the real Google API. The isolated web gateway exited at startup, so the screenshot comes from the destination application. Only the designated test files were written.

The chat tool wrote `截图验证 172027` to `Sheet1!D1` and read back `A1:D3`. The formula in `C1` still evaluated to `11`. The original screenshot shows both cells in Google Sheets.

[Original screenshot](evidence/1.0.0/cell-readback.jpg). The isolated connector sessions and copied OAuth client file were cleared after testing. Public Hub installation and explicit user confirmation of test completion are pending.

## User confirmation · 2026-11-13

After receiving the exact-version results and original screenshots, Song Haoran requested proceeding with the PR merge in the current conversation. The confirmed version is 1.0.0, wrapped ZIP SHA-256 65bdf3b6b49d3fa04130d1aeee8a7e7c014ba8815cbe744ee22fa0b06179b021. The linked confirmation is RPT-20261113-google-sheets-confirmed.
