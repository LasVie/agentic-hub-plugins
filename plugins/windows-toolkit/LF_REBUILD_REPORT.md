# PR42 packaging repair and tracker handoff

Task `AH-20261023-dsh-win-toolkit`; candidate `CAND-DSH-019`; owner Nguyen Trung Dung.
Original PR: https://github.com/LasVie/agentic-hub-plugins/pull/42
Original head: `8f21e91505e0f3689d8b46496c22809cd5af0feb`.

The original package-contract failure is genuine. A fresh checkout with
`core.autocrlf=false` reproduces `current source and release ZIP differ`.
The manifest has 0 CRLF pairs / 4,221 bytes in source and 117 pairs / 4,338 bytes
inside the ZIP. All five non-license files differ only by CRLF normalization;
the license already uses exact LF bytes. Both original archives have identical
native payloads, but those bytes do not match their Git source. The old
`source_zip_payload_identical` finding described the former CRLF working copy,
not a clean LF clone; it must not be propagated as clean-checkout evidence.

## Repair prepared locally

- Build from LF source; scoped `.gitattributes` preserves those text bytes on
  clients with either autocrlf setting and leaves ZIP/PNG originals binary.
- Use **1.0.1** because the packer rejects a changed ZIP under an existing
  version. Preserve both original 1.0.0 archives and confirmation history.
- Regenerate the canonical release, artifact.json and flat native importer ZIP.
- Verify all six payload files against source and both archives, UTF-8/LF,
  ZIP CRCs, safe paths, original MIT hash, deterministic output and unchanged
  Python AST. Only line endings and manifest.version change.
- Preserve `display_name.en = Windows Toolkit`. Its English rendering is
  the host's locale choice; it is not a compliance gap.

Native package: `test-packages/windows-toolkit-1.0.1-native.zip`.
SHA-256: `18c6b8d439992404bb308ac37084405a92869d38523c64d473dbf42d499421d4`.

Canonical package: `releases/agent-plugin/windows-toolkit/1.0.1/windows-toolkit-1.0.1.zip`.
SHA-256: `844450ba04d52481dbdb762eb515ddca4fcea179a1191f82d33f8a0a90b874a4`.

Source and extracted-package read-only direct checks: **7/7 each PASS**.
They use real Tool classes and PowerShell; no service mock is substituted.
Clipboard write/notification were not repeated; the original evidence remains
historical. `test_playground`: **4/4 PASS** in the LF checkout.
Current package/repository check and fresh-checkout evidence are recorded in
`packaging-repair-verification.json` and `package-verification.json`.

The previous assertion that check-repo or test_playground fails on clean
origin/main is withdrawn. The original checkout/clone was flawed. No unrelated
main asset is changed to hide this packaging defect.

## Tracker issue — actual saved state inspected

Locate **AH-20261023-message-quota-audit**, owner **Cai Zhenze**, by stable Task ID
immediately before any repair. It was row 36 when inspected, but row numbers
are not stable. Its persisted malformed values were confirmed through the
Sheets API, so they are not merely unsaved DOM editor text:

- Status: `Ready for TestingSubmittingReady for Testing`.
- Acceptance: `Pending AcceptancePending AcceptancePending Acceptance`.
- PR and Test Screenshot are blank. ID, task name, owner and types are intact.

The user specifically requests **dropdown selection in the UI**. Do not type
replacement strings, use Ctrl+A in a cell editor, or treat unsaved DOM content
as proof of persistence. Intended valid selections are **Ready for Testing**
and **Pending Acceptance**. Re-read the task by ID afterward and confirm both
saved values and the neighboring fields.

This session's UI inventory exposes no apps/browsers; opening the in-app browser
returns `Browser is not available: iab`. The two cells have therefore not been
modified by this repair. Direct Sheets API replacement is a possible alternative
only if the user permits that change of method; it should replace the two
userEnteredValue fields atomically after fresh ID/owner lookup and verify the
server readback. No broad row rewrite, clearing/retyping or overwrite of another
contributor's legitimate progress is authorized.

## Remaining delivery gates

Current 1.0.1 user completion is pending under AGENTS.md's changed-package rule.
The original seven screenshots and 1.0.0 confirmation remain preserved; they
are not represented as fresh 1.0.1 frontend testing. After explicit current
confirmation, update PR42 and all current-version/hash records, verify original
evidence links and required CI, merge under the existing authorization, then
delete only the eligible temporary source branch. Leave Project Lead acceptance
pending and Asset Ledger unchanged until their separate requirements are met.
