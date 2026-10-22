# Smart Download

Smart Download is a standalone WorkSwarm Plugin for reliable HTTP(S) file downloads. It exposes `smart_download` and `download_status`; no connector, Node.js service, `aria2` installation or API key is required.

The downloader probes server range support, uses one, four or eight Python download workers, writes through a `.part` file, resumes only when stored URL/validator metadata still matches, and atomically replaces the destination after optional SHA-256 verification.

## Boundaries

- HTTP and HTTPS only; no FTP, torrents or cloud-drive account management.
- Private and local addresses are blocked unless explicitly enabled for an approved intranet/test download.
- Acceleration depends on truthful server range support.
- Status records and partial-file metadata contain URLs and local paths. They are stored with owner-only permissions in the host temporary/output directories.
- Authentication headers are accepted but never returned by the tools.

See the included Skill for safe usage guidance.
