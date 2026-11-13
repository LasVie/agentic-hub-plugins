# Gmail read-only Connector — Build verification

Date: 2026-11-10, Asia/Singapore. Owner: Cai Zhenze.
Task: AH-20261110-gmail-readonly. Candidate: Not Applicable.
Chinese name: Gmail 只读邮件连接器. Version: 1.0.0.
Branch: feat/gmail-readonly, based on origin/main 933fc0f232c677fbf7f38c12482deb22cef8fded.
Local main 9f728e8 was divergent and was preserved; no merge/commit/reset was made.

## Current decision

Implementation is connector-only and read-only. Build is **not authenticated
Gmail acceptance**. The user supplied a Desktop OAuth client on 2026-11-10;
it was validated and configured locally. The user then authorized two named
test accounts and the newest five existing messages per account in this
conversation. The first browser OAuth flow completed, and first-account live
search plus five bounded message reads passed through the real WorkSwarm backend.
Both accounts' live integration results are recorded below. No mail mutation, model call or
paid service was used.
On 2026-11-11 the user explicitly confirmed that manual testing of the unchanged
native v1.0.0 ZIP is complete and passed. Six original screenshots were received.
The user authorized GitHub-only delivery, conditional on all Phase 3 gates.
The user subsequently explicitly confirmed the unchanged canonical wrapper hash and
instructed proceeding to merge while recording real denied-consent/provider-side
revocation checks as untested. Both exact-package confirmations and six originals
are available; no blocking defect is reported for the agreed bounded scope.
See USER_TEST_CONFIRMATION.md. GitHub-only delivery is authorized; no Release,
Hub operation, host modification, further account access or paid call is authorized.

## Host baseline and boundaries

- Existing checkout: `/Users/IDLE_And_R/Downloads/Huawei/jiuwenswarm`.
- Branch `local/connector-import`; HEAD fa91394e42a7af731424222db82b02351e694de9
  plus the existing uncommitted local-import feature.
- The 28 recorded source-file hashes in `local-only/connector-import/source-state.json`
  were checked unchanged before connector testing. No host source, SDK, shared
  dependencies, other connectors, model configuration or services were changed.
- Frontend6411 and upload HTTP6412 returned200; local import capabilities enabled.
  Browser verification reached Extensions → 连接器广场 and its local import controls.
- Backend web WebSocket29430, AgentServer28430, gateway30430. All are the existing
  isolated instance with dedicated state and disabled model configuration.
- This verifies the **modified local testing host**, not local-import support in
  unmodified WorkSwarm. Only the local-import route rebases `./launcher.py` in
  the MCP arguments. Other host/install routes need supported absolute command /
  path configuration and remain unverified; no host workaround is bundled.
- The host's integration.type=cli ignores undeclared mcp.json server entries.
  This package therefore uses genuine stdio-mcp, with explicit connector-owned
  browser login before the Marketplace Connect action. It does not claim a
  host-managed OAuth button or a working CLI/MCP hybrid.

## Dependency/runtime verification

An independent development venv and private user runtime were prepared with
Python3.12.14, MCP1.25.0, google-auth-oauthlib1.2.3, google-auth2.41.1 and
Requests2.32.5. Runtime lock pins/hash-checks 40 distributions. Dependencies were
not installed into the host. The private default runtime is
`~/.local/share/agentic-hub/gmail-readonly/runtime`; parent directory mode700.
At initial packaging, no real client or token file existed there. The later
configuration follow-up below records the protected client copy. No virtualenv/wheel/client/token is
included in the payload. Source/license findings are in SOURCE_REVIEW.md.

## Automated evidence

Command (connector-owned Python):

```text
connectors/gmail-readonly/.venv/bin/python -B -m pytest connectors/gmail-readonly/tests -q -p no:cacheprovider
```

The first complete run passed85 tests; the final expanded run is recorded below. These cover exact three-tool discovery,
GET endpoint allowlist, limits, sanitized provider failures, safe MIME/HTML text,
attachment omission, private state, extra-scope rejection, expiry/refresh,
revoked/missing credentials, login cancellation/configuration races and logout.
The installed Google library's **real local loopback HTTP callback** was exercised
with synthetic credentials and all outbound HTTP intercepted: correct state
exchanged a synthetic code, wrong state was rejected before exchange; PKCE S256
and no token/code logging were checked. This is **not live Google consent**.

