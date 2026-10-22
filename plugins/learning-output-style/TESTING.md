# User testing: Learning Output Style 1.0.1

Task: `AH-20261022-learning-output-style`; candidate: `CAND-ANT-037`; owner: Gan Mingrui.

Use `learning-output-style-1.0.1-native-test.zip` in JiuwenSwarm's local file-upload interface. Its payload files exactly match the inner Plugin in the marketplace ZIP, as recorded in `package-verification.json`. Keep both package hashes with the test result.

- Native test ZIP SHA-256: `ae36a586495e015b028dda8e35c5a04af4854bc9cf4e05f174b27cadb7a031a9`.
- Final marketplace ZIP SHA-256: `065afa71ff915c2d9ab494046e64edd2d47b1e7470f332bd8339922c0a1fc47d`.

Both archives are supplied together. If your host offers import from a local directory, you can also extract the final marketplace ZIP and import its inner `learning-output-style/learning-output-style/` directory directly. Record which route you used and both unchanged archive hashes when confirming the final package.

Required environment: native JiuwenSwarm/openJiuwen Harness, a configured model, and normal workspace file permissions. No extra Plugin dependency or API key is needed. Other Harness implementations remain unverified.

Follow the inner README's installation and test steps. Capture the installed version, prepared code location, insight, and request for your contribution; after providing code, capture the review/check result. Also test routine setup and a fresh conversation without the Plugin.

Suggested request: `Create learning_demo/retry_demo.py and coach me through implementing retries. Prepare the function and a TODO for a 5-10-line retry-delay strategy. Explain the tradeoff and wait for my contribution.` Expected: a concrete file/function, a meaningful TODO, implementation insights, and a pause for your code; after you provide it, a review and suitable checks. A routine setup request should not become an unnecessary exercise.

Confirm explicitly that **1.0.1 testing is complete** and report any blocking issue. The original 1.0.0 confirmation remains recorded in the tracker and is not transferred to the replacement. Supply an actual test screenshot or team-accessible link; do not substitute these automated checks for your test evidence.

After confirmation, the workflow can push the source and marketplace ZIP through a delivery PR, verify CI and merge, and submit the merged Plugin ZIP to Hub. Actual Hub evidence and Project Lead acceptance remain separate delivery gates.
