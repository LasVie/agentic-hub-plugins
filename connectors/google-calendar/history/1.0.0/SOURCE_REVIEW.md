# Source review

Google Calendar → Google 日历连接器 → google-calendar. Song Haoran, AH-20261116-google-calendar, Candidate ID Not Applicable, 2026-11-16.

The checked live Hub catalog contained Gmail and Google Drive assistant assets. The team repository separately contains delivered Gmail, Drive, Docs, Sheets and Slides connector packages. The checked catalog, tracker tasks and repository contained no Google Calendar connector. Calendar capabilities for other providers operate on different account data.

The Calendar service and Skill are independently authored against the Google Calendar event and OAuth documentation. WorkSwarm CLI startup, Desktop PKCE and the pinned runtime requirements are reused from the team-owned Google Docs 1.0.1 connector at commit 293e6ef8cc34286af0937d0be14e61b8ddedc230. No Google client credentials, OAuth tokens, dependency binaries or Google brand artwork are distributed. The reused dependencies, applicable bundled license text and pinned distribution evidence are recorded in provenance.json and THIRD_PARTY_NOTICES.md.