A separate real stdio MCP process initialized, listed exactly three tools,
returned not_signed_in without contacting Google and rejected path-shaped IDs.
Service/API tests use synthetic responses; they do not prove Gmail functionality.
Two upstream warnings were observed (Google datetime deprecation and Pydantic
lifespan annotation warning); neither failed protocol tests. No dependency patch.

## Exact packages and actual host tests

Packaging uses official openjiuwen-agentichub CLI0.0.1, fixed source
c8ee4ef44be0453470114aa5a19f4e1017462907, on a clean staging directory. Final
validation, ZIP inspection, preflight and source/native/wrapped byte equivalence
passed. Both archives contain the identical reviewed15-file native payload,
including all four full dependency license texts. No credentials, caches,
virtualenvs, tests or screenshots are packaged.
The repository packer's check/pack do not support agent-mcp and were not used.
The separate supported JavaScript preflight currently finds0 JS files/0 signatures.

Final regression run: **90 passed,2 upstream warnings** (31 auth,58 service,
1 real stdio protocol test). Token HTTP timeouts and concurrent configuration /
login reservation were included in the final fixes before these ZIPs were built.

| Form | Repository path | SHA-256 |
|---|---|---|
| Native | `test-packages/gmail-readonly-1.0.0-native.zip` | `b396d4adaedcfe48c7749570d777564482d50c9f23bfdc4d56b16b34a4051f52` |
| Canonical agent-mcp | `release/1.0.0/gmail-readonly-1.0.0-agent-mcp.zip` | `9fb5f0ad60109cbd3d8cafd8087475147808be711a46c5d07efeb2766f26f9a4` |

The exact native ZIP passed the existing host's actual load_mcp_package; wrapped
ZIP import returned200 and disconnected source=local_test, ID=local-test:gmail-readonly.
Import did not sign in. Explicit connect registered the real stdio server.
Actual running AgentServer list_tools discovered exactly the three declared
read-only tools. Actual calls returned version1.0.0/not_signed_in and
invalid_argument, with no Google requests. Disconnect caused MCP_NOT_FOUND;
reconnect restored registration. A native ZIP duplicate import returned400 with
a Chinese no-overwrite collision error. Installed15-file payload hashes equal
the canonical artifact map. Original host source hashes remained unchanged.

Browser-controlled visual inspection of Extensions → 连接器广场, filtered by
Gmail, showed Gmail 只读邮件连接器, native ID gmail-readonly, v1.0.0 and
**本地测试 · 未发布**. This was AI UI verification, not user manual acceptance or
authenticated Gmail evidence. The instance/card is left available for testing.
Whole-host restart persistence was not repeated, to preserve other services.
The later live follow-up verifies explicit credential refresh and authenticated
reconnect; real provider revocation/denied consent remain untested.

The gateway permits management RPC but not mcp_app.*; tool discovery/calls used
the existing running AgentServer RPC on28430, not a standalone harness and not a
model conversation. The connector-owned probe is tests/live_backend.py. No
provider content or credentials are written by that probe.

## Still required

1. Desktop client configuration is complete locally. Successful live calls
   establish Gmail API access for this client and the two tested accounts.
   Cloud Console settings, broader account eligibility, verification status and
   project billing/quota settings were not independently inspected.
2. Authorization received for the newest five messages in each of two accounts;
   keep further calls within that boundary. Whole-thread reads require additional
   authority when they could retrieve older messages.
3. Real browser sign-in/callback, bounded search/message reads, the specifically
   authorized second-account thread, explicit live refresh, reconnect and local
   logout have passed. User manual acceptance was confirmed on 2026-11-11.
   Real denied/revoked access and natural-expiry scenarios remain unverified;
   the user explicitly authorized GitHub delivery with the first two untested.
4. Native v1.0.0 user testing completion is confirmed and six originals are
   preserved. Canonical-wrapper confirmation is also received. The user explicitly
   accepts live denied-consent/revocation as untested for this handoff. Required
   PR attachments/link verification, CI and clean delivery review remain before merge.

