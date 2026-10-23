# Functional Test — picturereader 1.0.0

Test date: 2026-10-23 (Asia/Singapore). Task `AH-20261023-picturereader`; candidate `CAND-DSH-177`.

Environment: macOS arm64, Python 3.11.15, OpenJiuwen host venv, Pillow 12.1.1. No network calls, API keys, external models, or business data.

Command:

```bash
~/agent-core/.venv/bin/python plugins/picturereader/tests/test_picture_reader.py
```

Result: **PASS**, exit 0. The test generates a deterministic 120×80 four-quadrant fixture and invokes all four real OpenJiuwen tool classes.

| Check | Result |
| --- | --- |
| PNG, JPEG, and WebP scan | PASS |
| Region scan and red-dominant measured palette | PASS |
| Structure measurements bounded to 0..1 | PASS |
| Exact red/green/blue/white coordinate samples | PASS |
| Palette shares sum to approximately 1 | PASS |
| PNG crop dimensions and bytes | PASS |
| Source bytes unchanged | PASS |
| Existing-output protection | PASS |
| Out-of-bounds coordinate rejection | PASS |

Repository format, deterministic packaging, extracted-ZIP loader, and repository-wide structural checks are recorded after the release package is generated. This development test is not a user WorkSwarm screenshot, Hub submission, or Project Lead acceptance.

## User WorkSwarm test

The user confirmed the exact manifest-at-root ZIP SHA-256 `4118f7c64584247ca3b3087b53beb3dd74171f9dae2f52bf24c412a92fb268fa` on 2026-10-23 and supplied the original 2250×24045 screenshot at `test-evidence/jiuwenswarm-share-20261023-130342.png` (SHA-256 `809f95f22d77295af1445651c17fe810c8f724cc6936a555aa2a6ad4cb5d8631`). See `USER_TEST_CONFIRMATION.md`. This evidence is outside the runtime ZIP.
