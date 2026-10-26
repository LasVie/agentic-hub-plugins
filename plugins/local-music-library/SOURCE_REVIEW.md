# Source review — 本地音乐库

- Task: AH-20261023-local-music-library; Candidate: CAND-DSH-335; Owner: Cai Zhenze.
- Naming: kendu76/dsh-music-player → 本地音乐库 → `local-music-library`.
- Stable identity: `repo:agent-plugin:local-music-library`.
- Upstream: https://github.com/kendu76/dsh-music-player at `172355b147f91ae994631aa4cbd61adfe8a5fb66`, package 1.0.3.
- Review date: 2026-10-23. Mode: **ported**. The Python implementation adapts the MIT local directory / playlist / HTTP Range workflow; it is not claimed as an independent clean-room rewrite.

## Permission and scope

The complete pinned root LICENSE is MIT, Copyright (c) 2026 kendu76. Its permission notice and disclaimer must remain intact. The parent and candidates agent independently read it and the actual source. The inspected recursive tree has no separate local-code license or upstream NOTICE. The source download in `/private/tmp/music-library-upstream-20261023` is a research subset, not a complete upstream checkout.

Reused/adapted source: `lib/index.js`: local audio MIME list, bounded recursive collection shape, playlist member/order/persistence model and byte-range playback behavior. Actual adapted delivery path: `runtime/library.py`; source-relevant MIT notice is retained in its header. New `runtime/server.py`, `runtime/control.py`, native tool adapter and Chinese browser UI replace DSH/Cordis/React registration and do not import the upstream monolith.

Excluded: upstream React client, DSH services/hooks, images/screenshots, song/media fixtures, vendored QRCode, internet music/radio/lyrics, TTS, novel/news engines, provider credentials and all online/update integrations. Root MIT is not treated as permission to redistribute third-party media or service content. No upstream font, logo, recording or binary is bundled. Runtime uses Python standard library, the target host's existing openJiuwen SDK and browser-native audio decoding; no npm/pip dependency or FFmpeg binary is redistributed.

## Required adaptation

Music-only scan must have its own entry/track/depth limits; the original combined music/book stop condition is insufficient. Byte-range responses must stream bounded chunks instead of reading full files. Files must remain beneath an explicitly selected canonical root and reject symlinks. Playlist/runtime state is separate from source audio, with locking and atomic persistence. No automatic home-directory scan or browser launch. Browser autoplay/codec failures must be visible, not reported as success.

Full original MIT text is bundled at `licenses/dsh-music-player/LICENSE`; `THIRD_PARTY_NOTICES.md` maps reused source and modifications. Final per-file hashes, extracted ZIP/license/path checks and actual functional/host results will be recorded before the manual-testing handoff. No final test, packaging or manual pass is implied by this review.

## Final distribution review — 2026-10-23

Inspected all 14 runtime files after extraction. `runtime/library.py` retains the upstream copyright/permission-reference header and modification notice. Full original MIT bytes at `licenses/dsh-music-player/LICENSE` hash to `72da6f7e35695c2e2c48017943bf2a48be9c9855bf2384fc89c7ce0e1f6b044f`, matching pinned source and provenance. No third-party media/fonts/icons/QRCode or upstream online client is bundled; generated test WAVs remain outside delivery. No applicable upstream NOTICE was present; none fabricated. THIRD_PARTY_NOTICES records actual adaptation scope.

Canonical ZIP `releases/agent-plugin/local-music-library/1.0.0/local-music-library-1.0.0.zip`: SHA-256 `5c32cc0f4068d75272e00bff309b84a9b98c279d469d8c636d96960ca5e8408f`. Native same-payload testing ZIP `plugins/local-music-library/test-packages/local-music-library-1.0.0-workswarm.zip`: SHA-256 `e81650018d2d85667e6d2042c4ed33eb1129b58aba9de7be24c6f9c4e11eb24a`. All declared files, wrapper shape, version1.0.0, CRC, paths, Chinese content and license evidence match. Per-file digests are recorded in canonical artifact.json. Source/extracted tests each24/24 and actual installed-host/browser checks passed as detailed in TEST_REPORT; user manual confirmation remains pending. This review establishes the recorded scope and fulfilled notice conditions, not Hub approval or a new repository-wide license decision.