## Desktop client configuration follow-up — 2026-11-10

The user supplied a local Desktop OAuth JSON path in the current conversation.
The existing launcher configure command succeeded. The protected copy was
compared in memory against the validated source subset; directory mode700,
client file mode600 and current-user ownership passed. No credential values,
client identifier, JSON contents or credential-file fingerprint were recorded
in repository evidence. The original downloaded file was left unchanged.
The runtime had no access/refresh token and no login in progress afterward.
No Google request, browser sign-in or mailbox access occurred. The native and
canonical ZIPs and runtime payload are unchanged. Only report/artifact metadata
was updated; user account/message authorization is the next gate.

## Authorized live integration follow-up — 2026-11-10

The user explicitly authorized two named test accounts, followed by “Authorize
newest five per account” in the current conversation. Repository evidence uses
test-account-1/test-account-2 aliases; actual addresses remain in the conversation
and are not copied into packages or shared tracker narrative. This authorization
does not include sending, mailbox mutations or older messages in entire threads.

The user-directed first-account browser sign-in completed using the existing
connector helper: real Google authorization/code exchange, automatic loopback
callback and a protected credential saved successfully. No password, code or
token was pasted. The helper's output was captured in memory and only its
sanitized final status emitted; authorization URLs and tokens were not logged
to repository files. Selection of the first account was user-directed; this
package does not expose a profile/identity API and no independent profile call
was made.

Through the existing running WorkSwarm AgentServer MCP:

- Search with max_results5 returned5 message IDs. The selected messages' dates
  were descending. No messages outside that returned set were read in this
  initial pass.
- All5 gmail_read_message calls succeeded with plugin version1.0.0, bounded to
  3000 body characters each; none was truncated. Subject presence and expected
  recipient-header corroboration were checked privately (4 of5 To headers
  matched the user-directed first account). Headers are corroboration, not
  independent OAuth identity proof.
- Only aggregate results were emitted. No message IDs, subjects, message bodies,
  credential values or raw provider replies were recorded in repository evidence.
- No mailbox write operation was invoked. Independent Gmail UI state comparison
  and the user's full manual-testing confirmation remain pending.

The user subsequently authorized the single thread containing the newest message
in test-account-2. No other full thread is authorized or was fetched.

First-account lifecycle checks passed: a real Google refresh through the existing
StoredCredentials handler saved refreshed credentials privately; actual backend
disconnect caused MCP_NOT_FOUND, reconnect discovered exactly3 tools, and a read
of the same in-memory message ID returned identical bounded text and labels.
This compares the returned text/labels, not complete-message integrity or all
mailbox state. Explicit local logout succeeded; the next actual backend call
returned not_signed_in. This confirms the credential guard, not an independent
network trace. First-account Google consent was not revoked.

The user completed a second real browser OAuth/code exchange and automatic
loopback callback. Actual WorkSwarm MCP then returned5 IDs and5 successful
bounded message reads for test-account-2, plugin1.0.0; dates descended and no
returned body was truncated at3000 characters. All5 To-header corroboration
checks matched the user-directed second account. No profile API was called.
The specifically authorized newest-message thread was fetched with display
limits5 messages/6000 characters:1 message available and returned, no truncation,
matching thread ID and containing the newest message. No other thread was read.

Second-account explicit live refresh, actual backend disconnect/MCP_NOT_FOUND,
reconnect/three-tool discovery, and rereading the same first message passed;
the bounded text and labels matched the pre-refresh observation. The second
credential is left in protected local storage and its MCP connected for manual
testing; the first account's local token was removed before this second login.
Only one account is active at a time. No provider consent revocation, mailbox
write, sending/draft/delete/label/mark-read action, paid/model call, host change
or delivery action was performed. Provider-side revocation/denied consent,
natural token-expiry behavior, whole-host restart and full user acceptance remain
unverified. No raw mail, IDs, subjects, bodies or tokens were added to evidence.
Both ZIPs and all15 payload files are unchanged.


## Submission gate follow-up — 2026-11-11

