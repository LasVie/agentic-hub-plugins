# Interactive Playground

Version: **1.0.0**. Candidate: `CAND-ANT-014`. Task: `AH-20261022-playground`.

Create a single HTML file containing controls, a live preview, and instructions you can copy back into your coding agent. The page runs locally in a modern browser. A model with file-reading and file-writing tools generates the page; the skill does not include a model or a hosting service.

## Install

### Agentic Hub / JiuwenSwarm

Unpack `playground-1.0.0.zip`. In a Skill upload or import flow, select the **inner** `playground/playground/` directory containing `SKILL.md` and `templates/`. Keep the templates and license files with it. The outer `plugin.yaml` is marketplace packaging, not the skill entry point. This is a Skill asset, rather than an `agent-plugin` manifest or a UI extension.

The package structure has been checked locally. Target-host installation and model-triggered generation require user testing; no successful Hub import or publication is claimed.

### Codex in VS Code or the CLI

Copy this entire inner directory to `<test-workspace>/.agents/skills/playground/`, then open that workspace in Codex. If the skill does not appear in `/skills`, start a new session. Use:

```text
$playground Build a product-card design playground with controls for color,
padding, font size, corner radius, and shadow. Include three presets, a live
preview, and a copyable prompt. Save it as product-card.html.
```

### Hermes CLI

Copy this entire inner directory to the active Hermes profile's `skills/playground/` directory. The default profile normally uses `~/.hermes/skills/playground/`; use the home/profile in which your Hermes installation actually runs. Start a new session, check `/skills list`, and invoke:

```text
/playground Build a product-card design playground with live controls,
three presets, and a copyable prompt. Save it as product-card.html.
```

These are local Skill installation instructions, not Claude marketplace commands. Preserve `SKILL.md`, all six templates, and `licenses/` together. No Claude Code installation or service key is needed by this skill; the coding agent still needs its normal model access.

## Try the workflows

| Template | Example request | Interaction to verify |
| --- | --- | --- |
| Design playground | Explore the appearance of a product card | Controls and presets update both preview and prompt |
| Data explorer | Build a SQL query against an example orders schema | Filters and limits update a readable query and contextual prompt |
| Concept map | Explore concepts from a supplied guide | Knowledge markers and selected relationships change the learning request |
| Document critique | Review a supplied README | Approved suggestions and user comments enter the prompt; rejected items are not applied |
| Diff review | Review a real supplied Git diff | Feedback retains the correct file and line number |
| Code map | Map an actual repository | Layer filters and component comments refer to files that were read |

For a first test, use the product-card prompt above. Open the output by double-clicking it, or use PowerShell `Start-Process -FilePath '.\product-card.html'`. In a remote or headless environment, download the file and open it locally.

## Manual acceptance checks

1. The output is one HTML file. Disconnect external networking and reload it: the controls, preview, and prompt should still work.
2. Change a control and apply each preset. The preview and prompt should update immediately, and controls should reflect the selected preset.
3. Copy the prompt and paste it into a plain text editor. Its content should match the displayed prompt. If clipboard permission is denied, the page should explain manual copying rather than report success.
4. Paste that prompt into your agent session. Confirm that it contains enough context to apply the selected changes. The browser page itself does not send messages or edit your project.
5. Try a narrow viewport and keyboard navigation. Controls and prompt should remain usable.
6. For review workflows, verify that rejected suggestions are not included as changes to apply and that file/line references are accurate. Imported HTML-looking text should display literally, not execute.

Record the installed skill version, generated filename, operations, results, and any failure. Provide a real screenshot of the version and key result when reporting user testing. Testing this file's generated examples does not by itself verify every model, host, template, or prompt.

## Dependencies and boundaries

- Generation: a coding agent with model access and local file tools; enough context to read the selected template.
- Output: a modern browser with JavaScript. Clipboard access is optional because a manual-copy fallback is required.
- No Node.js, Python, package installation, CDN, remote fonts, external image service, or local server is required for the generated page.
- This skill creates HTML tools. It does not modify the host's page/TUI, automatically feed browser events into an agent, deploy a site, or supply access to private repositories or external data.
- Source documents and project context must be supplied or readable. Browser verification is reported as pending when unavailable. User testing of the packaged skill in the intended host remains required.

## Source

Ported from Anthropic's official Playground skill at commit `d4226d062928f8d9505dbdeadd10217d23361052`. The six templates retain their upstream contents. `SKILL.md` contains a prominent notice describing this port's changes. See `THIRD_PARTY_NOTICES.md` and `licenses/claude-plugins-official/LICENSE`.
