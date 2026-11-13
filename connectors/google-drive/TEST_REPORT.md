# Test report

`AH-20261113-google-drive` · Google 云端硬盘连接器 · 1.0.0 · Song Haoran.

## Package and stock WorkSwarm tests · 2026-11-13

Official Agentic Hub CLI 0.0.1 validation and packaging, JavaScript
preflight, and source/native/wrapped/extracted payload equivalence passed.
The exact wrapped SHA-256 is `565843dce7a9af51f7d43d4edab6a4580d2eda97a57af9c98d308bb4e8afcc22`
and the native SHA-256 is `a26bf9070f435ab14dcc5a0485a727ad29510d257dd65bb8f06f9de12a1c01e8`.
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

With Chinese input the exact installed CLI searched by name/type, used the returned file link in Slides, and exercised the Google Drive mock endpoint with the Drive-only bearer. Unit tests covered Drive query quoting and pagination, native PDF export, output preservation, and no access to untrusted URLs.

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

A narrow real Google Drive search succeeded. A second search found the newly created Slides deck by name and type. Its returned webViewLink opened the same deck in the Slides connector. PDF export succeeded and the downloaded file had the expected PDF signature and size.

Drive was disconnected first and the remaining three card sessions were
still connected. The test harness disconnected all remaining sessions and
removed its imported client copy. Only the three newly created test
files were written. This test exercised real Google APIs through the
installed CLI and the stock host's connector RPC. The earlier chat model
test used a synthetic provider. Public Hub installation, manual test
acceptance and original user screenshots are pending.

## Live retest and original screenshot · 2026-11-13

Installed the exact 1.0.0 wrapped ZIP (`565843dce7a9af51f7d43d4edab6a4580d2eda97a57af9c98d308bb4e8afcc22`) on stock macOS WorkSwarm 0.2.8 through the local Hub fixture. The user completed Google browser OAuth for the same Desktop test project. A scripted local model drove the stock host chat RPC and Bash tool to run the installed CLI against the real Google API. The isolated web gateway exited at startup, so the screenshot comes from the destination application. Only the designated test files were written.

The chat tool searched by file name and type, selected the disposable Slides deck, and exported a 60,258-byte PDF. The saved file matched the returned byte count and PDF signature. The original screenshot shows page 2 of the exact exported file in macOS Preview.

[Original screenshot](evidence/1.0.0/pdf-export.jpg). The isolated connector sessions and copied OAuth client file were cleared after testing. Public Hub installation and explicit user confirmation of test completion are pending.

## User confirmation · 2026-11-13

After receiving the exact-version results and original screenshots, Song Haoran requested proceeding with the PR merge in the current conversation. The confirmed version is 1.0.0, wrapped ZIP SHA-256 565843dce7a9af51f7d43d4edab6a4580d2eda97a57af9c98d308bb4e8afcc22. The linked confirmation is RPT-20261113-google-drive-confirmed.