Both exact v1.0.0 ZIPs are explicitly confirmed by the user; six original images
are preserved with full dimensions and SHA-256 inventory in USER_TEST_CONFIRMATION.md.
Images 1-4 are WorkSwarm conversation-result evidence; assistant prose in those
images does not independently prove backend invocation. Images 5-6 corroborate
Gmail page content only. Actual AgentServer MCP discovery/read evidence remains
separately recorded above. No mailbox data is transcribed into tracker/PR prose.

The current connector preserves genuine Gmail MCP functionality, but WorkSwarm's
Connect button cannot launch its Google OAuth helper, display the connected
account, or provide connector-specific Sign out through package-only changes.
The existing CLI OAuth interface cannot support these controls while preserving
the current MCP tool registration. Completing this UI workflow requires separate
WorkSwarm frontend/backend integration, outside this task's authorized scope.

Real denied-consent and provider-revocation checks remain untested; user explicitly
instructed proceeding with merge on that basis. Natural-expiry, whole-host restart,
production Google app verification, Windows/Linux and unmodified-host runtime
installation remain unverified as documented. No package/runtime change was made;
90 existing offline/protocol checks and prior actual backend tests are reused.

## v1.1.0 desktop connection update — 2026-11-11

Task AH-20261111-gmail-connection, based on the merged v1.0.0 package. macOS
arm64, Python 3.11.17, isolated WorkSwarm develop checkout at base 02b7735
with the matching host changes. WorkSwarm 0.2.8 installed on this machine
is the released baseline and does not include this host change.

- Connector regression suite: 91 passed, including real loopback HTTP and
  state/PKCE validation with a synthetic Google exchange and the empty-text
  MIME alternative regression. The independent dependency install and
  runtime version check passed.
- WorkSwarm MCP unit tests: 452 passed.
- With the staged payload, the actual local AgentServer WebSocket handled
  Connect, Cancel, synthetic consent denial, callback and auth completion,
  tool discovery, and Disconnect. A disabled stdio entry point returned
  MCP_UNREACHABLE after OAuth without promoting the connection to connected.
  All three MCP tools ran against synthetic provider data. A Chinese query
  and HTML-only Chinese body survived the protocol and GET-only Gmail calls
  were verified.
- Google token exchange and mail responses were simulated. No real OAuth
  consent, account data, packaged desktop UI, Windows/Linux or remote
  multi-user deployment was tested for v1.1.0. Current-package user
  confirmation and screenshots are pending.

Both exact v1.1.0 archives were also tested. The official Agentic Hub CLI
0.0.1 validated and packed the wrapper. The source and both extracted
payloads matched byte-for-byte. The real WorkSwarm Hub downloader and
installer validated each ZIP checksum, extracted and installed it into
an isolated workspace from locally supplied bytes, and persisted the
install record. The AgentServer WebSocket tests above passed for each
ZIP, including a successful retry after restoring the disabled stdio
entry point. Both exact-package tests confirmed the synthetic session tokens were removed.

- Native SHA-256 `325dff13976634ae857dd70dbddd40d0feb0b5e7d658ac5ecd4556f94bfd451e`
- Agentic Hub SHA-256 `53e357e0588cbf41cec8c693c4266d6e3b63aaa717ef8032731ad453d39fa90e`

## v1.2.0 CLI + Skill update — 2026-11-11

Task AH-20261111-gmail-connection continues. The unmodified WorkSwarm
0.2.8 executable from the installed macOS app ran in an isolated workspace
with a local model fixture and synthetic Google responses. The package's
one-time CLI setup installed the hash-pinned dependencies and an executable
available to the host and chat command tool. The WorkSwarm connector RPC
returned a Google authorization URL. Real loopback HTTP, synthetic token
exchange, skill installation and disconnect clearing local credentials
passed. An actual WorkSwarm chat produced three successful CLI tool results
and the mock transport recorded exactly one GET each for message search,
message read and thread read. The provider and the model response were test
fixtures. Google consent and a live test account remain pending.

CLI regression suite: 93 passed. macOS arm64 and Python 3.11.17 were used.
WorkSwarm desktop source and the existing app profile were kept intact.

