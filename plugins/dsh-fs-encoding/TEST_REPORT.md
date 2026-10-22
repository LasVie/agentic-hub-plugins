# Functional Test Report

Date: 2026-10-22

Version 1.0.1 fixes a host-test finding from 1.0.0: WorkSwarm can load separate tool classes in isolated module contexts, so an in-memory undo dictionary was not shared and `encoding_undo` returned `NO_UNDO`. Undo records now use an owner-only host temporary directory. The regression suite deliberately reloads the module between edit and undo, verifies byte restoration, and verifies `STALE_UNDO` after an external change.

Upstream 1.5.2 was pinned at commit `a4d31cc33bd6f0fab2bf6752f6e50e8301885b94` and checked under Node 24. `npm run build` passed. The upstream `npm test` result was 601 passed and 4 failed out of 605 tests; all four failures were in `test/grep-tool.test.ts`, where current ripgrep output included directory-prefixed paths rather than the basename-only keys expected by the tests. These upstream grep failures do not exercise code copied into this Python port. `npm ci` also reported five vulnerabilities in the upstream development/dependency tree (one moderate, two high and two critical); those Node packages are not bundled or used by this standard-library-only port.

The native port integration test covers UTF-8 BOM, UTF-16, GBK and CRLF preservation; explicit decoding and remembered encoding for a later full-file write; preview-only mutation; rejection of an unrepresentable emoji without byte changes; decoded search; successful undo; and byte-for-byte restoration.

The direct integration suite passed. WorkSwarm 0.2.7 L0/L1/L2 validation passed with one bound Skill, five bound Tools, and zero errors or warnings. Repository format validation and a repeat deterministic pack comparison also passed.

The user subsequently confirmed the full version 1.0.1 host test for ZIP SHA-256 `9572f21c28380903c389ec9aa2ab49c329edc0d69843c382a87a954b5f78d194`. All documented GBK, strict-write, grep, successful undo, stale-undo, UTF-8 BOM, UTF-16LE BOM and CRLF cases passed. A real test screenshot, PR merge, Hub submission and Project Lead acceptance remain pending.
