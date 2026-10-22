# Third-party notices

## Deckaura Tarot

- Source: https://github.com/gokimedia/claude-skill-tarot
- Fixed commit: `804c54558375416fd4fce605238927f39bbac1a2`; upstream version 1.0.0.
- Original notice: **Copyright (c) 2026 Deckaura**.
- License: MIT; full text including disclaimer is bundled at `licenses/deckaura-tarot/LICENSE`.
- Covered files: `skills/tarot-reading/SKILL.md`, `skills/tarot-reading/scripts/tarot.mjs`, `skills/tarot-reading/assets/deck.json`, and all five Markdown files under `skills/tarot-reading/references/`.
- Upstream `references/data-provenance.md` explicitly licenses the package and bundled structured dataset under MIT and asks to preserve source attribution/per-card guide URLs. These are retained. Suggested citation: Aura, S. (2026), *Tarot Card Meanings: A Complete 78-Card Semantic Dataset*, Deckaura, https://doi.org/10.5281/zenodo.19475329.
- Modifications: Skill instructions add native host-tool routing and describe its input/error contract; the original script, curated dataset and reference files are unchanged. The manifest, Python adapter and adaptation README are new repository work.
- No upstream NOTICE exists in the pinned recursive tree. No upstream icon/logo SVG, external fonts, card images, external model service or npm dependency is included.

This adaptation preserves upstream rights and attribution; it does not assert trademark permission or official endorsement and does not assign a unified license to repository-owned additions.
