# Offline Score Workbench 1.0.0 functional test report

Candidate CAND-EXT-012. Task AH-20261105-offline-score-workbench. Owner Cai Zhenze. Identity repo:agent-plugin:offline-score-workbench. Verovio → 离线乐谱工作台 → offline-score-workbench.

## Verified on 2026-11-05

- macOS, local WorkSwarm source revision 3ef1de9 and openJiuwen SDK 0.1.19. Separate host roots and ports 6395/29330/28330/30330. Frontend HTTP and direct/proxied WebSockets verified. The host has a disabled test model.
- Eleven plugin lifecycle and HTTP tests passed, including launch authorization, reuse, missing entry, foreign-installation refusal, cross-port navigation metadata, no score upload and browser security policy.
- Four engine tests passed using Node 22 with string code generation disabled. The independent MIDI parser verified two parts, a quarter rest, F-sharp, a tied note across measures, edit from pitch 60 to 62, MEI half notes and multi-page rendering. Verovio MIDI note-off precedes the notated boundary by one tick. The first fixture note inspection returned 60 at 0 ms with 500 ms duration.
- Browser engineering probe on the rebuilt vendor engine rendered the Chinese title, staves, notes, rests, accidental and tie. Input edits immediately cleared stale SVG and disabled both downloads. Re-rendering showed pitch 62. An external DTD produced a Chinese error and restoring the example recovered. Final package checks are recorded below after extraction.
- Twenty-one repository packaging tests passed. The new preflight reproduced both known Hub dynamic-JavaScript rejections on the original Mapshaper and RDKit archives. The preflight and browser policy test different boundaries: the former checks published source signatures and the latter permits compilation of bundled WebAssembly while blocking JavaScript string evaluation.

## Reproduction

```bash
python tools/asset_release.py check plugins/offline-score-workbench
python tools/asset_release.py preflight plugins/offline-score-workbench/offline-score-workbench
python -m unittest discover -s plugins/offline-score-workbench/tests -p 'test_*.py'
node --disallow-code-generation-from-strings --test plugins/offline-score-workbench/tests/test_engine.cjs
```

Browser requirements: a current desktop browser with WebAssembly and dedicated workers. The loopback launcher was exercised on macOS. Other OS/browser combinations and the full MusicXML/MEI standards remain outside this verification. See the bundled Chinese README and outer manual test guide.

## Frozen 1.0.0 package and WorkSwarm verification

| ZIP | SHA-256 |
| --- | --- |
| Native WorkSwarm `plugins/offline-score-workbench/test-packages/offline-score-workbench-1.0.0-workswarm.zip` | `4be76815a149d1dd96cbe5bd77a9b16ca3bc2f4f607402ff79cff5b5d6ba0e1c` |
| Canonical `releases/agent-plugin/offline-score-workbench/1.0.0/offline-score-workbench-1.0.0.zip` | `b49526395c26d1757988e28fe01bf91ad4d4a855c49aebd7844d2682ff2bb1d3` |

- Format, pack, ZIP CRC, UTF-8, per-file equality and repository checks passed. The 45 inner files are byte-identical across source, both ZIPs and the installed payload. The license check verified all 30 evidence-file hashes. Both ZIPs had zero findings on the two regression signatures and on the seven script files scanned with the full published content checker. The 24 script files in the extracted corresponding-source tar also had zero findings. These are local checks of the pinned public implementation.
- The corresponding source rebuilt successfully from a fresh extraction and passed all four engine tests with Node string-code generation disabled. The rebuild included a different absolute build path in JSON++ diagnostics. The selected runtime and delivered ZIP hashes above identify the tested bytes.
- The isolated 6395 WorkSwarm instance imported and installed the native ZIP through its supported interface. The installed 1.0.0 card appeared in the Chrome Extensions picker. Frontend and both WebSocket routes worked. A standalone SDK process loaded the installed payload and invoked status, refusal without confirmation, start, reuse, stream and stop. A Chrome cross-port link opened its actual returned URL. At Build handoff, model-backed chat dispatch awaited manual testing because the isolated test model was disabled. The engineering probe sent no model requests.
- Browser verification on the installed payload showed both staves, title, rest, F-sharp and tie. The example's first note showed pitch 60 at 0 ms with 500 ms duration, then 62 after editing. Before rerender the prior score cleared and both exports were disabled. The local MEI chooser rendered two half notes and inspected the first at 60 / 0 / 1000 ms. A 60-measure fixture paginated 1/2 → 2/2 → 1/2. Malformed XML and an external DTD were refused in Chinese, and a valid input recovered.
- The actual downloaded SVG parsed with four measure-staff groups and local glyph references. SHA-256 `fdf825637afeba55ba83f44b59916ff78313fdfacabc35779c38bdedab5e1eb6`. Independently decoded browser MIDI downloads were type 1, three tracks, 120 ticks per quarter. The first pitch changed from 60 to 62 and the other note events matched. The tied G starts at tick 360 and ends at 599. Original MIDI SHA-256 `496179a91242a9c27f7d2bcbfc17ec77f59c19fd74e047c19d24c47fb090402b`. Edited MIDI SHA-256 `8345b823c27567d49344b72b8c91c8d6ae8099b9252d6e69d3ec0db504fd73df`.

## User confirmation and delivery verification

Cai Zhenze confirmed in the current Codex conversation on 2026-11-05 (Asia/Singapore) that manual testing of 离线乐谱工作台 1.0.0 was complete and passed. The confirmation is recorded as `RPT-20261105-offline-score-workbench-confirmed` for `AH-20261105-offline-score-workbench` and covers the frozen ZIPs above. No blocking issues were reported.

The original WorkSwarm chat screenshot records a 1.0.0 status call, initial start, repeated start with reuse, and final status. Both starts and the final status returned the same workbench URL. This original is retained privately because it shows the local access URL. Six original browser PNGs show the 1.0.0 interface, two-note MEI engraving and timing, and two-part MusicXML engraving and timing. Download byte validation is covered by the engineering checks above.

Delivery verification rechecked both ZIP hashes and CRCs, the canonical wrapper, all 45 inner payload hashes, the repository package contract, and local dynamic-JavaScript preflight. All 21 packaging tests, 11 runtime tests, and four engine tests passed.
