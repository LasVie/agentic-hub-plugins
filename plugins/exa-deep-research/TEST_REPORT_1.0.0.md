# Exa Deep Research 1.0.0 — test report

Date: 2026-10-22 (Asia/Singapore). Task AH-20261022-exa-deep-research.

The final extracted package passed real native host import, installation,
four-tool/two-skill resolution, live anonymous search/fetch/domain filtering,
the managed-research guard and uninstallation. Nine port regression tests
passed independently. No active user installation or model account was used.

## Environment and source

- Windows, Python 3.12.6, MCP SDK 1.26.0, jsonschema 4.26.0, PyYAML 6.0.3.
- Actual openJiuwen source 4170e756504d70d8324c2ac18a5afdd770a99dc9.
- Actual JiuwenSwarm source 1bd3583934b76dd4b338ca959a6bff6b4cca3a2f.
- Actual host loader SHA-256 cf7f3ab694574ed771cba8b78899631bebd050814ed9b909acfee5ae246c4fc4.
- Pinned Exa source 3.4.2 at 0b499f095c4ca145eee07b09137641c037d58449.
  The hosted anonymous service advertised 3.5.0, with a required search
  objective absent from the pinned source. The port adapts to live discovery.
- No substitute Tool classes or simulated host loader. Error-path regression
  tests mock only the MCP exchange boundary. Live cases call the real service.

## Commands and results

`python -B -m unittest discover -s tests -p test_exa_deep_research.py -v`

9 passed, zero failures: invalid queries/counts/extra fields; file and
credential-URL rejection; explicit approval and missing-key guards before
network calls; ambiguous query/runId rejection; preserved remote isError and
structured content; nested secret redaction; ExceptionGroup sanitization;
single-result streaming; timeout without automatic retry.

`python -B tests/exa_plugin_smoke.py --sdk-root D:\jiuwen_repos\agent-core-latest --host-root D:\jiuwen_repos\jiuwenswarm --payload .research/extracted-exa --archive .research/test-packages/exa-deep-research-1.0.0-workswarm.zip --live --output .research/exa-final-smoke.json`

Exit 0. The actual host imported, installed and uninstalled the native ZIP
inside a temporary data directory. It resolved four native Tools and two
Skills. Anonymous search returned source URLs and 9659
characters of content. Fetch returned the MCP transport specification's page
text. Advanced search with a domain filter succeeded. The paid guard returned
its expected error without starting a run. Initial test-harness cleanup locks
on Windows were fixed by closing the host LogManager; final cleanup passed.
FUNCTIONAL_RESULTS.json contains a bounded summary, not retrieved copyrighted
page text or credentials.

`python -B tools/asset_release.py check plugins/exa-deep-research`

Passed: actual declared Tool classes/Skill paths, matching IDs and versions,
full license coverage and verified notice hashes. No AgentTemplate-only fields,
model aliases, keys, copied media, Node modules or comparison code are shipped.

`python -B tools/asset_release.py pack plugins/exa-deep-research`

Passed twice with identical ZIP bytes. Canonical release:
releases/agent-plugin/exa-deep-research/1.0.0/exa-deep-research-1.0.0.zip

SHA-256: f61bc3d94d3fdb48db5e1f41139cd9450c9f5902cfc992ccf730ea32b27cc8ac

`python -B plugins/exa-deep-research/build_local_test_package.py`

Native flat ZIP: .research/test-packages/exa-deep-research-1.0.0-workswarm.zip

SHA-256: 589ebbf999a42f0c15e9d98afe47b11d1b4747211c82becebca0ea1cf7f7f548

Extraction verified all 19 runtime files (46251 bytes),
every artifact.json payload hash, full MIT text, notices and absence of caches.
Both ZIP formats contain identical payload bytes. Canonical Git source hashes
and Windows checkout hashes are recorded separately in UPSTREAM_FILES.json;
the bundled full MIT text retains the checkout's CRLF line endings.

`python -B tools/asset_release.py check-repo`

Passed: 7 source assets and 8 release ZIPs. Windows' initial CRLF conversion
of unchanged tracked assets was repaired from canonical Git bytes; no changes
to those assets are part of this port. This checkout disables core.autocrlf.

The full unittest suite has two pre-existing symlink tests requiring Windows
privileges unavailable here, including outside the sandbox. They are not
reported as passing. Running the supported suite with UTF-8 enabled completed
57 tests: 31 passed and 26 were skipped by existing runtime-dependency guards.
The two omitted privilege cases are test_payload_symlinks_are_rejected and
test_generation_preserves_existing_files_and_rejects_symlinks. Exa's nine tests
and the separate real-host extracted-package test passed with real dependencies.

## Limits and user test gate

Authenticated managed research, premium providers, long ZDR streams and the
user's actual UI/model-guided flow have not been live-tested. Managed research
requires an authorized account and metered scope; no paid operation was run.
The earlier user statement "seems working" describes the original MCP tryout,
not completion of this new native version/hash. No test screenshot, current
package confirmation, GitHub delivery or Project Lead acceptance is asserted.
