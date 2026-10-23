# Manual testing — 物理解题审校 1.0.1

Task `AH-20261023-physics-assumption-check`; Candidate `CAND-CLD-250`; owner **Cai Zhenze**. Source branch: `feat/physics-assumption-check`.

Open **http://127.0.0.1:6383/**. This instance has separate data, tasks, caches and ports under `/private/tmp/physics-assumption-check-workswarm-20261023`. Backend 29220, agent 28220, gateway 30220. Preserve Main's other instance and ports.

## Exact test package

- Native Extensions ZIP: `dist/physics-assumption-check/1.0.1/physics-assumption-check-1.0.1-workswarm.zip`.
- Native SHA-256: `9eb25694e42a1c9b952cb32f6c511bd4921a867a2e5f12c31430880077794707`.
- Canonical marketplace ZIP: `releases/agent-plugin/physics-assumption-check/1.0.1/physics-assumption-check-1.0.1.zip`.
- Canonical SHA-256: `e363550695bda9524f5f1c3e3d6764f35ab36a2111fe5f4d5e7275dd7be5b06f`.

All paths above are relative to this worktree:
`/Users/IDLE_And_R/.codex/worktrees/581d/agentic-hub-plugins`.
The native companion contains the canonical inner runtime files byte-for-byte. The canonical two-level marketplace wrapper is not the file for this host's native importer.

## Installation and model setup

In **Extensions → My Extensions → Create → Create from file**, choose the native ZIP. Install/enable **物理解题审校 1.0.1**. If automated verification already installed this version, use the existing installation and check the version rather than importing a duplicate. Start a new Agent conversation and select the plugin with the Extensions/plugin selector. Confirm the `physics-review` Skill and `prepare_physics_figure` tool are available.

This isolated instance was prepared with no provider credentials copied and no model requests made. Before conversational testing, select/configure your model in this instance's model settings. Image-based interpretation requires a model and host capability that can actually view the input/output images. Keep any credentials in the host's settings; do not include them in screenshots or send them in this chat. All code/CLI and SDK checks were performed without model calls; model-driven solving quality is the part you will manually verify.

## Tests and expected behavior

1. **Text-only physics and checks.** Ask:

   ```text
   请使用物理解题审校：小球从地面以 20 m/s 的初速度竖直向上抛出，
   忽略空气阻力，取 g=10 m/s²。求最高高度和到达最高点的时间。
   请列出所求与条件，推导旁标记假设编号，给出单位及另一项独立校验，
   最后按风险列出假设清单。
   ```

   Expect **20 m** and **2 s**, a declared positive direction, the specified `g`, a dimension check and an independent check such as energy, and an assumption list. A model should show the checks rather than merely say they passed.

2. **Actual figure preparation and missing friction.** Attach/open the original synthetic input:

   `/Users/IDLE_And_R/.codex/worktrees/581d/agentic-hub-plugins/dist/physics-assumption-check/1.0.1/test-inputs/斜面受力图.png`

   Ask it to invoke the actual `prepare_physics_figure` tool with this path, width `1600`, `enhance: false`, and a fresh output such as:

   `/private/tmp/physics-assumption-check-workswarm-20261023/runtime/用户测试斜面放大.png`

   Expect version **1.0.1**, input **800×500**, output **1600×1000**, Chinese messages, SHA-256 values and `enhanced: false`. Open the generated image and compare it with the original. The helper does not interpret the image; the model must actually view it or state that viewing is unavailable.

   Then ask: “质量 2 kg、倾角 30°、g=9.8 m/s²，但未说明摩擦。能否唯一确定加速度？再分别说明无摩擦与静止时的条件。” Expect missing friction to remain explicit. Under the stated frictionless branch, the downslope acceleration is **4.9 m/s²**. A static branch requires appropriate static friction; it should not invent a coefficient or infer frictionlessness from the drawing. Check the unit and the frictionless `θ→0` limit.

3. **Reject overwrite.** Repeat the same tool request with the same output path. Expect a Chinese `output_exists` error and unchanged output/source bytes. Use a new output path for each later successful operation.

4. **Invalid input.** Call the tool on the sibling `test-inputs/损坏图片.png`, with a fresh output. Expect a Chinese `invalid_image` result, no generated image, and no invented success.

5. **Correcting assumptions.** Tell the model that a previous diagram interpretation was wrong, identifying the exact changed condition. It should revisit the corresponding assumption and equations, explain any changed result, and update the final list. It should not change an answer merely because the user insists, or claim a blurred diagram is confirmed after interpolation.

Save original full-resolution screenshots showing the current version, selected plugin/tool, key operation and readable results. After testing, explicitly confirm completion/pass or report issues for **1.0.1 and the exact hashes above**, and supply the original images. AI tests and these instructions do not constitute your manual test completion.

## Reproduction and limits

Use the prepared interpreter `/private/tmp/jiuwenswarm-plugin-dev-2hlu8bh8/venv/bin/python` (Python 3.12.14, Pillow 12.2.0, openJiuwen 0.1.19). The dependency environment is reused read-only; this instance's state and runtime files are separate. Source and extracted-payload functional tests are in `tests/test_physics_assumption_check.py`. `build_local_test_package.py` derives the native companion from the canonical ZIP; the test file's `--write-demo-dir` generates the original synthetic inputs.

Static PNG/JPEG only, input at most 25 MiB/20 million pixels, output at most 32 million pixels/64 MiB, target width 64–4096. Only enlargement is performed; crop coordinates refer to EXIF-corrected pixels. Outputs do not preserve EXIF/ICC metadata. The helper has no OCR, symbolic solver, numerical simulator, network service or model integration. The host may send images/text to the provider you configure. No paid model call was made during preparation.

The unpublished 1.0.0 preflight build is archived under ignored `dist/physics-assumption-check/history/`; it was never handed off for user testing. **1.0.1** fixes cyclic input links and corrupt metadata handling. Do not test or confirm the superseded build. Package changes after your confirmation require renewed testing for the changed version/hash.

GitHub delivery remains gated on your explicit current-package completion, resolved issues, original screenshots and all delivery materials. No push, delivery PR, merge, Hub operation or GitHub Release is part of this Build handoff.