Both exact ZIPs were validated and packed with Agentic Hub CLI 0.0.1, then
staged from the ZIP into separate isolated WorkSwarm workspaces. The
unmodified installed 0.2.8 AgentServer loaded both manifests and installed
the Gmail skill after the local OAuth callback. The model fixture invoked
the actual skill tool and then the three CLI commands. It received the
Chinese search result and the HTML-only Chinese body from the synthetic
provider. The CLI never issued a mailbox write.

Using the frontend shipped with the installed 0.2.8 app and the native
payload, the connector marketplace showed the Gmail card with Connect.
Clicking Connect triggered the authorization RPC and callback listener.
After a synthetic browser response, the same card changed to Use. The
packaged frontend also rendered the completed synthetic chat in history.
This proves the local card and chat wiring for 0.2.8. Live Google consent
and mailbox access still require the test Desktop OAuth client JSON.
User acceptance and delivery screenshots are pending.


After clarifying the logout instruction, both final ZIPs passed the
same stock 0.2.8 authorization and chat tests. Runtime code and the
card metadata are identical to the frontend test.

- native SHA-256 `95a82b633a225c87edd3ceb52f8df14f796ce40b86bcef8aeb43212598a8532f`
- agent-mcp_wrapped SHA-256 `66ba19c4430aab8032a759532303a42e1e13198d3b1c685fa98c4dc2d100f602`

## v1.3.0 CLI draft editing, send and reply — 2026-11-11

Task AH-20261111-gmail-connection. Build scope is the Agentic Hub
connector. Google Desktop authorization now requests `gmail.readonly`
and `gmail.compose`. Existing read-only grants continue to work for reads
and reject writes until the new consent is granted. Added draft list and
preview, draft editing, send new mail or an existing draft, and threaded
reply. The Chinese display name is Gmail 邮件连接器, with the existing
`gmail-readonly` identifier and command retained.

- 112 connector tests passed, including prior token migration, partial
  consent rejection, compose gating, MIME attachment preservation,
  draft subject/thread handling, address injection rejection, reply
  headers, route allowlisting, and uncertain writes without retry.
- The official Agentic Hub CLI validated both packaging forms and verified
  the extracted payload equality. Both final ZIPs were then staged in
  separate local instances using the installed macOS WorkSwarm 0.2.8
  executable. The connector returned a Google authorization URL requesting
  both scopes and PKCE. A real loopback HTTP callback was completed against
  a synthetic OAuth exchange.
- The actual WorkSwarm chat runtime loaded the skill and ran the CLI via
  its command tool using a local deterministic model fixture. A synthetic
  Gmail transport independently verified draft lookup, draft update with
  the existing attachment retained, new send, reply MIME and original
  thread identifier, and sending the edited draft. Each fixture write was
  invoked once. Disconnect cleared the synthetic token.
- Real Google consent and live Gmail writes remain untested. The scope
  change requires test-user consent for the current package. No real
  email was sent or modified.

- native SHA-256 `12417e74e4be1a2a7eca4c12ab49f0eb7b294522d81cdd354393bb6e37968e25`
- agent-mcp_wrapped SHA-256 `38856c6b8d86058ad37969817637585cc704cd03ba4c08f6c51e720502adc863`

### Live Gmail validation on WorkSwarm 0.2.8 — 2026-11-11

The exact native v1.3.0 ZIP was staged in an isolated workspace of the
installed macOS WorkSwarm 0.2.8 runtime. My First Project was used with an
external Google OAuth test user and a Desktop client. The card's actual
connection request opened Google consent for `gmail.readonly` and
`gmail.compose`. The user granted both scopes, the loopback callback saved
credentials, and WorkSwarm reported the connector connected with its skill
installed. The Gmail profile matched the selected account before writes.

WorkSwarm chat loaded the Gmail skill and executed each command below
once successfully. Gmail API readback independently confirmed the results.

- `edit-draft` changed the subject and body of a dedicated test draft.
  The same draft ID and sole self-recipient were preserved.
- `send` sent one new test mail to the authenticated account. Gmail
  returned the expected subject, body and `SENT` label.
- `reply` sent one reply to the same account. Gmail returned the expected
  reply body and `SENT` label, with the original Gmail thread ID.

