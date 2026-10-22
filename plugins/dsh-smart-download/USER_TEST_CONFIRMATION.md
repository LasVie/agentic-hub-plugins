# User Test Confirmation

- Date: 2026-10-22
- Version: 1.0.0
- Native WorkSwarm ZIP SHA-256: `80090178347eb748b0df06c5288e71208cb3fe6b753f636711ef629393239b69`
- Marketplace ZIP SHA-256: `77873887154682d3419ed68d95e3d0269aa21ec27237735882b07c794ba2aa0d`
- Confirmation source: current conversation

The user tested the exact native WorkSwarm package and concluded: “should be good to go”. The native test payload is byte-identical to the inner runtime payload in the marketplace ZIP recorded by `artifact.json`.

## Passed operations

- Eight-worker download completed for 29,186,321 bytes; task `b22ba96ce925489bab97fa9d0dce0a38`.
- `download_status` returned the matching completed byte counts and SHA-256.
- Four-worker verified download returned `verified=true`; task `0a11d3e2554f4e639e3436abf8ce3346`.
- Deliberately incorrect checksum returned `CHECKSUM_MISMATCH` and created no final file; task `c177f87990b449c884f3290986edd48a`.
- Existing-file protection returned `OUTPUT_EXISTS` and preserved bytes/hash; task `948ecc3f6e4648808a92322301bc40cb`.
- Default private-network protection rejected loopback; task `fe6831e302c340e4ac84a497170051a5`.
- `first.bin`, `verified.bin`, and `resume.bin` all had 29,186,321 bytes and SHA-256 `12445c7b3db3126c41190bfdc1c8239c39c719404e844babbd015a1bc3fafcd4`. `bad-checksum.bin` was absent.

## Retained limitation

The manual interrupted-transfer scenario was not exercised: the workers=1 transfer completed before it could be interrupted, so task `9aea567c0e4d440f8764a1d226896081` correctly reported `resumed=false`. Automated integration testing separately forces an interrupted transfer and verifies that the identical retry returns `resumed=true` with exact final bytes. Manual resume therefore remains unconfirmed, not failed.

The test directory was retained at `/tmp/dsh-smart-download-test`. No original screenshot link was supplied with this confirmation.
