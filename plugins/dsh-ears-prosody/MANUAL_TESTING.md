# Manual testing: DSH Ears Prosody 1.0.1

Candidate `CAND-DSH-189`; task `AH-20261022-dsh-ears-prosody`; owner Cai Zhenze.

Use the existing isolated local WorkSwarm at **http://127.0.0.1:6283/**. Its backend is on port 29110. The Node.js runtime must be on the backend PATH. The automated checks do not invoke a model; use your configured provider for any conversational tests you choose to perform.

## Files

- Canonical delivery ZIP: `releases/agent-plugin/dsh-ears-prosody/1.0.1/dsh-ears-prosody-1.0.1.zip`.
- WorkSwarm testing ZIP: `dist/dsh-ears-prosody/1.0.1/dsh-ears-prosody-1.0.1-workswarm.zip`.
- Synthetic audio: `dist/dsh-ears-prosody/1.0.1/test-audio/三段音高示例.wav` and `静音示例.wav`.

Paths are relative to the repository root. Exact package hashes and actual verification results are in `TEST_REPORT.md`; local companion metadata is `dist/dsh-ears-prosody/1.0.1/companion-artifact.json`. The native companion contains the canonical inner payload unchanged. It only removes the marketplace wrapper for the current WorkSwarm importer.

## Install and test

1. Open WorkSwarm, then **Extensions → My Extensions → Create → Create from file**. Choose the **WorkSwarm testing ZIP** above and confirm the import. Install or enable **DSH 韵律分析 1.0.1**. If already installed by the automated host test, inspect its version/card and use that installation; no duplicate import is necessary.
2. Start a fresh **Agent** conversation and attach the plugin using the Extensions/plugin selector. Confirm its Skill and `analyze_wav_prosody` tool are listed.
3. Use this prompt with the backend-accessible path:

```text
请使用 DSH 韵律分析的实际 analyze_wav_prosody 工具分析：
/Users/IDLE_And_R/Downloads/Huawei/agentic-hub-plugins/dist/dsh-ears-prosody/1.0.1/test-audio/三段音高示例.wav
用中文显示返回的版本、时长、活动段数、停顿、平均音高和能量峰节奏代理指标。
再分析同一目录中的 静音示例.wav，说明区别。
这些是合成信号，不是真人语音。不要推断情绪或意图；若工具或文件不可用，
如实报告错误，不要编造测量值。
```

Expected: version 1.0.1, duration 5.0 s, three activity segments, two pauses approximately 400 ms (frame/threshold tolerance), mean pitch approximately 220 Hz. The signal has three 1.2 s tones at 180/220/260 Hz, with 300 ms leading/trailing silence. Timing is approximate; this is not a speech-recognition test.

The installed-tool check returned 365 ms for each measured pause and 220.1 Hz mean pitch. The steady tones have no prominent internal amplitude pulses, so the pacing proxy is zero; it does not count the three tones as syllables.

4. Repeat with the sibling `静音示例.wav`: expect duration 1.0 s, zero activity segments and unavailable/null pitch. Ask it to explain why silence does not provide a speaking-rate estimate.
5. Optionally test your own short WAV (100 ms–60 s; 12 MiB maximum; mono/stereo; 8–48 kHz). Attach it and ensure the tool receives the actual backend file path. A missing path, unsupported format or invalid WAV must return a clear error, not invented measurements. A WAV supplied to this plugin stays local, though the host conversation may send its returned measurements/text to your configured model provider.
6. Capture an original screenshot showing version 1.0.1, the Chinese plugin/tool operation and its results. After testing, explicitly confirm whether this exact version/package is complete or describe any issue. The automated tests and screenshot alone do not authorize GitHub delivery.

## Reproduce the local companion and inputs

From the repository root, after creating the canonical release:

```sh
python plugins/dsh-ears-prosody/build_local_test_package.py
python tests/test_dsh_ears_prosody.py --write-demo-dir dist/dsh-ears-prosody/1.0.1/test-audio
```

No upload to Agentic Hub, GitHub Release, push, PR or merge belongs to this Build handoff. Song Haoran handles Hub operations separately.

## Why another version needs confirmation

The original English 1.0.0 passed user testing; its confirmation and original screenshot are retained in USER_TEST_CONFIRMATION.md. Main e0f6b866 added a mandatory Chinese-final-delivery policy before the delivery PR. This 1.0.1 package changes human-readable text and version only; its new hash requires its own explicit testing completion. The old screenshot does not establish testing of 1.0.1.

The old canonical ZIP/artifact are archived at `dist/dsh-ears-prosody/history/1.0.0/`, with the original source and records in local commit `1f6f30c`. They are retained as local historical evidence, excluded from the current delivery release tree. Do not click Publish; no Hub action is part of this test.