A deterministic local model fixture selected the commands. Google OAuth
and the mailbox operations used Google's live services. The draft edit
was confirmed from Gmail after a test-harness parsing failure, then the
remaining commands ran in a fresh isolated WorkSwarm workspace to avoid
a cached model endpoint. The dedicated draft was left in Drafts and the
two test messages were left in the same conversation. This run covers
the native ZIP and does not establish user acceptance or verify chat
behavior with a production model.

## v1.4.0 clean macOS WorkSwarm 0.2.8 Hub install — 2026-11-12

Task AH-20261111-gmail-connection. Installed WorkSwarm 0.2.8 backend
binary, isolated home and WorkSwarm data root (including spaces), and an
existing Python 3.11.17 on PATH. No Gmail CLI, venv, OAuth client JSON or
token existed in the profile. The test pointed WorkSwarm at a loopback
Hub API serving the exact wrapped ZIP. The unmodified backend handled
catalog lookup, checksum-verified download, extraction, `mcp.install`
and the card's `mcp.connect` RPC. The production Hub did not host this
test build and the Electron card was not clicked in this run.

- v1.3.0 downloaded and extracted but connect returned
  `MCP_CLI_INCOMPLETE` because the Gmail command was absent from PATH.
- v1.4.0 automatically created its private venv and installed the pinned
  dependencies. WorkSwarm recognized the CLI version and proceeded to
  authentication with no global CLI or manual prepare. An earlier
  local build exposed a WorkSwarm 0.2.8 behavior: it parsed the version
  in failed CLI output and skipped init. The final build emits no
  version when its runtime probe fails.
- The clean v1.4.0 run returned no browser URL and no token. Direct
  invocation of the same installed CLI returned
  `client_config_required`. No file was imported in this run.
  Against Google's live token endpoint for the team's Desktop client,
  both authorization-code and refresh requests using dummy grants were
  rejected for a missing `client_secret` when it was omitted. With the
  secret supplied, Google instead rejected the dummy grant. No real
  tokens were issued, and the Google project remained in Testing.
- In a separate control with pre-provisioned synthetic credentials and
  a mocked token endpoint, the same v1.4.0 ZIP returned the Google URL
  with PKCE and both Gmail scopes, accepted a loopback HTTP callback,
  reported connected with the skill installed, and cleared the local
  token on disconnect. This was not real Google consent.
- 113 connector tests passed. Official Agentic Hub CLI v0.0.1
  validation and packaging, JavaScript preflight, and native/wrapped
  payload equivalence passed. The actual Hub installation RPC used the
  wrapped artifact.

- Native SHA-256 `013db2354ce6ba6f046ea4bffbe7dc0d0636223c26575dcd206bb65ed97e24c7`
- Wrapped SHA-256 `716d16c5929343b3a16e916534264917c099d5e7c939df283da8fdfac378b280`

## v1.5.0 managed Google Workspace OAuth — 2026-11-12

Task AH-20261111-gmail-connection. Tested the exact wrapped ZIP on the
installed, unmodified macOS WorkSwarm 0.2.8 backend in an isolated
workspace. A local HTTP fixture supplied Hub catalog data and the exact
ZIP to the real WorkSwarm download and install handlers. The test profile
had no preinstalled Gmail CLI, no imported OAuth JSON, and no existing
session. Python 3.11.17 was already available. The test host was configured
with the temporary OAuth service origin. End users of a production build
will obtain that public origin from the package.

- WorkSwarm downloaded and verified the ZIP, prepared the bundled CLI,
  and returned the Google authorization URL from the card's Connect RPC.
  The service received an HTTP callback, consumed its state, and issued
  the session result only to the originating CLI. WorkSwarm reported
  connected and loaded the Gmail skill. A synthetic Gmail read then
  used the real broker token endpoint and confirmed Chinese content.
  Disconnect cleared both the local proof and the broker session.
- Repeated the exact package flow with live Google authorization and
  Google's real token endpoint. Safari showed Google's account chooser.
  Song Haoran selected the existing test account for My First Project
  and granted Gmail read and compose permissions. The test used the
  already registered Desktop OAuth client privately on the local broker
  and a loopback callback. Stock WorkSwarm reported connected and loaded
  the skill. The connector persisted the opaque broker proof without
  saving Google tokens or the client secret. Disconnect cleared both
  test session records. No live mail read or write was performed in
  this run.
