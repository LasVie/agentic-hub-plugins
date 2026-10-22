# Learning Output Style 1.0.1

This JiuwenSwarm Plugin adapts Anthropic's Apache-2.0 learning-output-style instructions. It explains implementation choices and prepares small, meaningful code contributions for the learner during real programming tasks.

## Install and test

The repository ZIP uses a marketplace wrapper: `learning-output-style/plugin.yaml` and the inner `learning-output-style/learning-output-style/` Plugin. For the JiuwenSwarm local file-upload test, use the supplied native test ZIP, which contains the identical inner payload at its root. The marketplace ZIP is reserved for the later Hub submission after testing and the delivery PR.

1. Open JiuwenSwarm's Extensions panel and use Create → Upload File with `learning-output-style-1.0.1-native-test.zip`.
2. Confirm that the installed Plugin is version **1.0.1**, then select it in a **new** programming conversation using the native JiuwenSwarm/openJiuwen Harness.
3. Request: `Create learning_demo/retry_demo.py and coach me through implementing retries. Prepare the function and a TODO for a 5-10-line retry-delay strategy. Explain the tradeoff and wait for my contribution.`
4. Expect a concrete file/function, a meaningful TODO, implementation insights, and a pause for your contribution. Provide the code, then ask the host to review it and run suitable checks.
5. In another new conversation, request routine configuration and confirm it does not create an unnecessary exercise. In a fresh conversation without the Plugin, check that the learning prompt is absent; previous conversation history can still influence replies.

File creation and checks require the host's usual workspace permissions. A configured model is required. The Plugin needs no extra API key, account, MCP connection, Python package, Node package, or Bash runtime.

The Plugin loads the original teaching text through a native `prompt_sections` entry. Its `learning-contribution` Skill provides an explicit entry for contribution coaching. No upstream hook script is executed. Other Harness implementations have not been verified.

## Scope and reuse

For manuals, code walkthroughs, or a standalone tutorial with checkpoints, reuse `code-analysis-toolbox` and its `hands-on-tutorial-design` capability when available. This companion adds teaching behavior while working on an actual feature. It does not duplicate a curriculum, learning schedule, or multi-role education team. The other Plugin is optional and is not automatically installed.

## Changes from the confirmed 1.0.0 package

- Adds the repository marketplace wrapper and a separate native test transport containing identical payload files.
- Adds the `learning-contribution` Skill and required source/license notices.
- Prepends a prominent attribution/change notice to the prompt; the original teaching text after that notice is byte-identical to 1.0.0.
- Removes unused upstream hook scripts and hidden source snapshots from the runtime payload. Their pinned identities remain in the source review outside the payload.

The user's test confirmation for 1.0.0 does not cover this changed package. Complete testing of 1.0.1 before pushing, creating a delivery PR, merging, or uploading to Hub.

## Source and license

Upstream author: Anthropic. Pinned source: https://github.com/anthropics/claude-plugins-official/tree/d1adba47161a271799de7b548225d929310046bd/plugins/learning-output-style (upstream version 1.0.0).

See `THIRD_PARTY_NOTICES.md` and `licenses/claude-plugins-official/LICENSE`. Upstream has no applicable NOTICE file in the inspected root or Plugin subtree at that commit. This adaptation does not claim official Anthropic endorsement. No new repository-wide or third-party relicensing decision is made.
