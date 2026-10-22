# Source and distribution review

Task `AH-20261022-learning-output-style`; candidate `CAND-ANT-037`; owner Gan Mingrui. Reviewed 2026-10-22.

## Confirmed input and required correction

Gan Mingrui supplied `learning-output-style_1.0.0.zip` and confirmed in the current conversation: “I have verified on this, please proceed with the uploading”. Its SHA-256 is `7e119eb95893e2a379c100d69f349a619a342c44dcf658c9ca80124020e96631`. The attachment and existing workspace ZIP are byte-identical. The original confirmation is recorded as `RPT-20261022-learning-output-style-confirmation`.

That ZIP is a native host package with no marketplace wrapper and no declared Skill/tool/rail/MCP capability. It contains full Apache texts and an adaptation NOTICE, but lacks the current repository's per-source license paths, THIRD_PARTY_NOTICES.md, and file-level change notices for the extracted prompt. It also contains unused hidden upstream metadata that the current packaging check excludes from runtime payloads. It has not been pushed, merged, or uploaded during this task.

Version 1.0.1 corrects these issues. Its original teaching text is preserved after a prominent attribution/change notice. It adds a functional `learning-contribution` Skill for explicit contribution coaching. The changed ZIP must be tested and confirmed independently; the 1.0.0 confirmation is not transferred.

## Functional overlap and reuse

Live tracker searches inspected programming, explanation, teaching, and learning capabilities across historical and new assets. Three relevant public version-detail records were then read on 2026-10-22; `comparison-evidence.json` preserves the functional descriptions and capability names, without signed URLs or copied implementation packages.

| Existing asset | Input, action, output, and difference |
| --- | --- |
| `code-analysis-toolbox` @ 1.0.0, Asset ID `5383b7c97dcf45e18805798365dd6c1f` | Reads a repository and produces source-verifiable manuals, code walkthroughs, or checkpoint tutorials. Its `hands-on-tutorial-design` entry overlaps educational programming. Reuse that installed entry for standalone tutorials; this companion adds ongoing session behavior during actual feature work: prepared function/TODO, learner-written 5-10-line logic, and implementation insights. It does not replace the existing manual/tutorial workflows or bundle their source. |
| `learning-guide` @ 1.0.0, Asset ID `4ecd40a3a50e4caab26e176c56975cba` | Assesses learning state, designs and validates learning methods, and creates an implementation schedule. Its output is a learning system and schedule, rather than an active repository contribution. |
| `llm-learning-tutor-team` @ 1.0.0, Asset ID `03074bc9dfbd41a3ab93af2bce54cb0b` | Takes a learner goal/level/period and produces a planned LLM/Agent learning guide with concepts, exercises, and review. This Plugin instead changes coaching while implementing a real feature; it provides no curriculum or multi-role pipeline. |

Outcome: **Partial Overlap - Extend Existing Capability**. Keep the established code-analysis-toolbox tutorial entry for tutorial work and deliver this narrowly scoped companion for interactive implementation coaching. The existing Plugin is optional and is not automatically installed. No complete functional duplicate was established by the inspected records. No source ZIPs from these existing assets were downloaded or copied.

## Materials and permission evidence

Upstream: https://github.com/anthropics/claude-plugins-official/tree/d1adba47161a271799de7b548225d929310046bd/plugins/learning-output-style, commit `d1adba47161a271799de7b548225d929310046bd`, upstream version `1.0.0`.

The full Plugin-level Apache-2.0 text was read. The current GitHub tree and file endpoint confirmed the pinned Plugin LICENSE and hook. The supplied Plugin metadata, hook configuration, hook source, README, and license have Git blob hashes identical to that pinned upstream tree, as recorded in `provenance.json`. The root and Plugin LICENSE blobs both equal `d645695673349e3947e8e5ae42332d0ac3164cd7`. The Plugin subtree and root contain no applicable upstream NOTICE file at that commit. Permissions are assessed for these actual text/configuration materials, not inferred from the website footer.

| Actual runtime material | Actual reuse and conditions |
| --- | --- |
| `prompt_sections/learning-output-style.md` | The hook's JSON `hookSpecificOutput.additionalContext` extracted as UTF-8, followed by its original trailing newline. The original extracted text SHA-256 is `8dddba09dd52aeccf094bc37024f73199d7a50a57c4527718cd5784029586e13`. A prominent adaptation notice is prepended. No Bash is executed. Apache-2.0 covers the originating Plugin code/prompt; full license and author attribution accompany this derivative. |
| `skills/learning-contribution/SKILL.md` | New invocation procedure adapted from those teaching instructions. The file carries its own prominent attribution and change notice and points to the bundled Apache text. |
| `LICENSE`, `licenses/claude-plugins-official/LICENSE` | Byte-identical upstream Apache-2.0 text, SHA-256 `cfc7749b96f63bd31c3c42b5c471bf756814053e847c10f3eb003417bc523d30`. |
| `NOTICE`, `THIRD_PARTY_NOTICES.md` | Retains the supplied adaptation notice and appends the actual 1.0.1 changes; identifies Anthropic using the original author statement. No upstream NOTICE is fabricated. These notices do not alter license terms. |
| `manifest.json`, `SOURCE.json`, README | Host metadata and instructions derived from the user-supplied adaptation and the pinned source identity. Updates describe version 1.0.1 and actual packaging/skill changes. User authorization is the request to upload the supplied adaptation. No new copyright ownership or unified license is assigned. |
| Original source snapshots | Preserved unmodified under `upstream-review/` outside the runtime payload, including original author metadata, script comments, README, and license. They are evidence, not loaded capabilities. |
| Icons, fonts, data, third-party packages | None used or bundled. The runtime includes no additional executable code or dependency installation. |
| Host/model/service dependency | Requires native JiuwenSwarm/openJiuwen prompt-section and Skill support and a configured model. The host and model are not redistributed; their terms and availability remain external. No trademark endorsement is implied. |

