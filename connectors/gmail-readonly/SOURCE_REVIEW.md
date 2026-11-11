# Gmail read-only Connector source review

Reviewed: 2026-11-10. Owner: Cai Zhenze. Task: `AH-20261110-gmail-readonly`.
Candidate: Not Applicable (independent, explicitly selected connector request).
Naming: **Gmail → Gmail 只读邮件连接器 → `gmail-readonly`**, version `1.0.0`.

## Decision and scope

Implementation mode is `native`: independently written connector code against
the public Gmail REST and Google installed-application OAuth interfaces, with
the maintained MCP Python SDK and Google authentication libraries as separately
installed dependencies. `NATIVE_DESIGN.md` owns the implementation requirements.
No existing Gmail asset or Workspace MCP implementation is copied or translated.
This review does not assign a new license to team-owned code or grant service,
trademark, user-data or publication rights.

The selected surface is bounded message search, message reading and thread
reading. The sole requested Google scope is
`https://www.googleapis.com/auth/gmail.readonly`. The connector's mailbox request
allowlist is GET-only `users/me/messages`, `users/me/messages/{id}` and
`users/me/threads/{id}`. OAuth authorization/token exchange is separate from that
mailbox allowlist. No sending, drafting, labeling, deleting, marking read,
attachment-download tool or arbitrary HTTP endpoint is included.

## Existing asset and maintained upstream assessment

- Existing catalog comparison: Gmail 邮件助手,
  `e4922fd9c9a54287957a2606728a46c4@1.0.0`, advertises overlapping Gmail operations.
  Its prior functional review is retained; its implementation reuse permission
  remains **unknown**. No code, prompts, media or package from that asset is
  reused. A new packaging/integration type alone is not a claim of new mailbox
  functionality; this is the user's selected Connector integration task.
