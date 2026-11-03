# Reproduce: 离线 PostgreSQL 实验台 1.0.3

1. Install the native companion ZIP through WorkSwarm Extensions; verify its hash. The canonical Hub wrapper and native ZIP have identical inner runtime files.
2. Enable this plugin in a task, choose an existing dedicated local workspace and ask WorkSwarm to open 离线 PostgreSQL 实验台. Use its actual returned loopback URL.
3. Exercise the following flow, inspect actual outputs, close/reopen the same installation and verify saved data. Sample data does not represent a user's production project.

The installed UI executed the real PostgreSQL JSONB stock query and rendered three Chinese products. Its snapshot export control produced a 4,581,183-byte archive downloaded through the browser; the archive contains PG_VERSION. The engine suite verifies writes, restart persistence, independent projects, SQL failure recovery and export.

4. Inspect actual exported files and Chinese text, retain original screenshots with version/hash association. These instructions do not claim additional human testing.

Limits: Embedded development database, one bounded worker per operation; 15-second timeout and at most 300 displayed rows. No production concurrency, replication or arbitrary PostgreSQL extension claims.
