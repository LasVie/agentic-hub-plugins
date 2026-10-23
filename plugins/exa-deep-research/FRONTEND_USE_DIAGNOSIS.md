# Frontend Use handoff: open investigation

Date: 2026-10-22. Task AH-20261022-exa-deep-research; candidate CAND-CLD-017.

The user clarified that their frontend has no plugin selection option and
that **Use** only navigates to the main page. The earlier recommendation to
find a manual selection switch was not verified against the user's UI.

## Verified behavior

- The running local frontend at http://127.0.0.1:5173/ serves WorkSwarm and
  `/assets/index-YOvyiWd9.js`, matching the checkout's existing build.
- PluginDetailPage calls `onUse(detail.runtimePackageName)`. App.tsx forwards
  that value as `initialEnabledPlugins` and forces single-agent mode. The new
  conversation code adds the plugin selection and transfers it to the real
  session before sending the first message. Navigation by itself is expected;
  a second manual selection should not be necessary.
- The source and served bundle contain that automatic handoff and a separate
  extension-picker implementation. Source presence does not prove that the
  picker is visible or usable in the user's rendered page.
- A diagnostic bundled the actual session/plugin stores and enabledExtensions
  helper with esbuild 0.21.5 and Node 24.19.0. With Exa installed and connected,
  adding Exa to the pending conversation and transferring it to a real session
  produced `plugin_names: ["exa-deep-research"]` as expected.
- In that state-module test, restoring an empty server equipment snapshot
  replaced the local selection with `[]`. This is a possible stale-snapshot
  race, not a proven explanation of the user's browser interaction.
- The earlier real backend test still verifies that the exact native ZIP's
  four tools mount correctly when the request includes its plugin ID.

## Remaining gap

No browser surface was available to this session's UI automation tools.
The real **Use** click, browser store changes and outgoing chat.send payload
have not been observed together. Do not assert that the user failed to select
the plugin or that the frontend activation defect has been fixed. The next
targeted check must capture the selection immediately after **Use**, after
session creation and in the outgoing chat.send request, including whether an
empty metadata response or disconnected catalog state removed it.

The supplied log also shows separate host IPC reconnection/delivery failures.
It contains neither an Exa import error nor the plugin-selection payload.
Only test instructions and diagnostic records changed. The runtime payload,
version 1.0.0 and ZIP hashes are unchanged. User test completion remains pending.

## Later confirmed host failure

The user subsequently supplied `equipment change rejected at non-fresh turn:
plugin set changed`. A regression reproduced that exact error under the real
Smart permission admission context with no competing turn. Admission's own
activity reservation was misclassified as a peer turn. The local JiuwenSwarm
host now distinguishes task-owned admission activity from real competitors.
All 68 targeted host tests and the real Exa native-ZIP Smart-admission mount
passed after the fix. See SMART_ADMISSION_FIX.md. This finding supersedes the
earlier speculation for this specific rejection; the UI retry and separate
IPC reconnection issue have not been declared resolved.