- 113 connector regression tests and 5 service tests passed. The
  service tests covered callback state and replay, proof and service
  isolation, encrypted server records, denial, partial and excessive
  scopes, refresh, and independent disconnect. Drive and Calendar
  profiles were exercised using synthetic grants only.
- The broker used an in-memory test store. Production Firestore, Web
  OAuth credentials, the HTTPS domain, Google verification, and the
  public Hub installation are still pending. The test used the card
  backend protocol plus Safari rather than clicking the Electron card.

Official Agentic Hub CLI 0.0.1 validated and packed the wrapper. The
native and wrapped extracted payloads matched, and JavaScript preflight
passed. The wrapped artifact was used for both 0.2.8 integration runs.

- Native SHA-256 `42fdbcd6232eb417865deeb6c6e522ddc7759522665602e6f64e2e90be8ecc4c`
- Wrapped SHA-256 `4b74ed1397f59cfb5d4c462531555054b9d79fe385974717a6337c1dcadd4f43`

## Cloudflare Pages and D1 deployment adapter — 2026-11-13

Task AH-20261111-gmail-connection. The adapter preserves the connector's
existing endpoints, does not enter the Hub ZIP, and reuses the public pages
under `oauth-service/public`. Cloudflare workerd with local D1 exercised
authorization, a concurrent callback replay, per-service isolation,
encrypted token storage, read-only consent, refusal of additional scopes,
refresh, revocation, expiry cleanup and disconnect. Google token responses
were simulated. Wrangler 4.161.0 applied the D1 migration locally, served
the built homepage, privacy page and stylesheet, and exercised denial
and disconnect over HTTP through Pages routing. Production DNS, Google Web OAuth consent, Cloudflare
edge CPU usage and public Hub installation require live validation.

## v1.6.0 packaged team OAuth origin — 2026-11-13

Task AH-20261111-gmail-connection. The connector now defaults to
`https://google-auth.workswarm.app`. The team's listed Google test
account completed real Web OAuth against this endpoint in the v1.5.0
baseline with a test-only origin setting. The stock macOS WorkSwarm 0.2.8
backend reported a connected session and installed skill, and Gmail's
profile API returned HTTP 200. That session was removed from the host and
the OAuth service. The production endpoint's public pages and health
check are available over HTTPS.

The v1.6.0 connector suite passed 114 tests, including the card login's
default origin and no-local-client path. The final wrapped and native
archive hashes and packaging checks are recorded in
`release/1.6.0/artifact.json`. The official Hub install and Google
consent with this version are pending catalog availability.

After packaging, the installed macOS WorkSwarm 0.2.8 backend used a local
Hub catalog fixture to download the exact wrapped ZIP. The clean profile
had no CLI installation, client JSON, previous session, or origin
override. WorkSwarm prepared its CLI runtime and the explicit card
Connect RPC returned Google's authorization URL with the public
`/oauth/google/callback`, PKCE S256, and the two expected Gmail scopes.
The test canceled at the consent boundary. The upload ZIP SHA-256 is
`bdf596065f71f0fa14573a63d9713f9b3dc5b8610def51bbf498c000e583c7ae`.

The exact v1.6.0 ZIP also completed the real Google consent flow from
the local Hub fixture with an existing Python 3.11 added to the test
host's PATH. The production callback completed, the host installed the
skill and returned connected, and Gmail `users/me/profile` returned
HTTP 200 for the two requested scopes. The test session was disconnected
and removed. A subsequent run with the standard macOS PATH and Python
3.9 reproduced a bootstrap failure before authorization.

## v1.6.1 macOS interpreter discovery — 2026-11-13

The macOS card can now launch through the system Python and use a
supported Python 3.11 or 3.12 already installed in a standard location.
The connector defaults to the team's OAuth endpoint.