Original author statement: Anthropic, as identified by `.claude-plugin/plugin.json`. The inspected hook has descriptive comments and no additional copyright header; those source comments remain unchanged in review evidence. No authorship, year, patent freedom, or trademark grant is invented.

Conclusion: `mode: ported`, `permission_status: verified` for the listed reused materials under the recorded distribution conditions. This is a scoped distribution review, not a repository-wide relicensing decision.

## Final archive review

The target marketplace layout is `learning-output-style/plugin.yaml` plus `learning-output-style/learning-output-style/`. Every reused runtime path above has license/notice coverage inside the inner payload. `license_evidence` points to the actual full license file with its exact SHA-256. The extracted prompt and derived Skill carry prominent local change notices; the central notice is additional attribution.

The native test transport contains exactly the same inner payload inventory and bytes. `package-verification.json` records both ZIP hashes and file hashes after packaging/extraction; `TEST_REPORT.md` records actual commands, environment, results, and limitations. Development evidence, tests, task records, caches, and original source snapshots are outside both runtime archives. The package is ready for submission only after its own current-version user test confirmation.

## Current-version user confirmation

Gan Mingrui explicitly confirmed 1.0.1 testing complete and authorized submission on 2026-10-22 in this conversation. See USER_TEST_CONFIRMATION.md and Progress Report RPT-20261022-learning-output-style-user-confirmed. The original PNG is to be attached to the delivery PR discussion; the task screenshot field will contain only its verified comment permalink. Final ZIP bytes remain unchanged.

## Version 1.0.2 Chinese documentation and listing update

Authorized on 2026-10-22 by the Project Lead-side human in the current conversation: repackage the ZIP in Chinese. Base delivery is merged PR #13, marketplace SHA-256 065afa71ff915c2d9ab494046e64edd2d47b1e7470f332bd8339922c0a1fc47d. New scope is Chinese marketplace display metadata, README/user instructions, version/source metadata and adaptation notices. Runtime teaching prompt and learning-contribution Skill remain byte-identical. The upstream pin and license coverage above remain unchanged. Pinned Plugin LICENSE Git blob d645695673349e3947e8e5ae42332d0ac3164cd7 was re-read through GitHub; the bundled complete Apache text is unchanged. No new code, icons, fonts, data or dependencies are introduced. The README has its own prominent change notice; original author/permission statements and full license copies remain in the payload.

The Hub official validation pipeline reads the inner README.md as detail_desc. The new Chinese README therefore supplies the actual user-facing detailed page, instead of relying on a short form-description override. Outer market metadata and the native manifest retain the original slug and matching 1.0.2 versions. Final extracted archive inventory, notice/license hashes, unchanged runtime-text hashes and both transport hashes are recorded in package-verification.json. User test completion for 1.0.1 is historical; it does not confirm 1.0.2. No 1.0.2 push, delivery PR, merge or Hub upload is authorized before its separate gate.


## Complete Chinese instruction edition (2026-10-22)

The user requested local WorkSwarm import and prompt tests for all Chinese packages. The active prompt `prompt_sections/learning-output-style.md` and invocation instructions `skills/learning-contribution/SKILL.md` are now translated into Simplified Chinese. This changes actual runtime instruction bytes. The translation retains meaningful 5–10-line contributions, prepared real files/signatures/TODOs, waiting for the learner, respecting a request to skip, and brief task-specific educational explanations. Chinese dialogue is the default; an explicit end-user output-language request takes precedence. Prominent file-level change notices retain Anthropic attribution and the exact source revision. No original English prompt is represented as byte-identical to the translation: `SOURCE.json.upstream_prompt_sha256` retains the English extraction hash `8dddba09dd52aeccf094bc37024f73199d7a50a57c4527718cd5784029586e13`, `prompt_sha256` hashes the Chinese teaching body, and `packaged_prompt_sha256` hashes the entire active file. The preserved review script was parsed as JSON to verify the original hash without executing Bash. The complete license copies remain unchanged. Earlier-version confirmations remain historical. Gan Mingrui remains the owner; this work does not change acceptance or Hub state. Actual current-version host/model results are recorded separately after testing.


## Actual WorkSwarm import defect and correction (2026-10-22)

The user-open WorkSwarm native UI imported Chinese1.0.3 but its detail/list rendering crashed on undefined.label. Real frontend localizedText expects zh/en objects, whereas this manifest supplied raw string tags. Converted only native manifest tags to valid localized objects; marketplace asset tags remain strings. Failure screenshot retained locally, followed by new-version import/prompt retest. Original owner Gan Mingrui and all prior evidence remain. This is an actual host compatibility correction, not a claimed test pass for the failed1.0.3.
