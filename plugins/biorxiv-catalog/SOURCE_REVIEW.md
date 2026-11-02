# Source and distribution review — bioRxiv catalog companion

Owner: Nguyen Trung Dung. Reviewed 2026-11-02, Asia/Singapore.
Task AH-20261102-biorxiv-catalog; Candidate CAND-CLD-274.
Mapping: bioRxiv -> 预印本目录助手 -> biorxiv-catalog; repo:agent-plugin:biorxiv-catalog.

## Source and actual reuse boundary

Pinned upstream: https://github.com/anthropics/knowledge-work-plugins/tree/2574e29377c7173d0cecffef29a6ecbd7f8ccb5d/bio-research.
The official directory identifies Anthropic as the connector publisher and says sign-in is not required:
https://claude.com/marketplace/connectors/biorxiv.

Only `bio-research/.mcp.json` is adapted, as payload `connection.json`: retain the official bioRxiv HTTP URL, omit the other ten services, and add a prominent dated modification notice. The configuration has no per-file copyright header. The upstream project/author identity is retained; no new upstream copyright owner/year is invented. Chinese ToolCard implementations, usage guide, validation and tests are original repository adapter work. Existing repository Domain/Percolate adapters were inspected as internal host-interface examples; no external server implementation was copied.

The nearest applicable `bio-research/LICENSE` is the complete Apache License 2.0 (Git blob d645695673349e3947e8e5ae42332d0ac3164cd7, 11358 source bytes). Root and bio-research directory inventories contain no NOTICE file or additional license for the adapted configuration. The root LICENSE has unrelated trailing text; this port uses the nearer, unmodified bio-research/LICENSE. Bundle it verbatim at `licenses/anthropic-bio-research/LICENSE`, retain the attribution and modification notice in connection.json and THIRD_PARTY_NOTICES.md, and record its actual final byte hash in provenance.json. Apache-2.0 permits this configuration adaptation subject to Section 4 retention, license-copy, change-notice and any applicable NOTICE requirements. Section 6 grants no general trademark rights. No upstream logo, icon, fonts, branding image, scientific Skill, agent prompt or backend implementation is copied.

## Hosted service, data and dependencies

Endpoint: https://hcls.mcp.claude.com/biorxiv/mcp. Protocol is Streamable HTTP MCP; current service identifies as biorxiv 3.2.0. Its actual seven-tool discovery is the compatibility reference, not the directory's older eight-tool listing. The directory and official connection configuration intentionally publish anonymous connector access. This is a client-only port, not a redistribution of the hosted server. No account, credentials, subscriptions or access bypass are added. Remote terms/availability/quotas can change; the client makes a user-requested bounded read with no automatic retries or bulk crawl.

Primary API documentation inspected: https://api.biorxiv.org/. It documents date/category/DOI/funder/publication endpoints and returns per-paper license fields. Funder coverage begins 2025-04-10. Preprints have not necessarily been peer reviewed. Article licenses vary; a successful test returned cc_by_nc_nd. The Apache license on integration configuration does not license papers, abstracts, served databases, API services or trademarks. No scientific paper, abstract, API dataset, audio/media or credentials enter the distributable ZIP. Source titles/authors/abstract/license values returned at runtime are preserved rather than relicensed. Test evidence committed to the repository contains bibliographic identifiers, field/count checks and response digests, not copied abstracts or full remote datasets.

MCP Python SDK (MIT), jsonschema (MIT) and their dependencies are imported from the host's separately installed environment, not bundled. openjiuwen is the host SDK and is not redistributed. The package requirements file states dependency ranges; no installer modifies host Python automatically. Tests record actual dependency versions. No third-party binary, vendored package, font or model weights are included.

## Functional overlap and boundaries

Paper Search Pro 857c5bc03bd848ca838c1b563734e85b@356ea33, Citation Management 1f4e4a2df62a40879bbbd77580973b99@356ea33, Literature Review 21acf82b61e14da08d87fe659575d27f@356ea33 and monitoring 1395c2191e7e49608fc277edf073a384@1.0.0 already cover general research entry points. This companion adds source-addressed preprint dates/categories/versions, publication links, funder ROR queries and source statistics to those workflows. It does not implement another generic review/writing pipeline, full-text download, clinical advice, research scoring or literature scheduler. Preserve Partial Overlap - Extend Existing Capability in the tracker.

## Final extraction review

Native extraction verified 2026-11-02: all nine runtime files match source byte-for-byte, the seven declared classes and Chinese Skill exist, and no cache, paper dataset, abstract, executable, media, credentials or upstream branding is present. The license is the exact original 11358-byte blob d645695673349e3947e8e5ae42332d0ac3164cd7; SHA-256 cfc7749b96f63bd31c3c42b5c471bf756814053e847c10f3eb003417bc523d30. Connection modification notice and THIRD_PARTY_NOTICES are present. Canonical-wrapper equality is recorded by the final archive verifier in TEST_REPORT.md. This source review does not establish user test completion or GitHub/Hub delivery.

## User-supplied screenshot evidence

Nine original user test PNGs received2026-11-02 are retained outside the runtime payload and embedded in the delivery PR. They show bibliographic metadata and short visible excerpts of actual source abstracts; this qualifies the earlier statement about identifier-only automated evidence, which still applies to tests/evidence JSON. No complete paper/abstract dataset or image evidence enters either ZIP. Original paper license fields remain visible and separate from the Apache configuration permission. USER_TEST_CONFIRMATION.md records explicit current-package completion and per-image limitations. Runtime, wrapper and both tested ZIP hashes are unchanged.
