---
name: smart-download
description: Download explicit HTTP(S) files with range acceleration, conservative resume, progress status, and optional SHA-256 verification.
---

# Smart Download

Use `smart_download` only after the user supplies or approves the URL and destination. Prefer `output_path` when the destination filename matters; otherwise pass `output_dir` and let the server or URL supply a sanitized filename.

Pass a known lowercase or uppercase 64-character `sha256` whenever one is published. A mismatch fails the operation and leaves no final file. The tool may use 4 or 8 HTTP range connections for sufficiently large files; it falls back to one connection when range behavior is unavailable or inconsistent. A compatible `.part` file can resume conservatively.

Private, loopback, link-local and reserved network destinations are rejected by default. Set `allow_private_network=true` only for a user-approved intranet or local test server. Custom headers may be used for ordinary HTTP metadata, but do not expose secrets in conversation text or status output.

Use `download_status` with the returned `task_id`. Do not claim that a file is complete unless `state` is `completed` and, when requested, `verified` is true.
