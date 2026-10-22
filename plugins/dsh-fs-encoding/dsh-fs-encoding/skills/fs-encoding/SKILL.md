---
name: fs-encoding
description: Safely read, create, edit, search, and undo legacy-encoded text files with explicit native tools.
---

# File Encoding Guardian

Use `encoding_read` before changing an existing file. For BOM-less non-UTF-8 files, pass an explicit encoding such as `gbk`, `big5`, `shift_jis`, `euc_kr`, or `windows-1252`. Use `encoding_write` for full replacement, `encoding_edit` for literal replacement, `encoding_grep` for search, and `encoding_undo` only for the most recent mutation. Undo records are stored with owner-only permissions in the host temporary directory so separately loaded tools can share them.

Never claim these tools replace WorkSwarm's built-ins. Writes preserve the detected encoding, BOM and dominant line ending. Unrepresentable characters are rejected before bytes change. Preview with `write=false`; mutate only when the user requests it.
