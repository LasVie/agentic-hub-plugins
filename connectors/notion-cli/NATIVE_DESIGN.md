# Native design

The user selected the official Notion CLI and Skill for a package-only connection on macOS WorkSwarm 0.2.8. The launcher uses the official CLI's public interface. A local browser page displays the expected verification code, then links to Notion. The launcher polls the official CLI and activates a private session only after verifying the authenticated account endpoint.

The Skill supports bounded title search, Markdown read and appending one plain-text paragraph to a user-specified page. A write is followed by a separate read. The adapter owns its runtime and credentials and does not use an existing system CLI session.
