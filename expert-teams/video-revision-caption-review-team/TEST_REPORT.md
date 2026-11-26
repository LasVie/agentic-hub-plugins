# Build verification · 视频改版字幕核验专家团 1.0.0

Cai Zhenze · AH-20261126-video-revision-caption-review-team · 2026-11-26 Asia/Singapore.

- Native WorkSwarm ZIP SHA-256 `840382bb741fdf026fc5d8b664d26f75510629aab466c37720a491b7fbdc44b2`.
- Hub-compatible wrapped ZIP SHA-256 `cf6f7d471e668b35f21350a60cba08ff5476bf1fdb9e531d01b8cbd9d6a3c6fc`.

Official SkillHub CLI 0.0.1 validator and packager passed. Source, both archive payloads, the native extraction and the local WorkSwarm installation match on 21 UTF-8 files. Repository preflight passed on all three package forms. The Python 3.10+ scripts use the standard library. See [source review](SOURCE_REVIEW.md), [artifact record](release/1.0.0/artifact.json), and [preflight record](tests/records/package-preflight.txt).

Ten functional tests passed on [source](tests/records/source-tests.txt) and on the [exact native extraction](tests/records/extracted-tests.txt). They cover initial and mid-video trims, an audio replacement, insertion at cue boundaries, an insertion with no caption, repeated and stale text, missing edit notes, source and receipt tampering, overlaps, bounds and ordering, invalid input, Chinese help, and existing output protection. The timing-only fixture generates a ready-to-reimport SRT with one correction and preserves subtitle text and cue IDs.

The isolated WorkSwarm 0.2.8 creator validated three members. Import and install used the exact ZIP. With fixed local responses, the leader created tasks, the timeline analyst ran the proposal, and the verifier ran a source-only baseline before receiving the revised SRT and proposal. The two specialist tasks completed with actual handoffs, and all four commands returned success. The run used 23 local scripted model requests and observed 208 host events. The audit matched seven approved and five revised cues. It marked five review rows, suggested changing revised cue #3 to 00:00:02,500–00:00:03,500, and delivered three files without a full SRT for the unresolved cut. The Chinese Markdown report rendered in a local Chrome preview. [Creator validation](tests/records/host-creator.json) · [Installation](tests/records/host-import.json) · [Role execution](tests/records/host-execution.json)

The loopback host used supplied subtitle files, fixed model responses, and a fresh asset-owned runtime directory. The test processes were stopped and runtime evidence was preserved locally. The desktop picker, the user's configured model, and playback to check actual audio-to-caption alignment remain for [manual testing](MANUAL_TESTING.md).
