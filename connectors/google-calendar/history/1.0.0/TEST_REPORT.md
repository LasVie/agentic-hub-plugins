# Test report

Google 日历连接器 1.0.0. Song Haoran, AH-20261116-google-calendar.

The test uses a private fixture event on the authorized user's primary calendar. The Calendar scope is separate from existing Workspace connector tokens.

## WorkSwarm 0.2.8 live verification, 2026-11-16

- Stock installed WorkSwarm 0.2.8 on Apple silicon macOS, using its web frontend, gateway and runtime in an isolated profile. No WorkSwarm source or application-bundle changes.
- Installed the exact wrapped ZIP from a loopback Hub-compatible catalog. WorkSwarm downloaded and registered SHA-256 `4b2c3ece4fc2d6b79689c6322d9458236a5aa500accefe98b57098789dace1f6`. Setup found an existing local Python interpreter and installed the locked runtime dependencies.
- Reused the team's existing test project's Desktop OAuth client in the isolated Workspace configuration, with no shared token reuse. Google Calendar API was enabled in the test project after user approval. Clicked Connect in the card. Song Haoran completed Google browser consent for the Calendar scope and the card changed to Use.
- The chat explicitly selected the installed Google Calendar Skill. The WorkSwarm test model drove three shell tool calls against the installed connector and live Calendar v3. It queried the designated primary-calendar time span and unique title, received no match, created one timed event, then separately read it by the returned event ID. The title, description, confirmed status and Singapore start/end times matched.
- A separate read with Calendar v3 confirmed private visibility, free availability, zero attendees and no default reminders. A second filtered list returned exactly one matching event. Test title `WorkSwarm 日历实测 20261116-937aa250`, 2026-11-17 20:00–20:15 Asia/Singapore. The fixture event was retained for review. Logout cleared the connector token in the isolated test profile.
- Six Calendar unit tests passed. The official Agentic Hub CLI validated and packed the ZIP. The native and wrapped artifacts have byte-equivalent payloads and independent recorded ZIP hashes.
- A deterministic local test model was used for chat orchestration. Official Hub deployment, production model routing, other operating systems, server callbacks and the Cloudflare OAuth route are outside this live test. The team's previously inspected Cloudflare OAuth service code only requests read-only Calendar event access.

Song Haoran confirmed that 1.0.0 passed testing on 2026-11-16 in the project conversation. Confirmation report `RPT-20261116-google-calendar-user-test`. The original WorkSwarm chat export shows the query, creation and readback results and is attached to the delivery PR. Original PNG 2250 × 2094, SHA-256 `87704d22f88533620771170fd8c93d6fdeb06e0a79734ac0320d8287a37ed838`.