Official CLI validation and packaging, native/wrapped payload equivalence,
JavaScript preflight, and all 116 connector regression tests passed.
The exact wrapped ZIP was downloaded from the local Hub fixture by the
installed stock macOS WorkSwarm 0.2.8 backend. Its PATH contained only
standard system directories. The isolated profile had no existing CLI,
OAuth JSON, Gmail session, or origin override. WorkSwarm found the Mac's
existing Python 3.11 and prepared the private CLI runtime automatically.
The explicit Connect RPC returned a Google authorization URL with PKCE
and the packaged HTTPS callback. Song Haoran consented with the team test
account. The public callback completed, WorkSwarm returned connected
and installed the skill, both Gmail scopes were present, and Gmail
`users/me/profile` returned HTTP 200. Disconnect cleared the local and
broker test session. No mail was modified. The final ZIP hash is
`3f6c1de28aca1c2f271a9b25d2a6acca380d3a350c4609d2ed3b04cba32cc9b5`.
The desktop button UI and official Hub download remain pending.

## v1.5.1 user-managed Desktop OAuth — 2026-11-13

Task `AH-20261111-gmail-connection` (Song Haoran). This interim Hub
release uses the v1.6.1 interpreter discovery and Gmail CLI while
selecting a user-supplied Google Cloud Desktop OAuth client by default.
The team-managed v1.6.1 ZIP is retained for the later upgrade. WorkSwarm
source is unchanged. No user OAuth JSON is included in either archive.

117 connector regression tests passed using synthetic inputs, including
missing configuration, real Google OAuth library loopback/PKCE handling,
scope enforcement, draft updates, send/reply and disconnect. Real Google
authorization and Gmail use with v1.6.1 in Desktop mode were recorded
separately.

- The exact wrapped ZIP SHA-256 is
  `9140035cb10415cf88f4394ec9cf34f6642ef591052d66d48fcb705781f11f2e`.
  Official Hub CLI validation, native and wrapped preflight, and payload
  byte-equivalence checks passed. The extracted bundle contains the Chinese
  instructions and existing third-party notices and no OAuth client JSON or
  account credentials. Chinese search, message and reply inputs and localized
  help and errors are covered by the regression tests.
- Clean macOS WorkSwarm 0.2.8, using a local Hub fixture and its default PATH,
  installed the exact payload and prepared the CLI. Connect returned an auth
  error before configuration; the launcher reported the missing Desktop JSON
  with setup instructions. After importing an existing personal project client
  JSON, Connect generated a Google authorization URL with both Gmail scopes,
  PKCE and a localhost callback. The new Google consent did not complete
  during that run.
- Using the exact extracted package and an existing isolated Desktop grant,
  a real Gmail search and read-thread succeeded against a seeded test thread.
  Live draft changes, sends and replies were not performed with this ZIP.
  Official Hub installation, manual acceptance and current package screenshots
  are pending.

## Final v1.5.1 live retest and user confirmation · 2026-11-13

The exact 1.5.1 wrapped archive (SHA-256 9140035cb10415cf88f4394ec9cf34f6642ef591052d66d48fcb705781f11f2e) was downloaded and installed in an isolated stock macOS WorkSwarm 0.2.8 profile from a local Hub catalog fixture. The card's browser consent completed against Google with the user-provided Desktop OAuth project. The host reported connected and installed the skill, and the installed CLI performed a live Gmail search.

The first fresh authorization returned a different account, so the account guard stopped that write attempt. With the user's instruction to test self-addressed mail, the same installed CLI used a separate copy of the already authorized team test account grant. The fixture created a dedicated draft. The CLI updated it, read it back, confirmed a sole self recipient and empty Cc/Bcc, sent it, found and read it, and replied in the same thread. Gmail API readback confirmed both bodies, the thread ID and self-only recipients. The isolated copies of OAuth configuration and tokens were removed. One earlier seeded draft remained unsent after the test harness failed to locate its runtime; only the two successful test messages were sent.

The [original screenshot](evidence/1.5.1/self-addressed-thread.jpg) shows the two dedicated messages in Gmail. The user explicitly confirmed this exact version passed and approved public posting of this screenshot, recorded in RPT-20261113-gmail-connection-151-confirmed.

The final regression run passed all 117 tests on Python 3.11 with the locked Gmail dependencies. Public Hub installation remains pending. The tested package is the user-managed Desktop OAuth version.
