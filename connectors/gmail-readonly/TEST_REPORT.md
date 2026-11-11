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
