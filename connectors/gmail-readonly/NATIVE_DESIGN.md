# Gmail read-only Connector design

Owner: Cai Zhenze. Task: AH-20261110-gmail-readonly. Candidate: Not Applicable.

The user selected Gmail search and message/thread reading on 2026-11-10.
This independently written integration follows the public Gmail REST and Google
installed-application OAuth specifications. It does not translate the unlicensed
catalogue Gmail plugin. That plugin's functional description and prior review
findings were seen; its implementation is not reused.

The maintained MIT google_workspace_mcp 2.4.0 at
53c392dc426ca8795e27dcf0301f92b5abe85688 was assessed. Its broad multi-service
configuration, identity scopes, subtractive tool filtering and unbounded thread /
raw-message export behavior do not fit the selected boundary without a larger
fork. No upstream implementation files are copied.

## Boundaries

- Genuine MCP stdio with exactly three bounded read tools. Gmail API requests
  use only GET on users/me/messages, messages/{id}, and threads/{id}.
- Request only gmail.readonly, with a developer-owned Desktop OAuth client,
  PKCE, state validation and a one-time 127.0.0.1 loopback callback. Browser login
  is explicit and separate from import / MCP initialization. No token paste.
- Credentials and the separately prepared Python runtime live in a private
  per-user directory outside the payload/repository. No automatic dependency
  installation or login during import or connection. The helper's prepare and
  configure commands are explicit developer operations.
- Email bodies are untrusted original data, never executable HTML or agent
  instructions. No remote image loading, attachment download, content logging,
  send/draft/label/delete/mark-read API or arbitrary HTTP tool.
- Local sign-out removes the local credential session; provider consent
  revocation is a separate user action. New operations load current credential
  state. An operation already in flight may finish.

## Host integration

Use the existing modified local host at 6411, native stdio-mcp manifest and its
local ZIP importer. The host's cli integration does not currently load hybrid
mcp.json server_config; do not rely on its stale hybrid comment or modify it.
The packaged helper opens Google's browser flow directly; the user then clicks
Connect. Genuine tool initialization/discovery can occur without credentials;
mail reads fail closed until sign-in. No Outlook identity or Hub asset ID.

## Verification

Mock tests cover read-only endpoint/tool allowlists, bounds, MIME handling,
sanitized errors, OAuth scopes/PKCE/callback arguments, private storage,
credential refresh and local disconnect. Real stdio and the running backend
verify tool discovery and missing-credential rejection without mailbox access.
Actual Google consent/callback, authorized mailbox reads, provider revocation and
refresh remain blocked until developer setup and user test-data authorization.
