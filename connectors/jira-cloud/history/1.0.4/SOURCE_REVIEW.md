# Source review

Jira Cloud → Jira Cloud 连接器 → `jira-cloud`. Song Haoran. AH-20261117-jira-cloud-connector.

Independent implementation based on [provider documentation](https://github.com/atlassian/homebrew-acli/blob/4e8f74c483ab002f2a6b0f17f9babbd62a9ffa95/Formula/acli.rb) (1.3.40-stable). The provider command is an external installation. No vendor binaries or provider code are distributed. Provider permissions, account terms, and implementation license coverage were considered separately. The pre-icon release bundled no upstream prompts, artwork, account material or logo.

The connector opens the official ACLI authorization URL in the same browser on macOS and Linux. Version 1.0.3 presents the CLI site selection in the local connector page after browser consent. The vendor CLI handles OAuth state, consent, the callback and credential storage. The consent page covers both Jira and Confluence scopes from the vendor OAuth client. The connector invokes Jira work item commands.

## 1.0.4 brand asset

- [Atlassian official material](https://atlassian.design/foundations/logos), retrieved 2026-11-17. [jira/PNG/Jira_icon.png](https://atlassian.design/assets/a92416454bd0/logos/jira_app.zip) is bundled unchanged as `icon.png` (SHA-256 `1db5048d57adcd0bfd50c6dd2a7f62e51e9689630c2dfb5f5af438c79c97df73`).
- [Terms](https://www.atlassian.com/legal/trademark). Atlassian publishes this product mark for identification and documents use outside its apps. The unmodified mark identifies the Jira service alongside the connector name and publisher.
- Attribution is included in `THIRD_PARTY_NOTICES.md`. The mark retains its owner and usage terms.