- Maintained alternative:
  [google_workspace_mcp v2.4.0](https://github.com/taylorwilsdon/google_workspace_mcp/releases/tag/v2.4.0),
  commit `53c392dc426ca8795e27dcf0301f92b5abe85688`, dated 2026-11-08.
  The pinned [MIT license](https://github.com/taylorwilsdon/google_workspace_mcp/blob/53c392dc426ca8795e27dcf0301f92b5abe85688/LICENSE)
  names Copyright (c) 2025 Taylor Wilsdon. Its license hash is
  `6c1f0beeb232472e68f961f11a0bd1b98f21513ccdbb88770d392fc95f17149a`.
  Public source was downloaded to designated temporary research storage and
  statically inspected, not installed or executed.
- [`auth/scopes.py`](https://github.com/taylorwilsdon/google_workspace_mcp/blob/53c392dc426ca8795e27dcf0301f92b5abe85688/auth/scopes.py)
  adds `openid`, `userinfo.email` and `userinfo.profile` base scopes even with
  Gmail-only/read-only configuration. This does not meet an exact Gmail-only
  scope requirement without changing that server.
- [`main.py`](https://github.com/taylorwilsdon/google_workspace_mcp/blob/53c392dc426ca8795e27dcf0301f92b5abe85688/main.py)
  offers service/tier filtering and `--disabled-tools`.
  [`core/tool_registry.py`](https://github.com/taylorwilsdon/google_workspace_mcp/blob/53c392dc426ca8795e27dcf0301f92b5abe85688/core/tool_registry.py)
  removes write tools in read-only mode, but logs and continues on removal
  exceptions. Its normal interface is broader than a fixed three-tool boundary.
- [`gmail/gmail_tools.py`](https://github.com/taylorwilsdon/google_workspace_mcp/blob/53c392dc426ca8795e27dcf0301f92b5abe85688/gmail/gmail_tools.py)
  includes attachment/batch/label reads, raw MIME and full-message export, and
  unbounded thread output. A broad-server fork would need additional restrictions
  and regression coverage. No such fork is shipped.
- Its legacy stdio authentication supports browser OAuth, PKCE and a standalone
  callback listener. Local credential storage is permission-restricted JSON,
  not encrypted storage. Its broad multi-service dependencies and account
  selection machinery are unnecessary here. These are scope/maintenance reasons
  for the smaller implementation, **not a finding that MIT reuse is prohibited**.

Materials seen: public upstream implementation, license and configuration during
this audit; public service/SDK documentation; the existing catalog description
and earlier review. No permission-unknown implementation was supplied for
translation or adaptation. No upstream brand graphics, icons, fonts, mailbox
data or sample messages are included.

## Google authentication, service limits and prerequisites

The developer must prepare a Google Cloud project with Gmail API enabled,
consent branding/audience, an appropriate Desktop OAuth client, and authorized
test users when using an external Testing app. The connector-owned helper opens
the browser and uses a one-time loopback callback, state validation and PKCE;
the end user signs in and grants consent without pasting tokens. Developer
client preparation is distinct from user sign-in. Desktop clients are public
clients, not a place to protect a confidential application secret.
[Official Desktop OAuth specification](https://developers.google.com/identity/protocols/oauth2/native-app).

`gmail.readonly` is a **Restricted** scope. Public distribution needs the
applicable Google verification; server storage/transmission of restricted data
can require a security assessment. Workspace administrator policy may block
consent. This local package does not establish production approval or exempt
data subsequently passed through WorkSwarm/model services from policy review.
[Gmail scope requirements](https://developers.google.com/workspace/gmail/api/auth/scopes).
External Testing apps with Gmail scopes receive refresh tokens that expire
after seven days; revocation, password changes and administrator restrictions
can also end access. Reauthentication is an expected recovery case.
[Token expiry documentation](https://developers.google.com/identity/protocols/oauth2#expiration).

The official remote Gmail MCP service is **not selected**: its current guide
requires Developer Preview eligibility, Gmail MCP API enablement, an agentic
OAuth client and remote-MCP OAuth host support. The documented example requests
both Gmail read-only and compose access. That setup is not evidence that the
target WorkSwarm supports the same sign-in or an exactly read-only tool surface.
This local stdio server calls ordinary Gmail REST endpoints, not that preview
endpoint. [Official Gmail MCP setup](https://developers.google.com/workspace/gmail/api/guides/configure-mcp-server).

Cost check, 2026-11-10: Google's current Gmail API guide says standard use has no
additional cost and lists an 80,000,000 quota-unit daily project threshold;
overage charging is planned with at least 90 days' notice. Current method costs
include `messages.list` 5, `messages.get` 20 or 60 for full/raw/HTML, and
`threads.get` 40 or 120 for full. Shared project usage and billing configuration
have **not** been checked. Do not enable paid capacity or describe all possible
usage as free. No live Gmail requests were made in this source audit.
[Current Gmail quota/pricing documentation](https://developers.google.com/workspace/gmail/api/reference/quota).

## Dependency and distribution review

The inspected local runtime uses Python 3.12 with direct requirements
`mcp==1.25.0`, `google-auth-oauthlib==1.2.3`, `requests==2.32.5`; the resolved
runtime lock also pins `google-auth==2.41.1`. All 40 runtime distributions in
the lock matched the locally installed metadata during this review. Test-only
packages are excluded from the runtime inventory in `provenance.json`.

The delivered payload contains requirement pins/hashes and the independently
written connector, **not** dependency source, binaries, wheels or a virtualenv.
Installation of that private runtime is an explicit preparation action. This
review must be revisited before vendoring dependencies or supporting a different
resolved platform environment.

Full, unchanged license texts from the installed exact-version distributions
are included for these referenced libraries:

| Distribution | License | Evidence inside native payload |
| --- | --- | --- |
| MCP Python SDK 1.25.0 | MIT; Copyright (c) 2024 Anthropic, PBC | `licenses/mcp/LICENSE` |
| google-auth-oauthlib 1.2.3 | Apache-2.0; Google LLC file headers | `licenses/google-auth-oauthlib/LICENSE` |
| google-auth 2.41.1 | Apache-2.0; Google LLC file headers | `licenses/google-auth/LICENSE` |
| Requests 2.32.5 | Apache-2.0; distribution author Kenneth Reitz | `licenses/requests/LICENSE` |

No separate NOTICE was present in these four installed distributions' metadata
file lists. No dependency files were modified. `THIRD_PARTY_NOTICES.md` explains
the non-vendored use; `provenance.json` records exact license hashes and all
runtime dependency metadata/license evidence hashes.

The transitive metadata includes MIT, MIT-0, Apache-2.0, BSD-2/3-Clause, ISC,
PSF-2.0, dual `Apache-2.0 OR BSD-3-Clause` (cryptography), and **MPL-2.0
(Certifi)**. Do not describe this as an entirely permissive or copyleft-free
dependency graph. `pyasn1-modules` metadata says BSD; its installed full license
contains the two redistribution clauses. This is a metadata/license-file audit
of the locked runtime, not an exhaustive embedded-code license or security
audit of every wheel. No broader redistribution conclusion is asserted.

## Integration and verification boundary

Native integration is `package_type: mcp` / `agent-mcp` / `stdio-mcp` with a
single local server. Browser authorization is handled explicitly by the
connector's own helper; no host-managed OAuth/token-schema capability is
claimed. The actual catalog/install route and running-host tests belong in
`TEST_REPORT.md`, not inferred from this source audit. No host/core/SDK patch is
part of the connector payload.

This review verifies source provenance, design suitability, installed dependency
versions and license evidence only. It does **not** establish Google consent,
callback success, mailbox access, token refresh, administrator approval,
production verification, or user manual testing. Real Google tests remain
blocked pending developer client setup and explicit test-account/data authority.
Final extracted ZIP contents and license hashes must be checked by packaging
verification and recorded against its exact artifact hash before handoff.

Final package inspection, 2026-11-10: official CLI validation/pack and both
extracted payload maps passed; all15 runtime files match source/native/wrapped
bytes. The four license texts match `license_reference_files` in provenance.
Native ZIP `test-packages/gmail-readonly-1.0.0-native.zip` SHA-256
`b396d4adaedcfe48c7749570d777564482d50c9f23bfdc4d56b16b34a4051f52`;
canonical `release/1.0.0/gmail-readonly-1.0.0-agent-mcp.zip` SHA-256
`9fb5f0ad60109cbd3d8cafd8087475147808be711a46c5d07efeb2766f26f9a4`.
Neither archive contains a Google client, token, account data, dependency wheel,
runtime environment or screenshot. Authentication acceptance remains pending.
