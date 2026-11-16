# Test report

Notion 工作区连接器 1.0.0. Song Haoran, AH-20261116-notion-cli.

The official ntn 0.23.30 archive was checked against npm integrity metadata. The downloaded darwin-arm64 binary reported the expected version. A fresh no-browser login request in an isolated temporary profile returned the official Notion URL, a verification code and the documented polling command. WorkSwarm package and authenticated operation tests are recorded separately below as they complete.

## WorkSwarm 0.2.8 live test, 2026-11-16

- macOS Apple silicon, stock installed WorkSwarm 0.2.8 web frontend, gateway and runtime, isolated data and connector profiles. A loopback Hub-compatible catalog served the exact wrapped 1.0.0 ZIP, SHA-256 `00cbe42995c36cd713c9b01187cc428ba92022a913595ccb2e2120becc5af2ab`. WorkSwarm downloaded it and automatically prepared the pinned ntn 0.23.30 binary. The separately provided native ZIP has byte-equivalent payload files.
- Clicked Connect on the Notion card. WorkSwarm opened the local verification-code page and waited for authorization. Song Haoran completed the official Notion browser consent for the new test workspace. WorkSwarm then displayed Use.
- Started a chat through Use and explicitly selected the bundled Skill in the slash menu. The test model used the host's runtime name `notion-cli` to load `notion-cli-guide`. The WorkSwarm chat executed four shell tool calls against the installed launcher and the real Notion API. Search identified the exact private test page, read returned the original Chinese paragraph, append returned a new block ID, and a separate read found the new Chinese marker exactly once with the original paragraph preserved. The Notion web page independently showed both paragraphs.
- A deterministic local model and command assertions drove the chat to avoid using a hosted model or unrelated Notion data. This tests WorkSwarm's connection, skill mounting, shell execution and the live Notion operations. It does not establish how reliably a production model selects the Skill from a plain prompt. The first test chat encountered WorkSwarm's default Documents path outside the test sandbox, and a later run encountered a runtime restart. The successful run used WorkSwarm's supported temporary task directory override and explicit Skill selection. WorkSwarm source and installed bundle files were not changed.
- Ran `python3 -B -m unittest discover -s connectors/notion-cli/tests -v`, with all six tests passing. The launcher cleared the local test session after the live run and reported disconnected. The private Notion test page was retained.
- Official catalog installation, other operating systems and the server-side browser flow remain unverified.
- Song Haoran accepted the reviewed 1.0.0 test results on 2026-11-16 in the current conversation. The shared tracker records the acceptance under `RPT-20261116-notion-cli-user-test`. The original WorkSwarm conversation PNG is retained locally for the delivery PR.
