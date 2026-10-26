# Percolate source and reuse review

Task AH-20261026-coffee-brewing-research; Candidate CAND-CLD-134; owner Nguyen Trung Dung.
Naming: Percolate → **咖啡选豆与冲煮** → `coffee-brewing-research`.
Stable ID: `repo:agent-plugin:coffee-brewing-research`.

## Capability comparison

Compared the live ledger and current development/merged records on 2026-10-26, including nutrition-coach
`b9df8da195e846beb39de954e8d28fe4`@1.0.0, meal planner `ddb4dcbf3bb6417da30f4e74b27af17d`@1.0.0 and
travel-guide-team `5929eb9690d9453bb459b5ac33ab6d88`@1.0.0. Their declared generic meal/nutrition/travel plans do
not expose a specialty-coffee catalog with real IDs, paired tasting profiles and brew-method dial-in evidence.
Outcome: Confirmed New Capability for that bounded public research scope, not a provider-name-only change.
No matching claimed task/delivery was found; candidate claim and task were registered before implementation.

## Pinned materials and permission

Source: https://github.com/bguillow-rgb/timberline-plugins/tree/a9c0c687825e61b567fb1a03cba0992cbf9393bc/percolate

Commit `a9c0c687825e61b567fb1a03cba0992cbf9393bc`; integration manifest **1.0.0**.
Actual hosted MCP reported **1.0.2**, protocol **2025-03-26**, eight tools. These are separate versions.
The recursive Git tree was complete (`truncated=false`). The selected subtree contains manifests, README,
Skill, full license and logo; root and selected-package license copies are identical. No NOTICE was present
in the complete tree. Other three product packages are outside the reused scope.

| Delivered path | Actual upstream material | Review and changes |
| --- | --- | --- |
| README.md | percolate/README.md, blob 79f854c6a8855e25485c27f9521f7145c0775f91 | MIT; Chinese installation/scope/evidence rewrite |
| skills/coffee-picks/SKILL.md | same relative upstream Skill, blob 4f3d070e7c2d146c898aef6b5178db55d4563ce1 | MIT; Chinese workflow, native names, validation/privacy boundaries |
| licenses/timberline-percolate/LICENSE | root/percolate full MIT, blob 673965950cb5e9ab4540da118b645d9772f178eb | Exact 1080 original bytes, original copyright and disclaimer |
| tools/coffee_tools.py | Public interface requirements; repository-native Tool/ToolCard pattern | Client adapter, not copied hosted implementation |
| tools/tool_catalog.json and references/api.md | Actual published MCP schema/functional interface | Chinese field explanations; compatible keys/enums retained |

Original copyright: **Copyright (c) 2026 Timberline Ventures LLC**.
Bundled license SHA-256: `23aa04bfd21c572e8aebb500ba5d841a5d0318419b8e05495e9474df1687a54b`.
`mode=ported`, `permission_status=verified` applies to the actual MIT README/Skill reuse.
Complete original license and THIRD_PARTY_NOTICES.md are inside the runtime payload.

## Separate assets, data, service and dependencies

No logo, product images, private server implementation, database, market/query results, credentials, model
or third-party runtime is distributed. Trademarks/names are informational source/record identifiers only.
The host supplies openJiuwen, MCP SDK, httpx and jsonschema; their implementations are not copied.

The publisher's public MCP page, terms and privacy pages were fetched directly on 2026-10-26 after the web
reader could not load them. Actual HTTPS 200 pages redirected to `www.percolateapp.com`; local HTML evidence
is ignored under `.research/coffee-brewing-research`. MCP page permits public read-only no-account lookup,
60 calls/minute and quoting with Percolate attribution. Terms prohibit abuse/scraping/reverse-engineering;
this package only makes bounded intended MCP calls, does not copy the dataset or implement the server.
Data/brand rights remain separate; a citation permission is not permission to redistribute the catalog.
Terms say recommendations are starting points and price/freshness/batch details can vary.

Privacy section 11 documents tool/argument/client/result-count logs (90 days), per-IP rate counters (three
days), and analytics. No personal collection or app account is available through this MCP. The adapter
passes only declared arguments, rejects extra fields before network, and does not read files/conversation.
Cards conservatively disable automatic replay/parallel safety despite upstream read-only/idempotent hints.

## Test/release stage

The reviewed Chinese runtime must be tested and extracted before Ready for Testing. Actual results and
final hashes are recorded in TEST_REPORT.md and package-verification.json after those steps occur.
Nguyen Trung Dung explicitly confirmed the unchanged current Chinese 1.0.0 package with “Confirmed working”
on 2026-10-26 and supplied eight original screenshots. USER_TEST_CONFIRMATION.md records exact hashes,
Report ID and image scope/limits. Complete materials now permit Submit; actual evidence/CI verification
is required before merge. This source review alone does not establish user testing or Hub publication.

## Final package verification

Eight source/native/canonical/extracted runtime files match byte-for-byte; UTF-8/LF/no BOM and both ZIP CRC/path checks pass.
Native SHA-256 `f7b178268153b8075460d5ba6e1ae1f72ab8e2dd1106576596eb54f2e916bb4b`; canonical
`974eacf436ce73b99571e03c30b41877b6a7318609bf73f5b84badfc8ecd31ea`.
Original 1080-byte MIT blob and SHA-256 match the pinned source. Chinese original-name lookup guidance and pods/format
limits were added before these ZIPs were created. Subsequent outer test-report/metadata changes do not change runtime bytes.
Actual source/extracted SDK, hosted service and real-agent evidence is in TEST_REPORT.md / host-verification.json.
Current-package user confirmation and eight original screenshots are recorded in USER_TEST_CONFIRMATION.md
and evidence/1.0.0/evidence.json. Actual GitHub delivery is recorded separately after creation/verification.
