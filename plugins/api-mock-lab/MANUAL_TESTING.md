# Reproduce: 接口模拟与联调台 1.0.3

1. Install the native companion ZIP through WorkSwarm Extensions; verify its hash. The canonical Hub wrapper and native ZIP have identical inner runtime files.
2. Enable this plugin in a task, choose an existing dedicated local workspace and ask WorkSwarm to open 接口模拟与联调台. Use its actual returned loopback URL.
3. Exercise the following flow, inspect actual outputs, close/reopen the same installation and verify saved data. Sample data does not represent a user's production project.

Normal HTTP 200 (6 ms), delayed HTTP 200 (357 ms) and simulated HTTP 503 (9 ms) were exercised through the installed Chinese UI. The history displays all three real requests. The engine suite also verifies OpenAPI 3.0 examples, external-reference rejection, POST routes and preservation after invalid definitions.

4. Inspect actual exported files and Chinese text, retain original screenshots with version/hash association. These instructions do not claim additional human testing.

Limits: Loopback deterministic mock APIs only; proxying, callbacks, external references, response files and dynamic templates are disabled. A mock result does not verify a production backend.
